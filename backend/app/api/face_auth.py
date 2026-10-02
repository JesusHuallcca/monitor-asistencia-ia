from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.face_auth import EnrolarRostro, EstadoRostro
from app.services import face_auth_service

router = APIRouter(prefix="/api/face-auth", tags=["Login facial"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/status", response_model=EstadoRostro)
def estado(user: Usuario = Depends(get_current_user)):
    return face_auth_service.estado_rostro(user)


@router.post("/enroll", status_code=201)
def enrolar(datos: EnrolarRostro, request: Request, db: Session = Depends(get_db),
            user: Usuario = Depends(get_current_user)):
    face_auth_service.enrolar(db, user, datos.imagenes, datos.consentimiento, _ip(request))
    return {"mensaje": "Login facial activado"}


@router.delete("", status_code=204)
def desactivar(request: Request, db: Session = Depends(get_db),
               user: Usuario = Depends(get_current_user)):
    face_auth_service.desactivar(db, user, _ip(request))