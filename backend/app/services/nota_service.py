from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Estudiante, Evaluacion, Matricula, Nota, Usuario
from app.services.auth_service import registrar_auditoria
from app.services.curso_service import exigir_gestion


def _f(valor):
    return None if valor is None else float(valor)


def evaluacion_dict(ev: Evaluacion) -> dict:
    return {"id": ev.id, "nombre": ev.nombre, "fecha_vencimiento": ev.fecha_vencimiento, "peso": float(ev.peso)}


def promedio_actual(items) -> float | None:
    """items: (peso, nota, estado). Promedio ponderado SOLO de lo ya calificado."""
    suma = 0.0
    pesos = 0.0
    for peso, nota, estado in items:
        if estado == "calificado" and nota is not None and peso is not None:
            suma += float(nota) * float(peso)
            pesos += float(peso)
    return round(suma / pesos, 2) if pesos > 0 else None


def _evaluaciones(db: Session, curso_id: int) -> list[Evaluacion]:
    return (db.query(Evaluacion)
              .filter(Evaluacion.curso_id == curso_id)
              .order_by(Evaluacion.fecha_vencimiento.is_(None), Evaluacion.fecha_vencimiento, Evaluacion.id)
              .all())


def _suma_pesos(db: Session, curso_id: int, excluir_id: int | None = None) -> float:
    q = db.query(func.coalesce(func.sum(Evaluacion.peso), 0)).filter(Evaluacion.curso_id == curso_id)
    if excluir_id is not None:
        q = q.filter(Evaluacion.id != excluir_id)
    return float(q.scalar() or 0)


def _estudiante_matriculado(db: Session, usuario_id: int, curso_id: int):
    est = db.query(Estudiante).filter(Estudiante.usuario_id == usuario_id).first()
    if est is None:
        return None
    ok = db.query(Matricula).filter(Matricula.curso_id == curso_id, Matricula.estudiante_id == est.id).first()
    return est if ok else None


# ---------- Estudiante ----------
def mis_notas(db: Session, user: Usuario, curso_id: int) -> dict:
    est = _estudiante_matriculado(db, user.id, curso_id)
    if est is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    evals = _evaluaciones(db, curso_id)
    notas = {}
    if evals:
        filas_nota = db.query(Nota).filter(
            Nota.estudiante_id == est.id, Nota.evaluacion_id.in_([e.id for e in evals])
        ).all()
        notas = {n.evaluacion_id: n for n in filas_nota}

    filas, items = [], []
    for e in evals:
        n = notas.get(e.id)
        estado = n.estado if n else "pendiente"
        valor = _f(n.nota) if n else None
        filas.append({
            "evaluacion_id": e.id, "nombre": e.nombre, "fecha_vencimiento": e.fecha_vencimiento,
            "peso": float(e.peso), "estado": estado, "nota": valor,
        })
        items.append((e.peso, valor, estado))
    return {"curso_id": curso_id, "promedio_actual": promedio_actual(items), "filas": filas}


# ---------- Profesor / admin ----------
def libro(db: Session, user: Usuario, curso_id: int) -> dict:
    exigir_gestion(db, user, curso_id)
    evals = _evaluaciones(db, curso_id)

    alumnos = (db.query(Usuario, Estudiante)
                 .join(Estudiante, Estudiante.usuario_id == Usuario.id)
                 .join(Matricula, Matricula.estudiante_id == Estudiante.id)
                 .filter(Matricula.curso_id == curso_id)
                 .order_by(Usuario.apellidos, Usuario.nombres).all())

    mapa = {}
    if evals and alumnos:
        for n in db.query(Nota).filter(
            Nota.evaluacion_id.in_([e.id for e in evals]),
            Nota.estudiante_id.in_([est.id for _, est in alumnos]),
        ).all():
            mapa[(n.estudiante_id, n.evaluacion_id)] = n

    filas = []
    for u, est in alumnos:
        celdas, items = [], []
        for e in evals:
            n = mapa.get((est.id, e.id))
            estado = n.estado if n else "pendiente"
            valor = _f(n.nota) if n else None
            celdas.append({"evaluacion_id": e.id, "nota": valor, "estado": estado})
            items.append((e.peso, valor, estado))
        filas.append({
            "usuario_id": u.id, "username": u.username, "nombres": u.nombres, "apellidos": u.apellidos,
            "codigo": est.codigo, "promedio_actual": promedio_actual(items), "notas": celdas,
        })
    return {"curso_id": curso_id, "evaluaciones": [evaluacion_dict(e) for e in evals], "alumnos": filas}


def crear_evaluacion(db: Session, user: Usuario, curso_id: int, datos, ip: str | None) -> Evaluacion:
    curso = exigir_gestion(db, user, curso_id)
    if _suma_pesos(db, curso_id) + datos.peso > 100.0001:
        raise HTTPException(status_code=400, detail="Los pesos del curso no pueden sumar más de 100")
    ev = Evaluacion(curso_id=curso_id, nombre=datos.nombre.strip(),
                    fecha_vencimiento=datos.fecha_vencimiento, peso=datos.peso, creado_por=user.id)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    registrar_auditoria(db, user.id, "evaluacion_creada", f"{curso.codigo}: {ev.nombre}", ip, True)
    return ev


def _evaluacion_gestionable(db: Session, user: Usuario, evaluacion_id: int):
    ev = db.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    curso = exigir_gestion(db, user, ev.curso_id)
    return ev, curso


def actualizar_evaluacion(db: Session, user: Usuario, evaluacion_id: int, datos, ip: str | None) -> Evaluacion:
    ev, curso = _evaluacion_gestionable(db, user, evaluacion_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "nombre" in cambios:
        if cambios["nombre"] is None:
            raise HTTPException(status_code=422, detail="El nombre no puede quedar vacío")
        ev.nombre = cambios["nombre"].strip()
    if "fecha_vencimiento" in cambios:
        ev.fecha_vencimiento = cambios["fecha_vencimiento"]
    if cambios.get("peso") is not None:
        if _suma_pesos(db, ev.curso_id, ev.id) + cambios["peso"] > 100.0001:
            raise HTTPException(status_code=400, detail="Los pesos del curso no pueden sumar más de 100")
        ev.peso = cambios["peso"]

    db.commit()
    db.refresh(ev)
    registrar_auditoria(db, user.id, "evaluacion_actualizada", f"{curso.codigo}: {ev.nombre}", ip, True)
    return ev


def eliminar_evaluacion(db: Session, user: Usuario, evaluacion_id: int, ip: str | None):
    ev, curso = _evaluacion_gestionable(db, user, evaluacion_id)
    nombre = ev.nombre
    db.delete(ev)  # las notas se borran en cascada (FK ON DELETE CASCADE)
    db.commit()
    registrar_auditoria(db, user.id, "evaluacion_eliminada", f"{curso.codigo}: {nombre}", ip, True)


def guardar_nota(db: Session, user: Usuario, evaluacion_id: int, usuario_id: int, datos, ip: str | None) -> dict:
    ev, curso = _evaluacion_gestionable(db, user, evaluacion_id)
    est = _estudiante_matriculado(db, usuario_id, curso.id)
    if est is None:
        raise HTTPException(status_code=404, detail="Ese estudiante no está matriculado en el curso")

    n = db.query(Nota).filter(Nota.evaluacion_id == ev.id, Nota.estudiante_id == est.id).first()
    if n is None:
        n = Nota(evaluacion_id=ev.id, estudiante_id=est.id)
        db.add(n)
    n.nota = datos.nota
    n.estado = datos.estado
    n.registrada_por = user.id
    db.commit()

    evals = _evaluaciones(db, curso.id)
    notas = {x.evaluacion_id: x for x in db.query(Nota).filter(
        Nota.estudiante_id == est.id, Nota.evaluacion_id.in_([e.id for e in evals])
    ).all()}
    items = [
        (e.peso, _f(notas[e.id].nota) if e.id in notas else None, notas[e.id].estado if e.id in notas else "pendiente")
        for e in evals
    ]
    registrar_auditoria(
        db, user.id, "nota_registrada",
        f"{curso.codigo} · {ev.nombre} · usuario {usuario_id}: {datos.estado}", ip, True,
    )
    return {"evaluacion_id": ev.id, "nota": datos.nota, "estado": datos.estado, "promedio_actual": promedio_actual(items)}