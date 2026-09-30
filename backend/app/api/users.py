from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import Usuario
from app.schemas.auth import UserOut

router = APIRouter(prefix="/api/users", tags=["Usuarios"])


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