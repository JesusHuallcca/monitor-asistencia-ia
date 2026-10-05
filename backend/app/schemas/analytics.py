from typing import Dict

from pydantic import BaseModel


class StudentStat(BaseModel):
    usuario_id: int
    media_asistencia: float
    n_registros: int


class CourseAnalyticsResponse(BaseModel):
    curso_id: int
    n_registros: int
    n_estudiantes: int
    media_asistencia: float
    mediana_asistencia: float
    desviacion_estandar: float
    tasa_presente: float
    tasa_tardanza: float
    tasa_ausente: float
    por_estudiante: list[StudentStat]


class PredictionResponse(BaseModel):
    estudiante_id: int
    probabilidad: float
    prediccion: int
    etiqueta: str
    features_usadas: Dict[str, float]