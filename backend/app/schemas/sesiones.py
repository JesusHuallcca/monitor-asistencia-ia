from datetime import date, time

from pydantic import BaseModel, Field


class SesionCrear(BaseModel):
    curso_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    tolerancia_minutos: int = Field(default=10, ge=0, le=60)


class SesionOut(BaseModel):
    id: int
    curso_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    tolerancia_minutos: int
    estado: str


class SesionActualOut(BaseModel):
    activa: bool
    sesion: SesionOut | None = None