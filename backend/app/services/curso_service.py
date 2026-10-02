from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import (
    AsignacionProfesor, Curso, Estudiante, Matricula, Profesor, Usuario,
)
from app.services.auth_service import registrar_auditoria

ADMIN_ROLES = ("admin", "superadmin")


def cursos_visibles(db: Session, user: Usuario):
    """Consulta de cursos que este usuario puede ver, según su rol."""
    q = db.query(Curso)
    if user.rol in ADMIN_ROLES:
        return q
    if user.rol == "profesor":
        return (q.join(AsignacionProfesor, AsignacionProfesor.curso_id == Curso.id)
                 .join(Profesor, Profesor.id == AsignacionProfesor.profesor_id)
                 .filter(Profesor.usuario_id == user.id))
    return (q.join(Matricula, Matricula.curso_id == Curso.id)
             .join(Estudiante, Estudiante.id == Matricula.estudiante_id)
             .filter(Estudiante.usuario_id == user.id))


def obtener_curso_visible(db: Session, user: Usuario, curso_id: int) -> Curso:
    curso = cursos_visibles(db, user).filter(Curso.id == curso_id).first()
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


def exigir_gestion(db: Session, user: Usuario, curso_id: int) -> Curso:
    """Admin, o profesor asignado a ese curso. Cualquier otro: 403."""
    curso = db.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    if user.rol in ADMIN_ROLES:
        return curso
    if user.rol == "profesor":
        asignado = (db.query(AsignacionProfesor)
                      .join(Profesor, Profesor.id == AsignacionProfesor.profesor_id)
                      .filter(AsignacionProfesor.curso_id == curso_id,
                              Profesor.usuario_id == user.id).first())
        if asignado:
            return curso
    raise HTTPException(status_code=403, detail="No tienes permiso sobre este curso")


def crear_curso(db: Session, datos, actor: Usuario, ip: str | None) -> Curso:
    if db.query(Curso).filter(Curso.codigo == datos.codigo).first():
        raise HTTPException(status_code=409, detail="Ya existe un curso con ese código")
    curso = Curso(codigo=datos.codigo, nombre=datos.nombre,
                  descripcion=datos.descripcion, periodo=datos.periodo)
    db.add(curso)
    db.commit()
    db.refresh(curso)
    registrar_auditoria(db, actor.id, "curso_creado", curso.codigo, ip, True)
    return curso


def actualizar_curso(db: Session, curso_id: int, datos, actor: Usuario, ip: str | None) -> Curso:
    curso = db.get(Curso, curso_id)
    if curso is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(curso, campo, valor)
    db.commit()
    db.refresh(curso)
    registrar_auditoria(db, actor.id, "curso_actualizado", curso.codigo, ip, True)
    return curso


def asignar_profesor(db: Session, curso: Curso, usuario_id: int, actor: Usuario, ip: str | None):
    prof = db.query(Profesor).filter(Profesor.usuario_id == usuario_id).first()
    if prof is None:
        raise HTTPException(status_code=404, detail="El usuario no es un profesor")
    if prof.usuario.estado != "activo":
        raise HTTPException(status_code=400, detail="El profesor no está activo")
    existe = db.query(AsignacionProfesor).filter(
        AsignacionProfesor.curso_id == curso.id, AsignacionProfesor.profesor_id == prof.id).first()
    if existe:
        raise HTTPException(status_code=409, detail="El profesor ya está asignado a este curso")
    db.add(AsignacionProfesor(curso_id=curso.id, profesor_id=prof.id, asignado_por=actor.id))
    db.commit()
    registrar_auditoria(db, actor.id, "profesor_asignado", f"{prof.usuario.username} -> {curso.codigo}", ip, True)


def quitar_profesor(db: Session, curso: Curso, usuario_id: int, actor: Usuario, ip: str | None):
    fila = (db.query(AsignacionProfesor)
              .join(Profesor, Profesor.id == AsignacionProfesor.profesor_id)
              .filter(AsignacionProfesor.curso_id == curso.id,
                      Profesor.usuario_id == usuario_id).first())
    if fila is None:
        raise HTTPException(status_code=404, detail="Ese profesor no está asignado al curso")
    db.delete(fila)
    db.commit()
    registrar_auditoria(db, actor.id, "profesor_quitado", f"usuario {usuario_id} <- {curso.codigo}", ip, True)


def matricular(db: Session, curso: Curso, usuario_id: int, actor: Usuario, ip: str | None):
    est = db.query(Estudiante).filter(Estudiante.usuario_id == usuario_id).first()
    if est is None:
        raise HTTPException(status_code=404, detail="El usuario no es un estudiante")
    if est.usuario.estado != "activo":
        raise HTTPException(status_code=400, detail="El estudiante no está activo")
    existe = db.query(Matricula).filter(
        Matricula.curso_id == curso.id, Matricula.estudiante_id == est.id).first()
    if existe:
        raise HTTPException(status_code=409, detail="El estudiante ya está matriculado")
    db.add(Matricula(curso_id=curso.id, estudiante_id=est.id, matriculado_por=actor.id))
    db.commit()
    registrar_auditoria(db, actor.id, "matricula_creada", f"{est.usuario.username} -> {curso.codigo}", ip, True)


def desmatricular(db: Session, curso: Curso, usuario_id: int, actor: Usuario, ip: str | None):
    fila = (db.query(Matricula)
              .join(Estudiante, Estudiante.id == Matricula.estudiante_id)
              .filter(Matricula.curso_id == curso.id,
                      Estudiante.usuario_id == usuario_id).first())
    if fila is None:
        raise HTTPException(status_code=404, detail="Ese estudiante no está matriculado")
    db.delete(fila)
    db.commit()
    registrar_auditoria(db, actor.id, "matricula_eliminada", f"usuario {usuario_id} <- {curso.codigo}", ip, True)


def listar_estudiantes(db: Session, curso_id: int) -> list[dict]:
    filas = (db.query(Usuario, Estudiante)
               .join(Estudiante, Estudiante.usuario_id == Usuario.id)
               .join(Matricula, Matricula.estudiante_id == Estudiante.id)
               .filter(Matricula.curso_id == curso_id)
               .order_by(Usuario.apellidos).all())
    return [{"usuario_id": u.id, "username": u.username, "nombres": u.nombres,
             "apellidos": u.apellidos, "detalle": e.codigo} for u, e in filas]


def listar_profesores(db: Session, curso_id: int) -> list[dict]:
    filas = (db.query(Usuario, Profesor)
               .join(Profesor, Profesor.usuario_id == Usuario.id)
               .join(AsignacionProfesor, AsignacionProfesor.profesor_id == Profesor.id)
               .filter(AsignacionProfesor.curso_id == curso_id)
               .order_by(Usuario.apellidos).all())
    return [{"usuario_id": u.id, "username": u.username, "nombres": u.nombres,
             "apellidos": u.apellidos, "detalle": p.especialidad} for u, p in filas]