"""Solo acciones cerradas y destinatario propio. Sin SQL, URL, canal o callable."""
from datetime import datetime
import re
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator

KINDS=Literal["next_class","evaluation","weekly_summary","absence_alert","tardy_alert","scheduled_report","tutoring","meeting","communication"]

class ActionSpec(BaseModel):
    model_config=ConfigDict(extra="forbid")
    kind:KINDS
    course_id:int|None=Field(default=None,gt=0)
    student_id:int|None=Field(default=None,gt=0)
    source_id:int|None=Field(default=None,gt=0)
    timezone:str=Field(default="America/Lima",max_length=64)
    frequency:Literal["once","daily","weekly"]="once"
    local_time:str="08:00"
    weekday:int=Field(default=0,ge=0,le=6)
    reminder_minutes:int=Field(default=30,ge=0,le=1440)
    threshold:int=Field(default=3,ge=1,le=100)
    window_days:int=Field(default=30,ge=1,le=90)
    event_at:datetime|None=None
    title:str=Field(default="",max_length=140)
    text:str=Field(default="",max_length=1500)

    @field_validator("timezone")
    @classmethod
    def zone(cls,value):
        try:ZoneInfo(value)
        except (ZoneInfoNotFoundError,ValueError):raise ValueError("Zona horaria IANA no válida.")
        return value

    @field_validator("local_time")
    @classmethod
    def wall(cls,value):
        if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]",value):raise ValueError("Usa HH:mm.")
        return value

    @field_validator("title","text")
    @classmethod
    def safe_text(cls,value):
        if any(ord(c)<32 and c not in "\n\t" for c in value):raise ValueError("Texto inválido.")
        return value.strip()

    @model_validator(mode="after")
    def shape(self):
        if self.kind in {"next_class","evaluation"} and (not self.course_id or not self.source_id or self.frequency!="once"):raise ValueError("Selecciona una fuente verificada y frecuencia única.")
        if self.kind in {"weekly_summary","absence_alert","tardy_alert","scheduled_report","communication"} and not self.course_id:raise ValueError("Selecciona un curso.")
        if self.kind=="weekly_summary" and self.frequency!="weekly":raise ValueError("El resumen es semanal.")
        if self.kind in {"absence_alert","tardy_alert","scheduled_report"} and self.frequency=="once":raise ValueError("Selecciona frecuencia diaria o semanal.")
        if self.kind in {"tutoring","meeting"}:
            if not self.event_at or self.event_at.utcoffset() is None or not self.title or self.frequency!="once":raise ValueError("Indica título, fecha con zona horaria y frecuencia única.")
        if self.kind=="communication" and self.frequency!="once":raise ValueError("La comunicación es solo un borrador revisable.")
        if self.event_at is not None and self.kind not in {"tutoring","meeting"}:raise ValueError("La fecha académica se obtiene del servidor.")
        if self.source_id is not None and self.kind not in {"next_class","evaluation"}:raise ValueError("Esta acción no acepta una fuente académica por ID.")
        return self

class Transition(BaseModel):
    model_config=ConfigDict(extra="forbid")
    version:int=Field(gt=0)
    operation:Literal["activate","pause","cancel","complete","review"]
    confirmed:bool=False

class Preferences(BaseModel):
    model_config=ConfigDict(extra="forbid")
    enabled:bool
    timezone:str=Field(default="America/Lima",max_length=64)
    _zone=field_validator("timezone")(classmethod(lambda cls,v:ActionSpec.zone(v)))

class NotificationState(BaseModel):
    model_config=ConfigDict(extra="forbid")
    state:Literal["read","completed","dismissed"]
