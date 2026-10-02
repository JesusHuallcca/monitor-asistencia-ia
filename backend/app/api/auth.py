from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.face_auth import FaceLogin
from app.services import face_auth_service


from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuarios import RegistroProfesor
from app.services import usuario_service
from app.services.auth_service import autenticar

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login de profesores y alumnos."""
    return autenticar(db, datos.identificador, datos.password, "general", datos.recordarme, _ip(request))


@router.post("/admin/login", response_model=TokenResponse)
def login_admin(datos: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login de administradores (sesión siempre corta, ignora 'recordarme')."""
    return autenticar(db, datos.identificador, datos.password, "admin", False, _ip(request))


@router.post("/register-profesor", status_code=201)
def registrar_profesor(datos: RegistroProfesor, request: Request, db: Session = Depends(get_db)):
    """Registro abierto solo para profesores. Queda 'pendiente' hasta que un admin lo active."""
    ip = _ip(request)

    # El rostro se valida primero: si falla, la cuenta no se crea
    cifrado = None
    if datos.imagenes:
        cifrado = face_auth_service.preparar_rostro_registro(db, datos.imagenes, datos.consentimiento)

    user = usuario_service.crear_usuario(db, datos, "profesor", "pendiente", None, ip)

    if cifrado is not None:
        face_auth_service.guardar_rostro(db, user.id, cifrado, ip)

    return {
        "mensaje": "Registro recibido. Un administrador debe aprobar tu cuenta.",
        "rostro_registrado": cifrado is not None,
    }

@router.post("/face-login", response_model=TokenResponse)
def login_facial(datos: FaceLogin, request: Request, db: Session = Depends(get_db)):
    """Login con rostro (1 a 1): usuario + captura de cámara."""
    return face_auth_service.login_facial(db, datos.identificador, datos.imagen, _ip(request))