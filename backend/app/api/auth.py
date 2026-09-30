from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
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