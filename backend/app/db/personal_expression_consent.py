"""Consentimiento personal separado del permiso opcional ligado a asistencia."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.db.database import Base, SessionLocal
from app.db.models import Usuario

VERSION = 'emoscan-personal-2026-10-26-v1'
TEXT = (
    'Acepto voluntariamente analizar mi expresión facial en la sección personal de EmoScan. '
    'Cada análisis requiere que pulse Analizar expresión o Repetir análisis. '
    'La imagen y las puntuaciones se procesan temporalmente en memoria, no se guardan en '
    'archivos ni en la base de datos y solo yo puedo consultar el resultado durante 30 segundos. '
    'Las puntuaciones no representan emociones internas verificadas, atención ni rendimiento. '
    'Puedo retirar este consentimiento sin afectar mi acceso, notas o asistencia. '
    'Este permiso no activa el análisis opcional al registrar asistencia.'
)


class PersonalExpressionConsent(Base):
    __tablename__ = 'consentimientos_emoscan_personal'
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    aceptado = Column(Boolean, nullable=False, default=False)
    texto_version = Column(String(80), nullable=False)
    revision = Column(String(32), nullable=False)
    actualizado_en = Column(DateTime, nullable=False)


def read_revision(db, uid):
    user = db.get(Usuario, uid)
    row = db.get(PersonalExpressionConsent, uid)
    if (user is not None and user.estado == 'activo' and user.rol == 'estudiante'
            and row is not None and row.aceptado and row.texto_version == VERSION):
        return row.revision
    return None


def current_revision(uid):
    with SessionLocal() as db:
        return read_revision(db, uid)


def set_consent(db, uid, accepted):
    row = db.get(PersonalExpressionConsent, uid)
    if row is None:
        row = PersonalExpressionConsent(usuario_id=uid)
        db.add(row)
    row.aceptado = accepted
    row.texto_version = VERSION
    row.revision = uuid4().hex
    row.actualizado_en = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
