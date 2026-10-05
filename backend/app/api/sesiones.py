from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.sesiones import SesionActualOut, SesionOut
from app.services.session_service import session_service


router = APIRouter(
    prefix="/api/sesiones",
    tags=["Sesiones"]
)


def convertir_sesion(sesion):
    return {
        "id": sesion.id,
        "curso_id": sesion.curso_id,
        "fecha": sesion.fecha,
        "hora_inicio": sesion.hora_inicio,
        "hora_fin": sesion.hora_fin,
        "tolerancia_minutos": sesion.tolerancia_minutos,
        "estado": sesion.estado,
    }


@router.get(
    "/actual",
    response_model=SesionActualOut
)
def obtener_sesion_actual(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    ahora = datetime.now()

    sesion = session_service.obtener_sesion_actual(
        db=db,
        current_date=ahora.date(),
        current_time=ahora.time()
    )

    if sesion is None:
        return {
            "activa": False,
            "sesion": None
        }

    return {
        "activa": True,
        "sesion": convertir_sesion(sesion)
    }


@router.get(
    "/fecha/{fecha}",
    response_model=list[SesionOut]
)
def obtener_sesiones_fecha(
    fecha: date,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    sesiones = session_service.obtener_sesiones_fecha(
        db=db,
        fecha=fecha
    )

    return [
        convertir_sesion(sesion)
        for sesion in sesiones
    ]


@router.get(
    "/{sesion_id}",
    response_model=SesionOut
)
def obtener_sesion(
    sesion_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    sesion = session_service.obtener_sesion(
        db=db,
        sesion_id=sesion_id
    )

    if sesion is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada"
        )

    return convertir_sesion(sesion)