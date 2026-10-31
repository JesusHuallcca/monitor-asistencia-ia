"""
Intent -> consulta parametrizada -> resultado.
Nunca se ejecuta SQL del usuario.
"""

import re
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select

from app.api.predictions import calcular_semana_ciclo
from app.core.config import TIMEZONE
from app.db.models import (
    Asistencia,
    Curso,
    Estudiante,
    Evaluacion,
    Metrica,
    Matricula,
    Nota,
    SesionClase,
    Usuario,
)
from app.services.prediction_service import prediction_service
from app.services.chatbot_security import academic_scope, deny


def normalize(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def full_name(nombres, apellidos):
    return f"{nombres} {apellidos}".strip()


def courses_for(db, user):
    """Compatibilidad para consumidores existentes; política común del chatbot."""
    return list(academic_scope(db, user).courses)


def get_next_session_for_student(db, estudiante_id, target_date=None, *, course_ids):
    local_date = datetime.now(
        ZoneInfo(TIMEZONE)
    ).date()

    query = (
        select(SesionClase, Curso)
        .join(
            Curso,
            SesionClase.curso_id == Curso.id,
        )
        .join(
            Matricula,
            Matricula.curso_id == Curso.id,
        )
        .where(
            Matricula.estudiante_id == estudiante_id,
            Curso.id.in_(course_ids),
            SesionClase.estado != "CANCELADA",
            SesionClase.fecha >= local_date,
        )
        .order_by(
            SesionClase.fecha.asc(),
            SesionClase.hora_inicio.asc(),
        )
    )

    if target_date is not None:
        query = query.where(
            SesionClase.fecha == target_date
        )

    return db.execute(query).first()


def build_prediction_for_student(db, estudiante_id, *, course_ids):
    next_session = get_next_session_for_student(
        db,
        estudiante_id,
        course_ids=course_ids,
    )

    if not next_session:
        return None

    sesion, curso = next_session

    local_date = datetime.now(
        ZoneInfo(TIMEZONE)
    ).date()

    cutoff_date = local_date - timedelta(days=30)

    history_rows = db.scalars(
        select(Asistencia.estado)
        .join(SesionClase, Asistencia.sesion_id == SesionClase.id)
        .join(
            Estudiante,
            Asistencia.usuario_id == Estudiante.usuario_id,
        )
        .where(
            Estudiante.id == estudiante_id,
            SesionClase.curso_id.in_(course_ids),
            Asistencia.fecha >= cutoff_date,
            Asistencia.fecha <= local_date,
        )
        .order_by(
            Asistencia.fecha.asc(),
            Asistencia.id.asc(),
        )
        .limit(30)
    ).all()

    historial = [
        {"estado": estado}
        for estado in history_rows
    ]

    promedio = db.scalar(
        select(func.avg(Nota.nota))
        .join(
            Evaluacion,
            Nota.evaluacion_id == Evaluacion.id,
        )
        .where(
            Nota.estudiante_id == estudiante_id,
            Evaluacion.curso_id.in_(course_ids),
            Nota.nota.is_not(None),
        )
    )

    promedio_notas = (
        float(promedio)
        if promedio is not None
        else 14.0
    )

    resultado = prediction_service.predict_for_student(
        historial=historial,
        dia_semana=sesion.fecha.weekday(),
        hora_inicio=sesion.hora_inicio.hour,
        semana_ciclo=calcular_semana_ciclo(db, curso.id, sesion.fecha),
        promedio_notas=promedio_notas,
    )

    return {
        "resultado": resultado,
        "sesion": sesion,
        "curso": curso,
    }


def answer(db, user, body, *, turn=None):
    role = str(user.rol).upper()

    q = normalize(body.message)

    scope = academic_scope(db, user)
    courses = scope.courses
    course_ids = list(scope.course_ids)
    own = scope.own_student_id

    if body.course_id is not None:
        if body.course_id not in course_ids:
            deny("course_filter")
        course_ids = [body.course_id]
    else:
        # Resolver curso antes del estudiante, sin ampliar el ámbito autorizado.
        matches = [course.id for course in courses
                   if normalize(course.nombre) in q or normalize(course.codigo) in q]
        if len(matches) == 1:
            course_ids = matches

    if turn and "course_id" not in turn.explicit_fields:
        matches = [c.id for c in courses if normalize(c.nombre) in q or normalize(c.codigo) in q]
        if re.search(r"(?:mis|todos mis) (?:cursos|materias|asignaturas)",q):
            course_ids=list(scope.course_ids)
        elif len(matches)==1:
            course_ids=matches

    if role == "ESTUDIANTE" and body.student_id is not None and body.student_id != own:
        deny("student_self_only")

    students = [(student, full_name(first, last))
                for student, first, last in db.execute(scope.students_query(course_ids)).unique()]
    student_ids = {student.id for student, _ in students}
    target = body.student_id
    if turn and "course_id" not in turn.explicit_fields and course_ids != ([body.course_id] if body.course_id else list(scope.course_ids)) and "student_id" not in turn.explicit_fields:
        target = own
    if target is not None and target not in student_ids:
        deny("student_filter")

    # Nunca buscar nombres en el directorio institucional para resolver una pregunta.
    named = []
    for student, name in students:
        normalized = normalize(name)
        first = normalized.split()[0] if normalized else ""
        if (normalized and normalized in q) or (first and re.search(r"\b" + re.escape(first) + r"\b", q)):
            named.append(student.id)
    if len(named) > 1:
        raise HTTPException(400, "Selecciona un estudiante del listado autorizado; el nombre es ambiguo.")
    if named:
        if target is not None and target != named[0] and (not turn or "student_id" in turn.explicit_fields):
            deny("conflicting_student_selector")
        target = named[0]
    elif re.search(r"\b(?:asistencia|historial|tardanzas|notas|faltas?|ausencias?)\s+de\s+(?!(?:hoy|ayer|asistencia|tardanzas|mis|mi|todos|los|la|las|esta|este|semana|mes|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b)[a-z]", q):
        # Mismo rechazo para nombres inexistentes y ajenos: no confirma identidades.
        deny("unresolved_student_reference")

    if target is None and own is not None:
        target = own
    # Una cuenta sin matrículas no habilita consultas implícitas a su historial global.
    if target is not None and target not in student_ids:
        deny("student_scope_empty")

    from app.services.chatbot_conversation import classify
    intent = turn.intent if turn else classify(q)

    data = []

    if intent in {"GREETING", "THANKS", "GOODBYE", "CLARIFY"}:
        reply = {
            "GREETING": "¡Hola! Soy tu asistente académico. Puedes preguntarme por tus cursos, asistencias o tardanzas.",
            "THANKS": "¡Con gusto! Si necesitas revisar otro curso o período, aquí estoy.",
            "GOODBYE": "¡Hasta pronto! Puedes volver cuando necesites consultar tus datos académicos.",
            "CLARIFY": "¿A qué curso o estudiante te refieres? Selecciónalo arriba o escribe su nombre autorizado.",
        }[intent]

    elif intent == "MODEL_METRICS":

        if role not in ("ADMIN", "SUPERADMIN"):
            deny("model_metrics_role")

        data = [
            {
                "modelo": m.modelo,
                "version": m.version,
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1": m.f1,
            }
            for m in db.scalars(
                select(Metrica)
                .order_by(
                    Metrica.id_metrica.desc()
                )
                .limit(20)
            )
        ]

        reply = (
            "Métricas registradas:\n"
            + "\n".join(str(r) for r in data)
            if data
            else (
                "Todavía no hay métricas reales "
                "de modelos registradas."
            )
        )

    elif intent == "PREDICTION":

        prediction_student_id = (
            target
            if target is not None
            else own
        )

        if prediction_student_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Indica qué estudiante deseas consultar."
                ),
            )

        prediction_data = build_prediction_for_student(
            db,
            prediction_student_id,
            course_ids=course_ids,
        )

        if not prediction_data:
            reply = (
                "No encontré una próxima clase programada "
                "para ese estudiante."
            )
            data = []

        else:
            resultado = prediction_data["resultado"]
            sesion = prediction_data["sesion"]
            curso = prediction_data["curso"]

            prob_asistencia = float(
                resultado["probabilidad"]
            )
            prob_falta = 1.0 - prob_asistencia

            data = {
                "estudiante_id": prediction_student_id,
                "curso": curso.nombre,
                "fecha_clase": str(sesion.fecha),
                "hora_inicio": str(sesion.hora_inicio),
                "probabilidad_asistir": round(
                    prob_asistencia,
                    4,
                ),
                "riesgo_faltar": round(
                    prob_falta,
                    4,
                ),
                "prediccion": resultado["prediccion"],
                "etiqueta": resultado["etiqueta"],
                "features_usadas": resultado.get(
                    "features_usadas",
                    {},
                ),
            }

            reply = (
                "Estimación para tu próxima clase "
                "(no es una certeza):\n"
                f"• Curso: {curso.nombre}\n"
                f"• Fecha: {sesion.fecha}\n"
                f"• Hora: {sesion.hora_inicio}\n"
                f"• Probabilidad estimada de asistir: "
                f"{prob_asistencia * 100:.1f}%\n"
                f"• Riesgo estimado de faltar: "
                f"{prob_falta * 100:.1f}%\n"
                f"• Predicción: {resultado['etiqueta']}."
            )

    elif intent == "NEXT_CLASS":

        next_student_id = (
            target
            if target is not None
            else own
        )

        if next_student_id is None:
            reply = (
                "Indica el estudiante para consultar "
                "su próxima clase."
            )
            data = []

        else:
            requested_date = None

            if "manana" in q:
                requested_date = (
                    datetime.now(
                        ZoneInfo(TIMEZONE)
                    ).date()
                    + timedelta(days=1)
                )

            result = get_next_session_for_student(
                db,
                next_student_id,
                requested_date,
                course_ids=course_ids,
            )

            if not result:
                if requested_date is not None:
                    reply = (
                        "No tienes una clase programada "
                        "para mañana."
                    )
                else:
                    reply = (
                        "No encontré próximas clases "
                        "programadas."
                    )

                data = []

            else:
                sesion, curso = result

                data = {
                    "curso_id": curso.id,
                    "curso": curso.nombre,
                    "codigo": curso.codigo,
                    "fecha": str(sesion.fecha),
                    "hora_inicio": str(sesion.hora_inicio),
                    "hora_fin": str(sesion.hora_fin),
                }

                reply = (
                    "Tu próxima clase es:\n"
                    f"• Curso: {curso.nombre}\n"
                    f"• Fecha: {sesion.fecha}\n"
                    f"• Horario: "
                    f"{sesion.hora_inicio} - "
                    f"{sesion.hora_fin}"
                )

    elif intent == "COURSES":

        data = [
            {
                "id": course.id,
                "nombre": course.nombre,
                "codigo": course.codigo,
            }
            for course in courses
            if course.id in course_ids
        ]

        reply = (
            "Tus cursos disponibles:\n"
            + "\n".join(
                f"• {r['nombre']} ({r['codigo']})"
                for r in data
            )
            if data
            else "No tienes cursos asignados."
        )

    elif intent == "HELP":

        reply = (
            "Puedo consultar tus cursos, asistencia de hoy, "
            "historial, tardanzas, estadísticas, próxima clase "
            "y predicciones del modelo. "
            "Prueba: «¿Cuál es mi próxima clase?» o "
            "«¿Cuál es mi riesgo de faltar?». "
            "Las respuestas respetan tu rol y los permisos."
        )

    else:

        query = (
            select(
                Asistencia,
                Usuario.nombres,
                Usuario.apellidos,
                Curso.nombre,
                SesionClase.fecha,
            )
            .join(
                SesionClase,
                Asistencia.sesion_id == SesionClase.id,
            )
            .join(
                Curso,
                SesionClase.curso_id == Curso.id,
            )
            .join(
                Estudiante,
                Asistencia.usuario_id
                == Estudiante.usuario_id,
            )
            .join(
                Usuario,
                Estudiante.usuario_id
                == Usuario.id,
            )
            .where(
                Curso.id.in_(course_ids),
                Estudiante.id.in_(student_ids),
            )
        )

        if target:
            query = query.where(
                Estudiante.id == target
            )

        if turn and turn.start:
            query = query.where(SesionClase.fecha >= turn.start, SesionClase.fecha <= turn.end)

        if intent == "ATTENDANCE_TODAY" and not (turn and turn.start):
            local_date = datetime.now(
                ZoneInfo(TIMEZONE)
            ).date()

            query = query.where(
                SesionClase.fecha == local_date
            )

        if intent == "LATE_STUDENTS":
            query = query.where(
                Asistencia.estado.in_(("TARDANZA", "TARDE"))
            )

        if intent == "ABSENT_STUDENTS":
            query = query.where(Asistencia.estado == "AUSENTE")

        if intent == "LATE_RANKING":
            rows = db.execute(query.where(Asistencia.estado.in_(("TARDANZA", "TARDE")))
                              .with_only_columns(Curso.id, Curso.nombre, func.count())
                              .order_by(None).group_by(Curso.id, Curso.nombre)).all()
            counts = {cid: count for cid, _, count in rows}
            data = sorted([{"curso_id":c.id,"curso":c.nombre,"tardanzas":counts.get(c.id,0)}
                           for c in courses if c.id in course_ids], key=lambda row:(-row["tardanzas"],row["curso_id"]))
            if not data or not data[0]["tardanzas"]:
                reply = "No hay tardanzas registradas en los cursos y el período consultados."
            else:
                maximum=data[0]["tardanzas"]
                winners=[row for row in data if row["tardanzas"]==maximum]
                reply = "Más tardanzas registradas: " + ", ".join(row["curso"] for row in winners) + f" ({maximum})."
                if len(winners)==1:
                    course_ids=[winners[0]["curso_id"]]
                    reply += " Usaré ese curso para el siguiente seguimiento; puedes cambiarlo en el filtro."
                else:
                    reply += " Hay un empate; selecciona un curso para continuar."

        elif intent == "COURSE_STATS":

            counts = dict(
                db.execute(
                    query.with_only_columns(
                        Asistencia.estado,
                        func.count(),
                    )
                    .order_by(None)
                    .group_by(Asistencia.estado)
                ).all()
            )

            total = sum(counts.values())
            present = counts.get("PRESENTE", 0)
            late = counts.get("TARDANZA", 0) + counts.get("TARDE", 0)
            absent = counts.get("AUSENTE", 0)

            percentage = (
                round(
                    (present + late)
                    / total
                    * 100,
                    2,
                )
                if total
                else None
            )

            data = {
                "registros": total,
                "presentes": present,
                "tardanzas": late,
                "ausentes": absent,
                "porcentaje_asistencia": percentage,
            }

            if total:
                reply = (
                    f"Resumen de {total} registros "
                    "de asistencia:\n"
                    f"• Presentes: {present}\n"
                    f"• Tardanzas: {late}\n"
                    f"• Ausentes: {absent}\n"
                    f"• Asistencia "
                    f"(presentes + tarde): "
                    f"{percentage}%.\n"
                    "El porcentaje usa los estados registrados; "
                    "no incluye sesiones sin asistencia cargada."
                )
            else:
                reply = (
                    "No hay registros de asistencia "
                    "en este ámbito."
                )

        else:

            rows = db.execute(
                query
                .order_by(
                    SesionClase.fecha.desc(),
                    Asistencia.id.desc(),
                )
                .limit(101)
            ).all()

            data = [
                {
                    "estudiante": full_name(
                        nombres,
                        apellidos,
                    ),
                    "curso": curso,
                    "fecha": str(fecha),
                    "estado": asistencia.estado,
                }
                for asistencia,
                nombres,
                apellidos,
                curso,
                fecha in rows[:100]
            ]

            if intent == "ATTENDANCE_TODAY":

                counts = dict(
                    db.execute(
                        query.with_only_columns(
                            Asistencia.estado,
                            func.count(),
                        )
                        .order_by(None)
                        .group_by(Asistencia.estado)
                    ).all()
                )

                reply = (
                    "Hoy, en tu ámbito: "
                    f"{counts.get('PRESENTE', 0)} presentes, "
                    f"{counts.get('TARDANZA', 0)} tardanzas y "
                    f"{counts.get('AUSENTE', 0)} ausencias.\n"
                )

            else:
                reply = (
                    "Historial de tardanzas:\n"
                    if intent == "LATE_STUDENTS"
                    else "Historial de inasistencias:\n" if intent == "ABSENT_STUDENTS" else "Historial de asistencia:\n"
                )

            reply += (
                "\n".join(
                    f"• {r['fecha']} · "
                    f"{r['estudiante']} · "
                    f"{r['curso']}: "
                    f"{r['estado']}"
                    for r in data
                )
                if data
                else "No hay registros para esta consulta."
            )

            if len(rows) > 100:
                reply += (
                    "\nSe muestran los 100 registros "
                    "más recientes."
                )

    if turn and turn.start and intent not in {"GREETING","THANKS","GOODBYE","CLARIFY","COURSES","HELP","NEXT_CLASS","PREDICTION","MODEL_METRICS"}:
        reply += f"\nPeríodo consultado: {turn.start.isoformat()} a {turn.end.isoformat()} (inclusive)."

    return {
        "_selection": {"course_id":course_ids[0] if len(course_ids)==1 else None,"student_id":target},
        "reply": reply,
        "intent": intent,
        "data": data,
        "provider": "local",
    }