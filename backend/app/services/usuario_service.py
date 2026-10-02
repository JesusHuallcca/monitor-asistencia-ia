from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Estudiante, Profesor, Usuario
from app.services.auth_service import registrar_auditoria


def crear_usuario(db: Session, datos, rol: str, estado: str,
                  creador_id: int | None = None, ip: str | None = None) -> Usuario:
    existe = db.query(Usuario).filter(
        or_(Usuario.username == datos.username, Usuario.email == datos.email)
    ).first()
    if existe:
        raise HTTPException(status_code=409, detail="El usuario o el correo ya existen")

    codigo = getattr(datos, "codigo", None)
    if codigo and db.query(Estudiante).filter(Estudiante.codigo == codigo).first():
        raise HTTPException(status_code=409, detail="El código de estudiante ya existe")

    user = Usuario(
        username=datos.username,
        email=datos.email,
        password_hash=hash_password(datos.password),
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        rol=rol,
        estado=estado,
        creado_por=creador_id,
    )
    try:
        db.add(user)
        db.flush()  # obtiene user.id sin cerrar la transacción

        if rol == "profesor":
            db.add(Profesor(usuario_id=user.id, especialidad=getattr(datos, "especialidad", None)))
        elif rol == "estudiante":
            db.add(Estudiante(
                usuario_id=user.id,
                codigo=codigo or f"E{datetime.now().year}-{user.id:04d}",
                carrera=getattr(datos, "carrera", None),
                ciclo=getattr(datos, "ciclo", None),
            ))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo crear: datos duplicados")

    db.refresh(user)
    registrar_auditoria(db, creador_id, "usuario_creado", f"{rol}: {user.username}", ip, True)
    return user


def cambiar_estado(db: Session, actor: Usuario, user_id: int, estado: str, ip: str | None = None) -> Usuario:
    objetivo = db.get(Usuario, user_id)
    if objetivo is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if objetivo.id == actor.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")
    if objetivo.rol == "superadmin":
        raise HTTPException(status_code=403, detail="No se puede modificar al superadmin")
    if objetivo.rol == "admin" and actor.rol != "superadmin":
        raise HTTPException(status_code=403, detail="Solo el superadmin puede modificar administradores")

    objetivo.estado = estado
    if estado == "activo":  # activar también desbloquea la cuenta
        objetivo.intentos_fallidos = 0
        objetivo.bloqueado_hasta = None
    db.commit()
    db.refresh(objetivo)
    registrar_auditoria(db, actor.id, "estado_cambiado", f"{objetivo.username} -> {estado}", ip, True)
    return objetivo