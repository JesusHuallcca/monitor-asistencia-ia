"""
Feature engineering para predicción de asistencia.
Persona 3 — Machine Learning / Estadística / Predicciones
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Columnas de entrada que espera el modelo
FEATURE_COLUMNS = [
    "asistencia_ratio_30d",      # % de asistencia en los últimos 30 días
    "asistencias_consecutivas", # racha de asistencias seguidas
    "ausencias_consecutivas",   # racha de ausencias seguidas
    "dia_semana",               # 0=lunes … 6=domingo
    "hora_inicio_clase",        # hora de inicio de la sesión (0-23)
    "es_inicio_ciclo",          # 1 si está en las primeras 2 semanas
    "promedio_notas",           # promedio de notas del estudiante (0-20)
    "tardanzas_ratio",          # % de tardanzas sobre total de registros
]

TARGET_COLUMN = "asistira"  # 1 = se predice que asistirá, 0 = no


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el vector de features a partir de un DataFrame de asistencias históricas.
    Espera columnas: usuario_id, curso_id, fecha, estado, dia_semana,
                     hora_inicio, semana_ciclo, promedio_notas
    """
    out = df.copy()

    # Normalizaciones básicas
    out["asistencia_ratio_30d"] = out["asistencia_ratio_30d"].clip(0, 1)
    out["tardanzas_ratio"] = out["tardanzas_ratio"].clip(0, 1)
    out["promedio_notas"] = out["promedio_notas"].clip(0, 20) / 20.0  # escala 0-1
    out["hora_inicio_clase"] = out["hora_inicio_clase"] / 23.0        # escala 0-1
    out["dia_semana"] = out["dia_semana"] / 6.0                       # escala 0-1

    # Asegurar que las rachas sean no negativas
    out["asistencias_consecutivas"] = out["asistencias_consecutivas"].clip(0, 30)
    out["ausencias_consecutivas"] = out["ausencias_consecutivas"].clip(0, 30)

    return out[FEATURE_COLUMNS]


def features_from_student_history(
    historial: list[dict],
    dia_semana: int,
    hora_inicio: int,
    semana_ciclo: int,
    promedio_notas: float,
) -> np.ndarray:
    """
    Genera un vector de features listo para predicción a partir del historial
    de un estudiante (lista de dicts con 'estado' y 'fecha').
    """
    if not historial:
        ratio_30d = 0.5
        racha_asist = 0
        racha_aus = 0
        tardanzas_ratio = 0.0
    else:
        estados = [h["estado"] for h in historial]
        presentes = sum(1 for e in estados if e == "PRESENTE")
        tardanzas = sum(1 for e in estados if e == "TARDANZA")
        total = len(estados)
        ratio_30d = (presentes + tardanzas * 0.5) / total if total else 0.5
        tardanzas_ratio = tardanzas / total if total else 0.0

        # Rachas desde el final
        racha_asist = 0
        racha_aus = 0
        for e in reversed(estados):
            if e in ("PRESENTE", "TARDANZA"):
                if racha_aus == 0:
                    racha_asist += 1
                else:
                    break
            else:
                if racha_asist == 0:
                    racha_aus += 1
                else:
                    break

    es_inicio = 1 if semana_ciclo <= 2 else 0

    row = {
        "asistencia_ratio_30d": ratio_30d,
        "asistencias_consecutivas": racha_asist,
        "ausencias_consecutivas": racha_aus,
        "dia_semana": dia_semana,
        "hora_inicio_clase": hora_inicio,
        "es_inicio_ciclo": es_inicio,
        "promedio_notas": promedio_notas,
        "tardanzas_ratio": tardanzas_ratio,
    }
    df = pd.DataFrame([row])
    return build_features(df).values.astype(np.float32)
