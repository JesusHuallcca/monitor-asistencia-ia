from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import (
    AsignacionProfesor,
    Asistencia,
    Estudiante,
    Evaluacion,
    Matricula,
    Nota,
    Profesor,
    SesionClase,
)
from app.schemas.analytics import PredictionResponse
from app.services.prediction_service import prediction_service


router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"],
)


def student_access_allowed(
    db,
    user,
    estudiante_id: int,
) -> bool:

    role = str(user.rol).upper()

    if role == "ADMIN":
        return True

    estudiante = db.get(
        Estudiante,
        estudiante_id,
    )

    if estudiante is None:
        return False

    if role == "ESTUDIANTE":
        return estudiante.usuario_id == user.id

    if role == "PROFESOR":

        profesor_id = db.scalar(
            select(Profesor.id).where(
                Profesor.usuario_id == user.id
            )
        )

        if profesor_id is None:
            return False

        return (
            db.scalar(
                select(AsignacionProfesor.curso_id)
                .join(
                    Matricula,
                    Matricula.curso_id
                    == AsignacionProfesor.curso_id,
                )
                .where(
                    AsignacionProfesor.profesor_id
                    == profesor_id,
                    Matricula.estudiante_id
                    == estudiante_id,
                )
                .limit(1)
            )
            is not None
        )

    return False


def get_next_session_for_student(
    db,
    estudiante_id: int,
):
    today = date.today()

    return db.execute(
        select(SesionClase)
        .join(
            Matricula,
            Matricula.curso_id
            == SesionClase.curso_id,
        )
        .where(
            Matricula.estudiante_id
            == estudiante_id,
            SesionClase.fecha >= today,
            SesionClase.estado != "CANCELADA",
        )
        .order_by(
            SesionClase.fecha.asc(),
            SesionClase.hora_inicio.asc(),
        )
    ).scalars().first()


def calcular_semana_ciclo(
    db,
    curso_id: int,
    fecha_sesion: date,
) -> int:

    primera_fecha = db.scalar(
        select(func.min(SesionClase.fecha)).where(
            SesionClase.curso_id == curso_id
        )
    )

    if primera_fecha is None:
        return 1

    semanas = (
        fecha_sesion - primera_fecha
    ).days // 7 + 1

    return max(
        1,
        min(20, semanas),
    )


def calcular_promedio_notas(
    db,
    estudiante_id: int,
) -> float:

    promedio_estudiante = db.scalar(
        select(func.avg(Nota.nota))
        .join(
            Evaluacion,
            Evaluacion.id == Nota.evaluacion_id,
        )
        .where(
            Nota.estudiante_id == estudiante_id,
            Nota.nota.is_not(None),
        )
    )

    if promedio_estudiante is not None:
        return float(promedio_estudiante)

    promedio_global = db.scalar(
        select(func.avg(Nota.nota)).where(
            Nota.nota.is_not(None)
        )
    )

    if promedio_global is not None:
        return float(promedio_global)

    return 0.0


@router.get(
    "/student/{estudiante_id}",
    response_model=PredictionResponse,
)
def predict_student_attendance(
    estudiante_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):

    estudiante = db.get(
        Estudiante,
        estudiante_id,
    )

    if estudiante is None:
        raise HTTPException(
            status_code=404,
            detail="Estudiante no encontrado.",
        )

    if not student_access_allowed(
        db,
        user,
        estudiante_id,
    ):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar esta predicción.",
        )

    next_session = get_next_session_for_student(
        db,
        estudiante_id,
    )

    if next_session is None:
        raise HTTPException(
            status_code=404,
            detail="No existe una próxima sesión programada para este estudiante.",
        )

    fecha_desde = date.today() - timedelta(
        days=30
    )

    historial_rows = db.execute(
        select(
            Asistencia.estado,
            Asistencia.fecha,
        )
        .where(
            Asistencia.usuario_id
            == estudiante.usuario_id,
            Asistencia.fecha >= fecha_desde,
        )
        .order_by(
            Asistencia.fecha.asc(),
            Asistencia.hora.asc(),
        )
    ).all()

    historial = []

    for estado, fecha in historial_rows:

        estado = str(estado).upper()

        if estado == "TARDE":
            estado = "TARDANZA"

        if estado not in {
            "PRESENTE",
            "TARDANZA",
            "AUSENTE",
        }:
            continue

        historial.append(
            {
                "estado": estado,
                "fecha": fecha,
            }
        )

    dia_semana = next_session.fecha.weekday()

    hora_inicio = next_session.hora_inicio.hour

    semana_ciclo = calcular_semana_ciclo(
        db,
        next_session.curso_id,
        next_session.fecha,
    )

    promedio_notas = calcular_promedio_notas(
        db,
        estudiante_id,
    )

    resultado = prediction_service.predict_for_student(
        historial=historial,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        semana_ciclo=semana_ciclo,
        promedio_notas=promedio_notas,
    )

    return PredictionResponse(
        estudiante_id=estudiante_id,
        **resultado,
    )