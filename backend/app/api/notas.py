from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.models import Usuario
from app.schemas.notas import (
    EvaluacionActualizar, EvaluacionCrear, EvaluacionOut, Libro, MisNotas, NotaGuardada, NotaGuardar,
)
from app.services import nota_service

router = APIRouter(tags=["Notas"])

solo_estudiante = require_roles("estudiante")
docente = require_roles("profesor", "admin", "superadmin")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/api/cursos/{curso_id}/mis-notas", response_model=MisNotas)
def mis_notas(curso_id: int, db: Session = Depends(get_db), user: Usuario = Depends(solo_estudiante)):
    """El estudiante ve SOLO sus notas, y solo de cursos donde está matriculado."""
    return nota_service.mis_notas(db, user, curso_id)


@router.get("/api/cursos/{curso_id}/libro", response_model=Libro)
def libro(curso_id: int, db: Session = Depends(get_db), user: Usuario = Depends(docente)):
    """Libro de calificaciones completo: solo el profesor del curso o un admin."""
    return nota_service.libro(db, user, curso_id)


@router.post("/api/cursos/{curso_id}/evaluaciones", response_model=EvaluacionOut, status_code=201)
def crear_evaluacion(curso_id: int, datos: EvaluacionCrear, request: Request,
                     db: Session = Depends(get_db), user: Usuario = Depends(docente)):
    ev = nota_service.crear_evaluacion(db, user, curso_id, datos, _ip(request))
    return nota_service.evaluacion_dict(ev)


@router.patch("/api/evaluaciones/{evaluacion_id}", response_model=EvaluacionOut)
def actualizar_evaluacion(evaluacion_id: int, datos: EvaluacionActualizar, request: Request,
                          db: Session = Depends(get_db), user: Usuario = Depends(docente)):
    ev = nota_service.actualizar_evaluacion(db, user, evaluacion_id, datos, _ip(request))
    return nota_service.evaluacion_dict(ev)


@router.delete("/api/evaluaciones/{evaluacion_id}", status_code=204)
def eliminar_evaluacion(evaluacion_id: int, request: Request,
                        db: Session = Depends(get_db), user: Usuario = Depends(docente)):
    nota_service.eliminar_evaluacion(db, user, evaluacion_id, _ip(request))


@router.put("/api/evaluaciones/{evaluacion_id}/notas/{usuario_id}", response_model=NotaGuardada)
def guardar_nota(evaluacion_id: int, usuario_id: int, datos: NotaGuardar, request: Request,
                 db: Session = Depends(get_db), user: Usuario = Depends(docente)):
    return nota_service.guardar_nota(db, user, evaluacion_id, usuario_id, datos, _ip(request))