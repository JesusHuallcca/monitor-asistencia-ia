from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.ml.predict import predict_attendance, load_model


class PredictionService:

    def __init__(
        self,
        model_path: str | Path | None = None,
    ):
        self.model_path = model_path
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            load_model(self.model_path)
            self._loaded = True

    def predict_for_student(
        self,
        historial: list[dict],
        dia_semana: int,
        hora_inicio: int,
        semana_ciclo: int = 5,
        promedio_notas: float = 14.0,
    ) -> dict[str, Any]:

        self._ensure_loaded()

        return predict_attendance(
            historial=historial,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            semana_ciclo=semana_ciclo,
            promedio_notas=promedio_notas,
            model_path=self.model_path,
        )


prediction_service = PredictionService()