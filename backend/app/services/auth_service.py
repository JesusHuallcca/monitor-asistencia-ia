from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.models import Auditoria, Usuario

MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15
MINUTOS_RECORDARME = 60 * 24 * 7  # 7 días

# Qué roles pueden entrar por cada pantalla de login
ROLES_PORTAL = {
    "general": {"profesor", "estudiante"},
    "admin": {"admin", "superadmin"},
}


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def registrar_auditoria(db: Session, usuario_id, accion: str, detalle=None, ip=None, exito=True):
    db.add(Auditoria(usuario_id=usuario_id, accion=accion, detalle=detalle, ip=ip, exito=exito))
    db.commit()


def _credenciales_invalidas() -> HTTPException:
    # Mensaje único: no revela si falló el usuario o la contraseña
    return HTTPException(status_code=401, detail="Credenciales inválidas")


def autenticar(db: Session, identificador: str, password: str, portal: str,
               recordarme: bool, ip: str | None) -> dict:
    ident = identificador.strip()
    user = db.query(Usuario).filter(
        or_(Usuario.username == ident, Usuario.email == ident)
    ).first()

    if user is None:
        registrar_auditoria(db, None, "login_fallido", f"usuario inexistente: {ident[:50]}", ip, False)
        raise _credenciales_invalidas()

    ahora = _ahora()

    if user.bloqueado_hasta and user.bloqueado_hasta > ahora:
        registrar_auditoria(db, user.id, "login_bloqueado", "cuenta bloqueada temporalmente", ip, False)
        raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente. Intenta más tarde.")

    if not verify_password(password, user.password_hash):
        user.intentos_fallidos += 1
        if user.intentos_fallidos >= MAX_INTENTOS:
            user.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            user.intentos_fallidos = 0
        db.commit()
        registrar_auditoria(db, user.id, "login_fallido", "contraseña incorrecta", ip, False)
        raise _credenciales_invalidas()

    # Contraseña correcta, pero ¿es la pantalla de login que le corresponde?
    if user.rol not in ROLES_PORTAL[portal]:
        registrar_auditoria(db, user.id, "login_portal_incorrecto", f"rol {user.rol} en portal {portal}", ip, False)
        raise _credenciales_invalidas()

    if user.estado == "pendiente":
        registrar_auditoria(db, user.id, "login_pendiente", "cuenta sin aprobar", ip, False)
        raise HTTPException(status_code=403, detail="Tu cuenta está pendiente de aprobación por un administrador.")
    if user.estado != "activo":
        registrar_auditoria(db, user.id, "login_inactivo", "cuenta desactivada", ip, False)
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada.")

    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.ultimo_login = ahora
    db.commit()
    registrar_auditoria(db, user.id, "login_ok", f"portal {portal}", ip, True)

    token = create_access_token(
        user.id, user.rol, expires_minutes=MINUTOS_RECORDARME if recordarme else None
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": user.rol,
        "nombre": f"{user.nombres} {user.apellidos}",
    }