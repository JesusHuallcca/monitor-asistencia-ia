"""Ámbito del chatbot: denegación por defecto, sin SQL del usuario ni del LLM."""
from dataclasses import dataclass
import logging
import hashlib
import json
import os

from fastapi import HTTPException
from sqlalchemy import select
from app.db.models import AsignacionProfesor, Curso, Estudiante, Matricula, Profesor, Usuario

logger = logging.getLogger("monitor.chatbot.security")
ADMIN_GRANT_ENV = "CHATBOT_INSTITUTIONAL_READ_USER_IDS"


def deny(reason):
    # Solo códigos internos: sin nombres, preguntas, tokens ni IDs de estudiantes.
    logger.warning("chatbot_access_denied reason=%s", reason)
    raise HTTPException(403, "Consulta fuera del ámbito autorizado del asistente.")


def require_chatbot_role(user):
    role = str(user.rol).upper()
    if role not in {"ESTUDIANTE", "PROFESOR", "ADMIN", "SUPERADMIN"}:
        deny("unsupported_role")
    return role


def has_institutional_read(user):
    if str(user.rol).upper() not in {"ADMIN", "SUPERADMIN"}:
        return False
    # Concesión explícita del operador; nunca desde body, JWT ni Gemini.
    raw = os.environ.get(ADMIN_GRANT_ENV, "").strip()
    if not raw:
        return False
    entries = [value.strip() for value in raw.split(",")]
    if any(not value.isascii() or not value.isdecimal() or int(value) <= 0 for value in entries):
        return False  # Configuración malformada: no conceder permisos parciales.
    return user.id in {int(value) for value in entries}


@dataclass(frozen=True)
class AcademicScope:
    courses: tuple
    own_student_id: int | None

    @property
    def course_ids(self):
        return tuple(course.id for course in self.courses)

    def students_query(self, course_ids=None):
        ids = self.course_ids if course_ids is None else tuple(course_ids)
        if not set(ids).issubset(self.course_ids):
            deny("course_scope")
        query = (select(Estudiante, Usuario.nombres, Usuario.apellidos)
                 .join(Usuario, Estudiante.usuario_id == Usuario.id)
                 .join(Matricula, Matricula.estudiante_id == Estudiante.id)
                 .where(Matricula.curso_id.in_(ids)))
        # IN vacío se conserva: devuelve cero filas, nunca todos los estudiantes.
        if self.own_student_id is not None:
            query = query.where(Estudiante.id == self.own_student_id)
        return query.distinct()


def academic_scope(db, user):
    role = require_chatbot_role(user)
    query = select(Curso)
    own = None
    if role in {"ADMIN", "SUPERADMIN"}:
        if not has_institutional_read(user):
            deny("institutional_grant_required")
    else:
        query = query.where(Curso.activo.is_(True))
        if role == "PROFESOR":
            query = (query.join(AsignacionProfesor, Curso.id == AsignacionProfesor.curso_id)
                     .join(Profesor, Profesor.id == AsignacionProfesor.profesor_id)
                     .where(Profesor.usuario_id == user.id))
        else:
            own = db.scalar(select(Estudiante.id).where(Estudiante.usuario_id == user.id))
            if own is None:
                deny("student_profile_required")
            query = (query.join(Matricula, Matricula.curso_id == Curso.id)
                     .where(Matricula.estudiante_id == own))
    return AcademicScope(tuple(db.scalars(query).unique()), own)


def history_scope_key(db, user):
    """Huella del ámbito actual: invalida respuestas tras cambios de rol/matrículas."""
    scope = academic_scope(db, user)
    query = select(Matricula.curso_id, Matricula.estudiante_id).where(
        Matricula.curso_id.in_(scope.course_ids))
    if scope.own_student_id is not None:
        query = query.where(Matricula.estudiante_id == scope.own_student_id)
    enrollments = sorted(tuple(row) for row in db.execute(query.distinct()))
    payload = [user.id, str(user.rol).upper(), sorted(scope.course_ids), enrollments, scope.own_student_id]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def encode_history_reply(reply, scope_key):
    # El formato público sigue siendo texto; solo cambia el contenido de la columna TEXT.
    return json.dumps({"chatbot_scope_version": 1, "scope": scope_key, "reply": reply}, ensure_ascii=False)


def visible_history_reply(stored, scope_key):
    fallback = "Respuesta anterior no verificable con tus permisos actuales. Vuelve a consultar."
    try:
        data = json.loads(stored)
    except (ValueError, TypeError):
        return fallback
    if (not isinstance(data, dict) or data.get("chatbot_scope_version") != 1
            or data.get("scope") != scope_key or not isinstance(data.get("reply"), str)):
        return fallback
    return data["reply"]
