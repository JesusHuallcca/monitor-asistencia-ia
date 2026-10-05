from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def normalizar_estado(estado: str) -> str | None:
    estado = str(estado).strip().upper()

    if estado == "PRESENTE":
        return "PRESENTE"

    if estado in {"TARDANZA", "TARDE"}:
        return "TARDANZA"

    if estado == "AUSENTE":
        return "AUSENTE"

    return None


def compute_course_stats(asistencias: list[dict]) -> dict[str, Any]:
    if not asistencias:
        return {
            "n_registros": 0,
            "n_estudiantes": 0,
            "media_asistencia": 0.0,
            "mediana_asistencia": 0.0,
            "desviacion_estandar": 0.0,
            "tasa_presente": 0.0,
            "tasa_tardanza": 0.0,
            "tasa_ausente": 0.0,
            "por_estudiante": [],
        }

    registros = []

    for item in asistencias:
        estado = normalizar_estado(item["estado"])

        if estado is None:
            continue

        registros.append({
            "usuario_id": int(item["usuario_id"]),
            "estado": estado,
        })

    if not registros:
        return {
            "n_registros": 0,
            "n_estudiantes": 0,
            "media_asistencia": 0.0,
            "mediana_asistencia": 0.0,
            "desviacion_estandar": 0.0,
            "tasa_presente": 0.0,
            "tasa_tardanza": 0.0,
            "tasa_ausente": 0.0,
            "por_estudiante": [],
        }

    df = pd.DataFrame(registros)

    # Para la tasa de asistencia del sistema:
    # PRESENTE y TARDANZA cuentan como asistencia.
    df["score"] = df["estado"].apply(
        lambda estado: 1.0
        if estado in {"PRESENTE", "TARDANZA"}
        else 0.0
    )

    por_est = (
        df.groupby("usuario_id")["score"]
        .agg(media="mean", n="count")
        .reset_index()
    )

    medias = por_est["media"].values

    total = len(df)
    n_presente = int((df["estado"] == "PRESENTE").sum())
    n_tardanza = int((df["estado"] == "TARDANZA").sum())
    n_ausente = int((df["estado"] == "AUSENTE").sum())

    return {
        "n_registros": total,
        "n_estudiantes": int(por_est["usuario_id"].nunique()),
        "media_asistencia": round(float(np.mean(medias)), 4),
        "mediana_asistencia": round(float(np.median(medias)), 4),
        "desviacion_estandar": round(
            float(np.std(medias, ddof=1))
            if len(medias) > 1
            else 0.0,
            4,
        ),
        "tasa_presente": round(n_presente / total, 4),
        "tasa_tardanza": round(n_tardanza / total, 4),
        "tasa_ausente": round(n_ausente / total, 4),
        "por_estudiante": [
            {
                "usuario_id": int(row.usuario_id),
                "media_asistencia": round(float(row.media), 4),
                "n_registros": int(row.n),
            }
            for row in por_est.itertuples()
        ],
    }


class AnalyticsService:

    def stats_for_course(
        self,
        asistencias: list[dict],
    ) -> dict[str, Any]:
        return compute_course_stats(asistencias)


analytics_service = AnalyticsService()