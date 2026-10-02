from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import Curso, Usuario
from app.schemas.cursos import (
    AsignarUsuario, CursoActualizar, CursoCrear, CursoOut, PersonaCurso,
)
from app.services import curso_service

router = APIRouter(prefix="/api/cursos", tags=["Cursos"])

solo_admin = require_roles("admin", "superadmin")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[CursoOut])
def listar(q: str | None = Query(default=None, max_length=50),
           db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Cada rol ve solo los cursos que le corresponden."""
    consulta = curso_service.cursos_visibles(db, user)
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(or_(Curso.nombre.like(patron), Curso.codigo.like(patron)))
    return consulta.order_by(Curso.nombre).all()


@router.get("/{curso_id}", response_model=CursoOut)
def detalle(curso_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return curso_service.obtener_curso_visible(db, user, curso_id)


@router.post("", response_model=CursoOut, status_code=201)
def crear(datos: CursoCrear, request: Request, db: Session = Depends(get_db),
          actor: Usuario = Depends(solo_admin)):
    return curso_service.crear_curso(db, datos, actor, _ip(request))


@router.patch("/{curso_id}", response_model=CursoOut)
def actualizar(curso_id: int, datos: CursoActualizar, request: Request,
               db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    return curso_service.actualizar_curso(db, curso_id, datos, actor, _ip(request))


# ---------- Profesores del curso ----------
@router.get("/{curso_id}/profesores", response_model=list[PersonaCurso])
def ver_profesores(curso_id: int, db: Session = Depends(get_db),
                   user: Usuario = Depends(get_current_user)):
    curso_service.obtener_curso_visible(db, user, curso_id)
    return curso_service.listar_profesores(db, curso_id)


@router.post("/{curso_id}/profesores", status_code=201)
def asignar_profesor(curso_id: int, datos: AsignarUsuario, request: Request,
                     db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    curso = curso_service.exigir_gestion(db, actor, curso_id)
    curso_service.asignar_profesor(db, curso, datos.usuario_id, actor, _ip(request))
    return {"mensaje": "Profesor asignado"}


@router.delete("/{curso_id}/profesores/{usuario_id}", status_code=204)
def quitar_profesor(curso_id: int, usuario_id: int, request: Request,
                    db: Session = Depends(get_db), actor: Usuario = Depends(solo_admin)):
    curso = curso_service.exigir_gestion(db, actor, curso_id)
    curso_service.quitar_profesor(db, curso, usuario_id, actor, _ip(request))


# ---------- Estudiantes del curso (admin o profesor del curso) ----------
gestor = require_roles("admin", "superadmin", "profesor")


@router.get("/{curso_id}/estudiantes", response_model=list[PersonaCurso])
def ver_estudiantes(curso_id: int, db: Session = Depends(get_db), user: Usuario = Depends(gestor)):
    curso_service.exigir_gestion(db, user, curso_id)
    return curso_service.listar_estudiantes(db, curso_id)


@router.post("/{curso_id}/estudiantes", status_code=201)
def matricular(curso_id: int, datos: AsignarUsuario, request: Request,
               db: Session = Depends(get_db), user: Usuario = Depends(gestor)):
    curso = curso_service.exigir_gestion(db, user, curso_id)
    curso_service.matricular(db, curso, datos.usuario_id, user, _ip(request))
    return {"mensaje": "Estudiante matriculado"}


@router.delete("/{curso_id}/estudiantes/{usuario_id}", status_code=204)
def desmatricular(curso_id: int, usuario_id: int, request: Request,
                  db: Session = Depends(get_db), user: Usuario = Depends(gestor)):
    curso = curso_service.exigir_gestion(db, user, curso_id)
    curso_service.desmatricular(db, curso, usuario_id, user, _ip(request))