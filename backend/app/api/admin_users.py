from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.usuarios import CambiarEstado, UsuarioCrear, UsuarioListado
from app.services import usuario_service

router = APIRouter(prefix="/api/admin/usuarios", tags=["Admin: usuarios"])

solo_admin = require_roles("admin", "superadmin")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=UsuarioListado, status_code=201)
def crear(datos: UsuarioCrear, request: Request, db: Session = Depends(get_db),
          actor: Usuario = Depends(solo_admin)):
    if datos.rol == "admin" and actor.rol != "superadmin":
        raise HTTPException(status_code=403, detail="Solo el superadmin puede crear administradores")
    return usuario_service.crear_usuario(db, datos, datos.rol, "activo", actor.id, _ip(request))


@router.get("", response_model=list[UsuarioListado])
def listar(
    rol: str | None = None,
    estado: str | None = None,
    q: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    actor: Usuario = Depends(solo_admin),
):
    consulta = db.query(Usuario)
    if rol:
        consulta = consulta.filter(Usuario.rol == rol)
    if estado:
        consulta = consulta.filter(Usuario.estado == estado)
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(or_(
            Usuario.username.like(patron), Usuario.email.like(patron),
            Usuario.nombres.like(patron), Usuario.apellidos.like(patron),
        ))
    return consulta.order_by(Usuario.id).offset(offset).limit(limit).all()


@router.patch("/{user_id}/estado", response_model=UsuarioListado)
def cambiar_estado(user_id: int, datos: CambiarEstado, request: Request,
                   db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    return usuario_service.cambiar_estado(db, actor, user_id, datos.estado, _ip(request))