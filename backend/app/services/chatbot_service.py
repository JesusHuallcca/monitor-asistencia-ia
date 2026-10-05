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
    AsignacionProfesor,
    Asistencia,
    Curso,
    Estudiante,
    Evaluacion,
    Matricula,
    Metrica,
    Nota,
    Profesor,
    Prediccion,
    SesionClase,
    Usuario,
)
from app.services.prediction_service import prediction_service


def normalize(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


def full_name(nombres, apellidos):
    return f"{nombres} {apellidos}".strip()


def courses_for(db, user):
    role = str(user.rol).upper()

    query = select(Curso)

    if role not in ("ADMIN", "SUPERADMIN"):
        query = query.where(Curso.activo.is_(True))

    if role == "PROFESOR":
        query = (
            query
            .join(
                AsignacionProfesor,
                Curso.id == AsignacionProfesor.curso_id,
            )
            .join(
                Profesor,
                Profesor.id == AsignacionProfesor.profesor_id,
            )
            .where(Profesor.usuario_id == user.id)
        )

    elif role == "ESTUDIANTE":
        query = (
            query
            .join(
                Matricula,
                Curso.id == Matricula.curso_id,
            )
            .join(
                Estudiante,
                Estudiante.id == Matricula.estudiante_id,
            )
            .where(Estudiante.usuario_id == user.id)
        )

    return list(db.scalars(query).unique())


def get_next_session_for_student(db, estudiante_id, target_date=None):
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


def build_prediction_for_student(db, estudiante_id):
    next_session = get_next_session_for_student(
        db,
        estudiante_id,
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
        .join(
            Estudiante,
            Asistencia.usuario_id == Estudiante.usuario_id,
        )
        .where(
            Estudiante.id == estudiante_id,
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
semana_ciclo=calcular_semana_ciclo(
    db,
    curso.id,
    sesion.fecha,
),        promedio_notas=promedio_notas,
    )

    return {
        "resultado": resultado,
        "sesion": sesion,
        "curso": curso,
    }


def answer(db, user, body):
    role = str(user.rol).upper()

    q = normalize(body.message)

    courses = courses_for(db, user)
    course_ids = [c.id for c in courses]

    if body.course_id is not None and body.course_id not in course_ids:
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a ese curso.",
        )

    if body.course_id:
        course_ids = [body.course_id]

    own = None

    if role == "ESTUDIANTE":
        own = db.scalar(
            select(Estudiante.id).where(
                Estudiante.usuario_id == user.id
            )
        )

        if body.student_id is not None and body.student_id != own:
            raise HTTPException(
                status_code=403,
                detail="Solo puedes consultar tus propios datos.",
            )

    # Estudiantes dentro del ámbito autorizado.
    students_query = (
        select(
            Estudiante,
            Usuario.nombres,
            Usuario.apellidos,
        )
        .join(
            Usuario,
            Estudiante.usuario_id == Usuario.id,
        )
        .join(
            Matricula,
            Matricula.estudiante_id == Estudiante.id,
        )
        .where(Matricula.curso_id.in_(course_ids))
    )

    students = [
        (
            estudiante,
            full_name(nombres, apellidos),
        )
        for estudiante, nombres, apellidos
        in db.execute(students_query).unique()
    ]

    if own is not None:
        students = [
            (estudiante, nombre)
            for estudiante, nombre in students
            if estudiante.id == own
        ]

    student_ids = {
        estudiante.id
        for estudiante, _ in students
    }

    target = body.student_id

    # Los nombres también se resuelven únicamente
    # dentro del ámbito autorizado.
    all_students_query = (
        select(
            Estudiante,
            Usuario.nombres,
            Usuario.apellidos,
        )
        .join(
            Usuario,
            Estudiante.usuario_id == Usuario.id,
        )
    )

    named = []

    for estudiante, nombres, apellidos in db.execute(
        all_students_query
    ):
        nombre = full_name(nombres, apellidos)
        normalized_name = normalize(nombre)

        first_name = (
            normalized_name.split()[0]
            if normalized_name
            else ""
        )

        if normalized_name in q or (
            first_name
            and re.search(
                r"\b" + re.escape(first_name) + r"\b",
                q,
            )
        ):
            named.append(estudiante.id)

    if any(sid not in student_ids for sid in named):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar ese estudiante.",
        )

    if target is None and len(named) == 1:
        target = named[0]

    if target is not None and target not in student_ids:
        raise HTTPException(
            status_code=403,
            detail="Ese estudiante no pertenece a tu ámbito autorizado.",
        )

    # Permite identificar cursos por nombre o código.
    for course in courses:
        if (
            normalize(course.nombre) in q
            or normalize(course.codigo) in q
        ):
            course_ids = [course.id]
            break

    intent = "HELP"

    if any(
        word in q
        for word in (
            "metrica",
            "modelo",
            "precision",
            "recall",
        )
    ):
        intent = "MODEL_METRICS"

    elif any(
        word in q
        for word in (
            "riesgo",
            "predic",
            "probabilidad",
        )
    ):
        intent = "PREDICTION"

    elif any(
        word in q
        for word in (
            "proxima clase",
            "proxima",
            "siguiente clase",
            "que clase",
            "clase manana",
            "manana",
        )
    ):
        intent = "NEXT_CLASS"

    elif any(
        word in q
        for word in (
            "tarde",
            "tardanza",
        )
    ):
        intent = "LATE_STUDENTS"

    elif (
        "historial" in q
        or "asistencia de" in q
    ):
        intent = "STUDENT_HISTORY"

    elif any(
        word in q
        for word in (
            "estadistica",
            "porcentaje",
            "promedio",
            "resumen",
        )
    ):
        intent = "COURSE_STATS"

    elif any(
        word in q
        for word in (
            "hoy",
            "falt",
            "ausen",
            "asist",
        )
    ):
        intent = "ATTENDANCE_TODAY"

    elif "curso" in q:
        intent = "COURSES"

    data = []

    if intent == "MODEL_METRICS":

        if role not in ("ADMIN", "SUPERADMIN"):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Las métricas de los modelos están "
                    "disponibles para el administrador."
                ),
            )

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

        if intent == "ATTENDANCE_TODAY":
            local_date = datetime.now(
                ZoneInfo(TIMEZONE)
            ).date()

            query = query.where(
                SesionClase.fecha == local_date
            )

        if intent == "LATE_STUDENTS":
            query = query.where(
                Asistencia.estado == "TARDANZA"
            )

        if intent == "COURSE_STATS":

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
            late = counts.get("TARDANZA", 0)
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
                    else "Historial de asistencia:\n"
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

    return {
        "reply": reply,
        "intent": intent,
        "data": data,
        "provider": "local",
    }