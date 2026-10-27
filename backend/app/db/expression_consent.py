"""Only consent metadata is persistent. No images or expression results."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.db.database import Base, SessionLocal
from app.db.models import Usuario

CONSENT_VERSION = "emoscan-2026-10-25-v1"
CONSENT_TEXT = (
    "Acepto voluntariamente el análisis de mi expresión facial al registrar asistencia. "
    "Se usará el mismo fotograma, únicamente después de confirmar mi identidad y asistencia. "
    "La imagen y las puntuaciones se procesan temporalmente en memoria y no se guardan "
    "en archivos ni en la base de datos. Solo yo puedo consultar el resultado durante "
    "30 segundos. Es una estimación de expresión, no una prueba de emociones internas, "
    "atención o rendimiento. Puedo rechazar o revocar este permiso sin afectar mi asistencia."
)


class ExpressionConsent(Base):
    __tablename__ = "consentimientos_expresiones"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    aceptado = Column(Boolean, nullable=False, default=False)
    texto_version = Column(String(80), nullable=False)
    revision = Column(String(32), nullable=False)
    actualizado_en = Column(DateTime, nullable=False)


def read_revision(db, usuario_id):
    user = db.get(Usuario, usuario_id)
    row = db.get(ExpressionConsent, usuario_id)
    if (user is not None and user.estado == "activo" and user.rol == "estudiante"
            and row is not None and row.aceptado and row.texto_version == CONSENT_VERSION):
        return row.revision
    return None


def current_revision(usuario_id):
    # Never share request-scoped SQLAlchemy sessions with the worker thread.
    with SessionLocal() as db:
        return read_revision(db, usuario_id)


def set_consent(db, usuario_id, accepted):
    row = db.get(ExpressionConsent, usuario_id)
    if row is None:
        row = ExpressionConsent(usuario_id=usuario_id)
        db.add(row)
    row.aceptado = accepted
    row.texto_version = CONSENT_VERSION
    row.revision = uuid4().hex
    row.actualizado_en = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return row
