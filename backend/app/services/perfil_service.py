from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models import Usuario
from app.services.auth_service import MAX_INTENTOS, MINUTOS_BLOQUEO, _ahora, registrar_auditoria

# Qué campos puede editar cada rol en su propio perfil
PERMITIDOS = {
    "estudiante": {"email", "telefono"},
    "profesor": {"nombres", "apellidos", "email", "telefono", "especialidad"},
    "admin": {"nombres", "apellidos", "email"},
    "superadmin": {"nombres", "apellidos", "email"},
}


def armar_perfil(user: Usuario) -> dict:
    rostro = user.rostro
    d = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nombres": user.nombres,
        "apellidos": user.apellidos,
        "rol": user.rol,
        "estado": user.estado,
        "tiene_login_facial": bool(rostro and rostro.consentimiento and rostro.login_facial_activo),
        "ultimo_login": user.ultimo_login,
        "creado_en": user.creado_en,
        "telefono": None,
        "especialidad": None,
        "codigo": None,
        "carrera": None,
        "ciclo": None,
    }
    if user.profesor:
        d["telefono"] = user.profesor.telefono
        d["especialidad"] = user.profesor.especialidad
    if user.estudiante:
        d["telefono"] = user.estudiante.telefono
        d["codigo"] = user.estudiante.codigo
        d["carrera"] = user.estudiante.carrera
        d["ciclo"] = user.estudiante.ciclo
    return d


def _limpio(valor):
    valor = (valor or "").strip()
    return valor or None


def actualizar_perfil(db: Session, user: Usuario, datos, ip: str | None) -> dict:
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=400, detail="No hay cambios para guardar")

    prohibidos = set(cambios) - PERMITIDOS.get(user.rol, set())
    if prohibidos:
        raise HTTPException(status_code=403, detail="No puedes modificar: " + ", ".join(sorted(prohibidos)))

    for campo in ("nombres", "apellidos"):
        if campo in cambios:
            valor = (cambios[campo] or "").strip()
            if not valor:
                raise HTTPException(status_code=422, detail=f"El campo {campo} no puede quedar vacío")
            setattr(user, campo, valor)

    if cambios.get("email") is not None:
        email = str(cambios["email"]).strip()
        otro = db.query(Usuario).filter(Usuario.email == email, Usuario.id != user.id).first()
        if otro:
            raise HTTPException(status_code=409, detail="Ese correo ya está en uso")
        user.email = email

    if "telefono" in cambios:
        if user.profesor:
            user.profesor.telefono = _limpio(cambios["telefono"])
        elif user.estudiante:
            user.estudiante.telefono = _limpio(cambios["telefono"])

    if "especialidad" in cambios and user.profesor:
        user.profesor.especialidad = _limpio(cambios["especialidad"])

    db.commit()
    db.refresh(user)
    registrar_auditoria(db, user.id, "perfil_actualizado", "campos: " + ", ".join(sorted(cambios)), ip, True)
    return armar_perfil(user)


def cambiar_password(db: Session, user: Usuario, actual: str, nueva: str, ip: str | None):
    ahora = _ahora()
    if user.bloqueado_hasta and user.bloqueado_hasta > ahora:
        raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente. Intenta más tarde.")

    # Se responde 400 (no 401) para que el navegador no lo confunda con una sesión vencida
    if not verify_password(actual, user.password_hash):
        user.intentos_fallidos += 1
        if user.intentos_fallidos >= MAX_INTENTOS:
            user.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            user.intentos_fallidos = 0
        db.commit()
        registrar_auditoria(db, user.id, "password_cambio_fallido", "contraseña actual incorrecta", ip, False)
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")

    if verify_password(nueva, user.password_hash):
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser distinta de la actual")

    user.password_hash = hash_password(nueva)
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    db.commit()
    registrar_auditoria(db, user.id, "password_cambiada", "contraseña actualizada", ip, True)