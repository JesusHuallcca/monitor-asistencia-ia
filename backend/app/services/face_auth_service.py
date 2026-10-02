import base64
import binascii
from datetime import date, timedelta

import numpy as np
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.face_crypto import CryptoError, decrypt_embedding, encrypt_embedding
from app.core.security import create_access_token
from app.db.models import Rostro, Usuario
from app.services.auth_service import MAX_INTENTOS, MINUTOS_BLOQUEO, _ahora, registrar_auditoria
from app.services.face_engine import FaceError, FaceUnavailable, get_engine

ROLES_FACIAL = {"profesor", "estudiante"}
RETENCION_DIAS = 365


def _decodificar(imagen_b64: str) -> bytes:
    if imagen_b64.startswith("data:") and "," in imagen_b64[:100]:
        imagen_b64 = imagen_b64.split(",", 1)[1]
    try:
        return base64.b64decode(imagen_b64, validate=True)
    except (binascii.Error, ValueError):
        raise FaceError("Imagen inválida")


def _motor():
    try:
        return get_engine()
    except FaceUnavailable:
        raise HTTPException(status_code=503, detail="El reconocimiento facial no está disponible")


def _embedding(motor, imagen_b64: str) -> np.ndarray:
    try:
        return motor.embedding(_decodificar(imagen_b64))
    except FaceError as e:
        raise HTTPException(status_code=422, detail=str(e))


def verificar_vida(imagenes: list[str]) -> bool:
    # PENDIENTE (Persona 2): prueba de vida real (parpadeo, giro de cabeza o modelo anti-spoof).
    # Mientras no exista, el login facial es solo para demo: una foto podría engañarlo.
    return True


def estado_rostro(user: Usuario) -> dict:
    r = user.rostro
    activo = bool(r and r.consentimiento and r.login_facial_activo)
    return {"activo": activo, "retener_hasta": r.retener_hasta if activo else None}


def _rostro_duplicado(db: Session, motor, vector: np.ndarray, excluir_usuario_id: int) -> bool:
    """True si este rostro ya está registrado en OTRA cuenta."""
    otros = db.query(Rostro).filter(
        Rostro.usuario_id != excluir_usuario_id,
        Rostro.login_facial_activo == True,  # noqa: E712
    ).all()
    for r in otros:
        try:
            guardado = decrypt_embedding(r.embedding)
        except CryptoError:
            continue
        if motor.similarity(vector, guardado) >= settings.FACE_THRESHOLD:
            return True
    return False


def enrolar(db: Session, user: Usuario, imagenes: list[str], consentimiento: bool, ip: str | None):
    if user.rol not in ROLES_FACIAL:
        raise HTTPException(status_code=403, detail="El login facial no está disponible para tu rol")
    if not consentimiento:
        raise HTTPException(status_code=400, detail="Debes aceptar el uso de tu rostro para activarlo")
    if not verificar_vida(imagenes):
        raise HTTPException(status_code=422, detail="No se pudo comprobar que eres una persona real")

    motor = _motor()
    vectores = [_embedding(motor, img) for img in imagenes]

    # Las capturas deben ser de la misma persona
    for v in vectores[1:]:
        if motor.similarity(vectores[0], v) < settings.FACE_THRESHOLD:
            raise HTTPException(status_code=422, detail="Las capturas no parecen ser de la misma persona. Intenta de nuevo.")

    promedio = np.mean(vectores, axis=0)
    promedio = promedio / np.linalg.norm(promedio)

    # Un mismo rostro no puede estar en dos cuentas
    if _rostro_duplicado(db, motor, promedio, user.id):
        registrar_auditoria(db, user.id, "rostro_duplicado", "rostro ya asociado a otra cuenta", ip, False)
        raise HTTPException(status_code=409, detail="Este rostro ya está asociado a otra cuenta.")

    try:
        cifrado = encrypt_embedding(promedio)
    except CryptoError:
        raise HTTPException(status_code=503, detail="El reconocimiento facial no está configurado")

    ahora = _ahora()
    rostro = db.query(Rostro).filter(Rostro.usuario_id == user.id).first()
    if rostro is None:
        rostro = Rostro(usuario_id=user.id, embedding=cifrado)
        db.add(rostro)
    else:
        rostro.embedding = cifrado
    rostro.consentimiento = True
    rostro.fecha_consentimiento = ahora
    rostro.login_facial_activo = True
    rostro.retener_hasta = date.today() + timedelta(days=RETENCION_DIAS)
    db.commit()
    registrar_auditoria(db, user.id, "rostro_enrolado", "login facial activado", ip, True)


def desactivar(db: Session, user: Usuario, ip: str | None):
    rostro = db.query(Rostro).filter(Rostro.usuario_id == user.id).first()
    if rostro is not None:
        db.delete(rostro)  # se borra el embedding, no solo se desactiva
        db.commit()
    registrar_auditoria(db, user.id, "rostro_eliminado", "login facial desactivado", ip, True)


def login_facial(db: Session, identificador: str, imagen: str, ip: str | None) -> dict:
    ident = identificador.strip()
    user = db.query(Usuario).filter(
        or_(Usuario.username == ident, Usuario.email == ident)
    ).first()

    # Mismo mensaje para "no existe", "sin rostro" y "no coincide": no revela cuál fue
    rechazo = HTTPException(status_code=401, detail="No se pudo verificar tu identidad")

    if user is None:
        registrar_auditoria(db, None, "login_facial_fallido", f"usuario inexistente: {ident[:50]}", ip, False)
        raise rechazo

    ahora = _ahora()
    if user.bloqueado_hasta and user.bloqueado_hasta > ahora:
        registrar_auditoria(db, user.id, "login_bloqueado", "cuenta bloqueada (facial)", ip, False)
        raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente. Intenta más tarde.")

    rostro = user.rostro
    habilitado = (
        user.rol in ROLES_FACIAL
        and rostro is not None
        and rostro.consentimiento
        and rostro.login_facial_activo
        and not (rostro.retener_hasta and rostro.retener_hasta < date.today())
    )
    if not habilitado:
        registrar_auditoria(db, user.id, "login_facial_sin_rostro", "rostro no habilitado", ip, False)
        raise rechazo

    if not verificar_vida([imagen]):
        registrar_auditoria(db, user.id, "login_facial_vida", "prueba de vida fallida", ip, False)
        raise rechazo

    motor = _motor()
    # Si no se ve la cara, devuelve 422 y NO cuenta como intento fallido
    capturado = _embedding(motor, imagen)
    try:
        guardado = decrypt_embedding(rostro.embedding)
    except CryptoError:
        raise HTTPException(status_code=503, detail="El reconocimiento facial no está disponible")

    similitud = motor.similarity(capturado, guardado)

    if similitud < settings.FACE_THRESHOLD:
        user.intentos_fallidos += 1
        if user.intentos_fallidos >= MAX_INTENTOS:
            user.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            user.intentos_fallidos = 0
        db.commit()
        registrar_auditoria(db, user.id, "login_facial_fallido", f"similitud {similitud:.3f}", ip, False)
        raise rechazo

    if user.estado == "pendiente":
        raise HTTPException(status_code=403, detail="Tu cuenta está pendiente de aprobación por un administrador.")
    if user.estado != "activo":
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada.")

    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.ultimo_login = ahora
    db.commit()
    registrar_auditoria(db, user.id, "login_ok", f"portal facial (similitud {similitud:.3f})", ip, True)

    return {
        "access_token": create_access_token(user.id, user.rol),
        "token_type": "bearer",
        "rol": user.rol,
        "nombre": f"{user.nombres} {user.apellidos}",
    }