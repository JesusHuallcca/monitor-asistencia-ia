from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EvaluacionCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=150)
    fecha_vencimiento: date | None = None
    peso: float = Field(ge=0, le=100)


class EvaluacionActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    fecha_vencimiento: date | None = None
    peso: float | None = Field(default=None, ge=0, le=100)


class NotaGuardar(BaseModel):
    estado: Literal["pendiente", "entregado", "calificado"]
    nota: float | None = Field(default=None, ge=0, le=20)

    @model_validator(mode="after")
    def coherente(self):
        if self.estado == "calificado" and self.nota is None:
            raise ValueError("Una evaluación calificada necesita una nota")
        if self.estado != "calificado":
            self.nota = None
        return self


class EvaluacionOut(BaseModel):
    id: int
    nombre: str
    fecha_vencimiento: date | None
    peso: float


# ---- Vista del estudiante ----
class FilaNota(BaseModel):
    evaluacion_id: int
    nombre: str
    fecha_vencimiento: date | None
    peso: float
    estado: str
    nota: float | None


class MisNotas(BaseModel):
    curso_id: int
    promedio_actual: float | None
    filas: list[FilaNota]


# ---- Vista del profesor ----
class NotaCelda(BaseModel):
    evaluacion_id: int
    nota: float | None
    estado: str


class NotaGuardada(NotaCelda):
    promedio_actual: float | None


class FilaAlumno(BaseModel):
    usuario_id: int
    username: str
    nombres: str
    apellidos: str
    codigo: str | None
    promedio_actual: float | None
    notas: list[NotaCelda]


class Libro(BaseModel):
    curso_id: int
    evaluaciones: list[EvaluacionOut]
    alumnos: list[FilaAlumno]