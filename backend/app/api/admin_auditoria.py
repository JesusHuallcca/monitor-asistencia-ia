from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.models import Auditoria, Usuario

router = APIRouter(prefix="/api/admin/auditoria", tags=["Admin: auditoría"])

solo_admin = require_roles("admin", "superadmin")


class EventoOut(BaseModel):
    id: int
    fecha: datetime | None
    usuario_id: int | None
    username: str | None
    accion: str
    detalle: str | None
    ip: str | None
    exito: bool


@router.get("/resumen")
def resumen(db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    """Conteos del día de hoy."""
    hoy = db.query(Auditoria).filter(Auditoria.fecha >= func.curdate())
    return {
        "total": hoy.count(),
        "ingresos": hoy.filter(Auditoria.accion == "login_ok").count(),
        "fallidos": hoy.filter(Auditoria.exito == False).count(),  # noqa: E712
        "bloqueos": hoy.filter(Auditoria.accion == "login_bloqueado").count(),
    }


@router.get("/acciones", response_model=list[str])
def acciones(db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    filas = db.query(Auditoria.accion).distinct().order_by(Auditoria.accion).all()
    return [f[0] for f in filas]


@router.get("", response_model=list[EventoOut])
def listar(
    accion: str | None = Query(default=None, max_length=60),
    exito: bool | None = None,
    usuario_id: int | None = None,
    q: str | None = Query(default=None, max_length=50),
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(solo_admin),
):
    consulta = db.query(Auditoria, Usuario.username).outerjoin(Usuario, Usuario.id == Auditoria.usuario_id)

    if accion:
        consulta = consulta.filter(Auditoria.accion == accion)
    if exito is not None:
        consulta = consulta.filter(Auditoria.exito == exito)
    if usuario_id is not None:
        consulta = consulta.filter(Auditoria.usuario_id == usuario_id)
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(or_(
            Usuario.username.like(patron), Auditoria.detalle.like(patron), Auditoria.ip.like(patron),
        ))
    if desde:
        consulta = consulta.filter(Auditoria.fecha >= datetime.combine(desde, time.min))
    if hasta:
        consulta = consulta.filter(Auditoria.fecha < datetime.combine(hasta + timedelta(days=1), time.min))

    filas = consulta.order_by(Auditoria.id.desc()).offset(offset).limit(limit).all()
    return [
        EventoOut(
            id=a.id, fecha=a.fecha, usuario_id=a.usuario_id, username=nombre,
            accion=a.accion, detalle=a.detalle, ip=a.ip, exito=bool(a.exito),
        )
        for a, nombre in filas
    ]