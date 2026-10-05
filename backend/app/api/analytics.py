from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import (
    AsignacionProfesor,
    Asistencia,
    Curso,
    Profesor,
    SesionClase,
)
from app.schemas.analytics import CourseAnalyticsResponse
from app.services.analytics_service import analytics_service


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


def professor_can_access_course(
    db,
    user,
    curso_id: int,
) -> bool:
    profesor_id = db.scalar(
        select(Profesor.id).where(
            Profesor.usuario_id == user.id
        )
    )

    if profesor_id is None:
        return False

    return (
        db.scalar(
            select(AsignacionProfesor.curso_id).where(
                AsignacionProfesor.profesor_id == profesor_id,
                AsignacionProfesor.curso_id == curso_id,
            )
        )
        is not None
    )


@router.get(
    "/course/{curso_id}",
    response_model=CourseAnalyticsResponse,
)
def get_course_analytics(
    curso_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    role = str(user.rol).upper()

    curso = db.get(Curso, curso_id)

    if curso is None:
        raise HTTPException(
            status_code=404,
            detail="Curso no encontrado.",
        )

    if role == "ESTUDIANTE":
        raise HTTPException(
            status_code=403,
            detail="Los estudiantes no pueden consultar estadísticas globales del curso.",
        )

    if role == "PROFESOR":
        if not professor_can_access_course(
            db,
            user,
            curso_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para consultar este curso.",
            )

    if role not in {"ADMIN", "PROFESOR"}:
        raise HTTPException(
            status_code=403,
            detail="Rol no autorizado.",
        )

    rows = db.execute(
        select(
            Asistencia.usuario_id,
            Asistencia.estado,
        )
        .join(
            SesionClase,
            Asistencia.sesion_id == SesionClase.id,
        )
        .where(
            SesionClase.curso_id == curso_id
        )
        .order_by(
            Asistencia.fecha,
            Asistencia.hora,
        )
    ).all()

    asistencias = [
        {
            "usuario_id": usuario_id,
            "estado": estado,
        }
        for usuario_id, estado in rows
    ]

    stats = analytics_service.stats_for_course(
        asistencias
    )

    return CourseAnalyticsResponse(
        curso_id=curso_id,
        **stats,
    )