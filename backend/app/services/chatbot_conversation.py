"""Intenciones cerradas y memoria temporal firmada. Sin SQL ni decisión de permisos."""
import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import hmac
import re
import unicodedata
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from jose import JWTError, jwt
from app.core.config import settings, TIMEZONE
from app.schemas.chatbot import ChatMessage
from app.services.chatbot_security import deny

TTL_SECONDS = 1200
MONTHS = ("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre").split()


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def signing_key():
    return hmac.new(settings.JWT_SECRET_KEY.encode(), b"monitor-chatbot-context-v1", hashlib.sha256).hexdigest()


def load_memory(token, user, scope_key):
    if not token:
        return {}
    try:
        memory = jwt.decode(token, signing_key(), algorithms=["HS256"], audience="chatbot-context")
    except JWTError:
        raise HTTPException(409, "El contexto expiró o no es válido. Restablece el contexto y vuelve a consultar.")
    if memory.get("uid") != user.id:
        deny("conversation_owner")
    if memory.get("scope") != scope_key:
        raise HTTPException(409, "Tus permisos cambiaron. Restablece el contexto y selecciona de nuevo.")
    return memory


def parse_period(q, today):
    if re.search(r"sin (?:filtro de )?fecha|todo el historial|todos los periodos", q):
        return None, None, True
    if "esta semana" in q or "semana pasada" in q:
        start=today-timedelta(days=today.weekday())
        if "semana pasada" in q:start-=timedelta(days=7)
        return start,start+timedelta(days=6),True
    if "mes pasado" in q:
        end = today.replace(day=1)-timedelta(days=1)
        return end.replace(day=1), end, True
    if "este mes" in q:
        return today.replace(day=1), today.replace(day=calendar.monthrange(today.year,today.month)[1]), True
    for month, name in enumerate(MONTHS, 1):
        match = re.search(r"\b"+name+r"(?:\s+(?:de\s+)?(20\d{2}))?\b", q)
        if match:
            year = int(match.group(1)) if match.group(1) else today.year
            return date(year,month,1), date(year,month,calendar.monthrange(year,month)[1]), True
    if re.search(r"\bayer\b",q):
        day=today-timedelta(days=1)
        return day,day,True
    if re.search(r"\bhoy\b",q):
        return today,today,True
    return None,None,False


def classify(q, last_intent=None, has_period=False):
    clean=q.strip(" ¿?¡!.,;")
    if re.fullmatch(r"(?:hola|buenas|buenos dias|buenas tardes|buenas noches|que tal)(?:[ ,]+(?:monitor|asistente))?",clean): return "GREETING"
    if re.fullmatch(r"(?:muchas )?gracias(?: por (?:todo|tu ayuda|la ayuda))?|te agradezco",clean): return "THANKS"
    if re.fullmatch(r"adios|chau|chao|hasta (?:luego|pronto|manana)|nos vemos",clean): return "GOODBYE"
    if re.search(r"recorda|recuerda|reportes? programad|notific|tutoria|reunion|comunicaci|borrador|(?:programa|agenda).*(?:reporte|informe)|resumen.*semanal|alerta.*(?:ausencia|falta|tardanza)",q):return "PROACTIVE"
    from app.services.chatbot_ml import intent_for
    ml_intent=intent_for(q,last_intent)
    if ml_intent:return ml_intent
    if re.search(r"reporte|informe|descarg|vista previa|excel|xlsx|pdf|docx|\bword\b|imprim|compara|resumen mensual|resumen academico|(?:muestrame).*(?:tardanzas|ausencias|faltas)|tardanzas de esta semana",q):return "REPORT"
    if re.search(r"mas (?:tardanzas|retrasos)|mayor (?:cantidad|numero) de tardanzas",q): return "LATE_RANKING"
    if any(w in q for w in ("metrica","modelo","precision","recall")): return "MODEL_METRICS"
    if any(w in q for w in ("riesgo","predic","probabilidad")): return "PREDICTION"
    if any(w in q for w in ("proxima","siguiente clase","que clase","manana")): return "NEXT_CLASS"
    if any(w in q for w in ("tardanza","tarde","retraso")): return "LATE_STUDENTS"
    if any(w in q for w in ("historial","registros")): return "STUDENT_HISTORY"
    if any(w in q for w in ("estadistica","porcentaje","promedio","resumen")): return "COURSE_STATS"
    if any(w in q for w in ("curso","materia","asignatura")): return "COURSES"
    if any(w in q for w in ("asistencia de",)): return "STUDENT_HISTORY"
    if any(w in q for w in ("hoy","falt","ausen","asist")): return "STUDENT_HISTORY" if has_period else "ATTENDANCE_TODAY"
    if has_period:
        return last_intent if last_intent in {"STUDENT_HISTORY","LATE_STUDENTS","COURSE_STATS","LATE_RANKING","REPORT"} else "STUDENT_HISTORY"
    if re.search(r"^(?:y |ese|esa|el mismo|la misma|cual)",clean):
        return last_intent if last_intent in {"STUDENT_HISTORY","LATE_STUDENTS","COURSE_STATS"} and re.search(r"mismo|misma|tambien",q) else "CLARIFY"
    return "HELP"


@dataclass
class Turn:
    body: ChatMessage
    intent: str
    start: date | None
    end: date | None
    explicit_fields: frozenset
    previous_intent: str | None
    report_id: str | None = None
    ml_model: str | None = None


def prepare_turn(user, body, scope_key):
    memory = {} if body.reset_context else load_memory(body.context_token,user,scope_key)
    values = {key: memory.get(key) for key in ("course_id","student_id","period_start","period_end")}
    for field in values:
        if field in body.model_fields_set:
            values[field] = getattr(body,field)
    q=normalize(body.message)
    start,end,explicit=parse_period(q,datetime.now(ZoneInfo(TIMEZONE)).date())
    if explicit:
        values.update(period_start=start,period_end=end)
    effective=ChatMessage.model_validate(dict(body.model_dump(),**values))
    intent=classify(q,memory.get("last_intent"),effective.period_start is not None)
    ml_model=memory.get("ml_model")
    candidates=[name for pattern,name in [(r"k[ -]?means|segmentacion|cluster|centroide|como se agrupan|que (?:representa|significa).*grupo","kmeans"),(r"red(?:es)? neuronal|parte ?6","red_neuronal_parte6"),(r"regresion","regresion_logistica")] if re.search(pattern,q)]
    if len(candidates)==1:ml_model=candidates[0]
    if intent=="PREDICTION" and ml_model=="red_neuronal_parte6":intent="ML_NEURAL"
    return Turn(effective,intent,effective.period_start,effective.period_end,frozenset(body.model_fields_set),memory.get("last_intent"),memory.get("report_id"),ml_model)


def finish_turn(user, scope_key, turn, selection):
    state={"course_id":selection.get("course_id"), "student_id":selection.get("student_id"),
           "period_start":turn.start.isoformat() if turn.start else None,
           "period_end":turn.end.isoformat() if turn.end else None,"report_id":turn.report_id,"ml_model":turn.ml_model}
    last_intent=turn.previous_intent if turn.intent in {"GREETING","THANKS","GOODBYE","CLARIFY","HELP"} else turn.intent
    payload=dict(state,uid=user.id,scope=scope_key,last_intent=last_intent,
                 aud="chatbot-context",exp=datetime.now(timezone.utc)+timedelta(seconds=TTL_SECONDS))
    return dict(state,expires_in=TTL_SECONDS,token=jwt.encode(payload,signing_key(),algorithm="HS256"))
