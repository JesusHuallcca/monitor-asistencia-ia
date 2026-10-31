"""
API Parte 4 – Regresión Logística (Clasificación binaria de asistencia).
Endpoints:
  GET  /api/logistica/metricas
  POST /api/logistica/predecir
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/api/logistica", tags=["Logística"])

# ── Rutas absolutas ──────────────────────────────────────────────────────────
_RAIZ = Path(__file__).resolve().parents[3]          # monitor-asistencia-ia/
_MODELS = _RAIZ / "models"
_METRICAS_PATH = _MODELS / "metricas_modelo.json"
_COEF_PATH     = _MODELS / "coeficientes.json"


# ── Carga de artefactos (una sola vez) ───────────────────────────────────────
@lru_cache(maxsize=1)
def _cargar_metricas() -> dict:
    if not _METRICAS_PATH.exists():
        raise HTTPException(503, f"Archivo no encontrado: {_METRICAS_PATH}")
    with open(_METRICAS_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _cargar_coeficientes() -> dict:
    if not _COEF_PATH.exists():
        raise HTTPException(503, f"Archivo no encontrado: {_COEF_PATH}")
    with open(_COEF_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Logística manual (sigmoide sobre coeficientes) ───────────────────────────
def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _predecir_logistica(features: dict[str, float], umbral: float = 0.5) -> dict[str, Any]:
    """
    Calcula probabilidad usando los coeficientes guardados en coeficientes.json.
    Aplica función sigmoide: P(y=1) = 1 / (1 + e^(-z))
    """
    coef_data = _cargar_coeficientes()
    intercept = coef_data.get("intercept", 0.0)
    coefs = coef_data.get("coefficients", {})

    logit = intercept
    for feature, coef in coefs.items():
        val = features.get(feature, 0.0)
        logit += coef * val

    proba = _sigmoid(logit)
    pred = 1 if proba >= umbral else 0
    return {
        "probabilidad": round(proba, 4),
        "prediccion": pred,
        "etiqueta": "Asistirá" if pred == 1 else "No asistirá",
        "logit": round(logit, 4),
    }


# ── Esquema de entrada ────────────────────────────────────────────────────────
class EntradaPrediccion(BaseModel):
    asistencia_ratio_30d: float = Field(
        ..., ge=0.0, le=1.0,
        description="Ratio de asistencia en los últimos 30 días (0-1)"
    )
    asistencias_consecutivas: int = Field(
        ..., ge=0, le=30,
        description="Número de asistencias consecutivas recientes"
    )
    ausencias_consecutivas: int = Field(
        ..., ge=0, le=30,
        description="Número de ausencias consecutivas recientes"
    )
    dia_semana: int = Field(
        ..., ge=0, le=6,
        description="Día de la semana (0=lunes, 6=domingo)"
    )
    hora_inicio_clase: int = Field(
        ..., ge=0, le=23,
        description="Hora de inicio de la clase (0-23)"
    )
    es_inicio_ciclo: int = Field(
        0, ge=0, le=1,
        description="1 si es la primera semana del ciclo académico"
    )
    promedio_notas: float = Field(
        ..., ge=0.0, le=20.0,
        description="Promedio de notas del estudiante (escala 0-20)"
    )
    tardanzas_ratio: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Ratio de tardanzas sobre total de asistencias (0-1)"
    )
    umbral: float = Field(
        0.5, ge=0.0, le=1.0,
        description="Umbral de decisión para clasificar como 'Asistirá' (default 0.5)"
    )

    @validator("tardanzas_ratio", always=True)
    def tardanzas_validas(cls, v, values):
        ratio = values.get("asistencia_ratio_30d", 1.0)
        if ratio > 0 and v > ratio:
            raise ValueError("tardanzas_ratio no puede ser mayor que asistencia_ratio_30d")
        return v


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/metricas")
def get_metricas():
    """Devuelve métricas del modelo y tabla de coeficientes."""
    metricas = _cargar_metricas()
    coef_data = _cargar_coeficientes()

    # Ordenar coeficientes por impacto absoluto descendente
    coefs_raw = coef_data.get("coefficients", {})
    tabla_coeficientes = sorted(
        [
            {
                "feature": k,
                "coeficiente": round(v, 4),
                "impacto": "positivo" if v > 0 else "negativo",
                "magnitud": round(abs(v), 4),
            }
            for k, v in coefs_raw.items()
        ],
        key=lambda x: x["magnitud"],
        reverse=True,
    )

    return {
        "modelo": "Regresión Logística (LogisticRegression)",
        "accuracy": metricas.get("accuracy"),
        "precision": metricas.get("precision"),
        "recall": metricas.get("recall"),
        "f1": metricas.get("f1"),
        "roc_auc": metricas.get("roc_auc"),
        "n_train": metricas.get("n_train"),
        "n_test": metricas.get("n_test"),
        "n_features": metricas.get("n_features"),
        "features": metricas.get("features", []),
        "trained_at": metricas.get("trained_at"),
        "intercept": round(coef_data.get("intercept", 0.0), 4),
        "tabla_coeficientes": tabla_coeficientes,
    }


@router.post("/predecir")
def post_predecir(entrada: EntradaPrediccion):
    """
    Simulador de clasificación logística interactiva.
    """
    features = {
        "asistencia_ratio_30d":   entrada.asistencia_ratio_30d,
        "asistencias_consecutivas": float(entrada.asistencias_consecutivas),
        "ausencias_consecutivas":  float(entrada.ausencias_consecutivas),
        "dia_semana":              float(entrada.dia_semana),
        "hora_inicio_clase":       float(entrada.hora_inicio_clase),
        "es_inicio_ciclo":         float(entrada.es_inicio_ciclo),
        "promedio_notas":          entrada.promedio_notas,
        "tardanzas_ratio":         entrada.tardanzas_ratio,
    }

    resultado = _predecir_logistica(features, umbral=entrada.umbral)

    # Nivel de confianza basado en la distancia al umbral
    delta = abs(resultado["probabilidad"] - entrada.umbral)
    if delta >= 0.25:
        confianza = "Alta"
    elif delta >= 0.10:
        confianza = "Media"
    else:
        confianza = "Baja"

    return {
        **resultado,
        "confianza": confianza,
        "features_usadas": features,
        "umbral": entrada.umbral,
    }
