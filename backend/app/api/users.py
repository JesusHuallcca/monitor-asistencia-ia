from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.auth import UserOut
from app.schemas.perfil import CambiarPassword, PerfilActualizar, PerfilOut
from app.services import perfil_service

router = APIRouter(prefix="/api/users", tags=["Usuarios"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/me", response_model=UserOut)
def me(user: Usuario = Depends(get_current_user)):
    rostro = user.rostro
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        nombres=user.nombres,
        apellidos=user.apellidos,
        rol=user.rol,
        estado=user.estado,
        tiene_login_facial=bool(rostro and rostro.consentimiento and rostro.login_facial_activo),
    )


@router.get("/me/perfil", response_model=PerfilOut)
def mi_perfil(user: Usuario = Depends(get_current_user)):
    return perfil_service.armar_perfil(user)


@router.patch("/me/perfil", response_model=PerfilOut)
def actualizar_mi_perfil(datos: PerfilActualizar, request: Request, db: Session = Depends(get_db),
                         user: Usuario = Depends(get_current_user)):
    return perfil_service.actualizar_perfil(db, user, datos, _ip(request))


@router.post("/me/password", status_code=204)
def cambiar_mi_password(datos: CambiarPassword, request: Request, db: Session = Depends(get_db),
                        user: Usuario = Depends(get_current_user)):
    perfil_service.cambiar_password(db, user, datos.actual, datos.nueva, _ip(request))