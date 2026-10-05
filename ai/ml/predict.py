"""
Inferencia: predicción de asistencia para un estudiante.
Persona 3 — Machine Learning
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from ai.ml.features import FEATURE_COLUMNS, features_from_student_history


_model = None
_model_path = None


def load_model(model_path: str | Path | None = None):
    global _model, _model_path

    if model_path is None:
        # Ruta relativa al repo
        model_path = (
            Path(__file__).resolve().parents[2]
            / "models"
            / "asistencia_logreg.joblib"
        )

    model_path = Path(model_path)

    if _model is None or _model_path != model_path:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en {model_path}. "
                "Ejecuta primero: python -m ai.ml.train"
            )

        _model = joblib.load(model_path)
        _model_path = model_path

    return _model


def predict_attendance(
    historial: list[dict],
    dia_semana: int,
    hora_inicio: int,
    semana_ciclo: int = 5,
    promedio_notas: float = 14.0,
    model_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Predice si un estudiante asistirá a una sesión.

    Parameters
    ----------
    historial : list[dict]
        Lista de registros previos, cada uno con al menos 'estado'
        (PRESENTE | TARDANZA | AUSENTE).
    dia_semana : int
        0=lunes … 6=domingo
    hora_inicio : int
        Hora de inicio de la clase (0-23)
    semana_ciclo : int
        Número de semana del ciclo académico
    promedio_notas : float
        Promedio de notas del estudiante (escala 0-20)

    Returns
    -------
    dict con:
        - probabilidad: float 0-1
        - prediccion: int 0|1
        - etiqueta: str
        - features_usadas: dict
    """

    model = load_model(model_path)

    X = features_from_student_history(
        historial,
        dia_semana,
        hora_inicio,
        semana_ciclo,
        promedio_notas,
    )

    # Compatibilidad con modelos LogisticRegression
    # cargados con versiones anteriores de scikit-learn.
    if not hasattr(model.steps[-1][1], "multi_class"):
        model.steps[-1][1].multi_class = "auto"

    proba = float(model.predict_proba(X)[0, 1])
    pred = int(model.predict(X)[0])

    features_dict = dict(zip(FEATURE_COLUMNS, X[0].tolist()))

    return {
        "probabilidad": round(proba, 4),
        "prediccion": pred,
        "etiqueta": "Asistirá" if pred == 1 else "No asistirá",
        "features_usadas": {
            k: round(float(v), 4)
            for k, v in features_dict.items()
        },
    }


if __name__ == "__main__":
    # Ejemplo rápido de uso
    ejemplo_historial = [
        {"estado": "PRESENTE"},
        {"estado": "PRESENTE"},
        {"estado": "TARDANZA"},
        {"estado": "AUSENTE"},
        {"estado": "PRESENTE"},
    ]

    resultado = predict_attendance(
        historial=ejemplo_historial,
        dia_semana=1,      # martes
        hora_inicio=10,
        semana_ciclo=6,
        promedio_notas=15.5,
    )

    print(resultado)