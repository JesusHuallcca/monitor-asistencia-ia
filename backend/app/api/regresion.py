from functools import lru_cache
import json
from pathlib import Path
from typing import Dict, Any, Union

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_roles
from app.db.models import Usuario

router = APIRouter(prefix="/api/regresion", tags=["Regresión Lineal (Parte 2)"])

# Rutas canónicas absolutas
BASE_DIR = Path(__file__).resolve().parents[3]
REGRESION_DIR = BASE_DIR / "regresion_lineal"
MODELO_PATH = REGRESION_DIR / "modelo_regresion.pkl"
SCALER_PATH = REGRESION_DIR / "scaler_regresion.pkl"
COEF_PATH = REGRESION_DIR / "coef.json"

GRAFICOS_PERMITIDOS = {
    "prediccion_vs_real.png",
    "regresion_simple.png",
    "graficos_exploracion.png"
}

profesor_o_admin = require_roles("profesor", "admin", "superadmin")


@lru_cache(maxsize=1)
def _cargar_modelo_y_scaler():
    """Carga el modelo y scaler una sola vez en memoria (Singleton/Cache)."""
    if not MODELO_PATH.exists() or not SCALER_PATH.exists():
        return None, None
    try:
        modelo = joblib.load(MODELO_PATH)
        scaler = joblib.load(SCALER_PATH)
        return modelo, scaler
    except Exception as e:
        print(f"Error al cargar modelo de regresión: {e}")
        return None, None


class PrediccionRequest(BaseModel):
    dia_semana: int = Field(default=1, ge=0, le=6, description="0=Lunes, 1=Martes, ..., 4=Viernes")
    hora_llegada: Union[int, float, str] = Field(default=485, description="Minutos desde 00:00 (485) o string '08:05'")
    confianza: float = Field(default=0.90, ge=0.0, description="Confianza facial 0.0 - 1.0 (o 0-100)")
    liveness_score: float = Field(default=0.88, ge=0.0, description="Liveness score 0.0 - 1.0 (o 0-100)")
    happy: float = Field(default=0.40, ge=0.0)
    neutral: float = Field(default=0.35, ge=0.0)
    sad: float = Field(default=0.15, ge=0.0)
    angry: float = Field(default=0.10, ge=0.0)


def _normalizar_hora(hora_raw: Union[int, float, str]) -> float:
    """Convierte un string '08:15' o número a minutos desde medianoche."""
    if isinstance(hora_raw, str):
        hora_str = hora_raw.strip()
        if ":" in hora_str:
            partes = hora_str.split(":")
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else 0
            return float(h * 60 + m)
        try:
            return float(hora_str)
        except ValueError:
            return 480.0  # Default 8:00 AM
    return float(hora_raw)


@router.get("/metricas")
def obtener_metricas(user: Usuario = Depends(get_current_user)):
    """Retorna las métricas, R2, MAE y coeficientes del modelo de regresión."""
    if not COEF_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el archivo coef.json de la regresión lineal."
        )

    try:
        with open(COEF_PATH, "r", encoding="utf-8") as f:
            datos_coef = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer coef.json: {str(e)}"
        )

    metricas = datos_coef.get("metricas", {})
    features_list = datos_coef.get("features", [])
    coefs_list = datos_coef.get("coeficientes", [])

    descripciones = {
        "hora_llegada": ("Alto (Negativo)", "Llegadas con tardanza penalizan severamente el puntaje"),
        "confianza": ("Positivo", "Mayor nitidez y precisión biométrica elevan el puntaje"),
        "liveness_score": ("Positivo", "Detección positiva anti-suplantación refuerza el registro"),
        "happy": ("Compensado", "Puntaje equilibrado dentro de las expresiones positivas"),
        "neutral": ("Compensado", "Comportamiento estándar de atención en clase"),
        "sad": ("Negativo", "Asociado a desatención o tardanza reiterada"),
        "angry": ("Negativo", "Asociado a conflicto o desmotivación"),
        "dia_semana": ("Bajo", "Impacto marginal según el día de la semana lectiva")
    }

    desglose_features = []
    for f_nom, c_val in zip(features_list, coefs_list):
        impacto, desc = descripciones.get(f_nom, ("Neutro", "Parámetro del modelo"))
        desglose_features.append({
            "feature": f_nom,
            "coeficiente": round(c_val, 4),
            "impacto": impacto,
            "descripcion": desc
        })

    # Ordenar por impacto absoluto
    desglose_features.sort(key=lambda x: abs(x["coeficiente"]), reverse=True)

    return {
        "modelo": datos_coef.get("modelo", "Regresión Lineal Múltiple"),
        "r2_multiple": metricas.get("r2_multiple", 0.779),
        "mae_multiple": metricas.get("mae_multiple", 6.184),
        "r2_simple": metricas.get("r2_simple", 0.1777),
        "mae_simple": metricas.get("mae_simple", 12.262),
        "intercepto": round(datos_coef.get("intercepto", 73.534), 3),
        "ecuacion_resumen": "Puntaje = 73.53 - 11.59 × Hora + 4.03 × Confianza + 2.16 × Liveness + Expresiones",
        "features": desglose_features,
        "graficos_disponibles": sorted(list(GRAFICOS_PERMITIDOS))
    }


@router.post("/predecir")
def predecir_asistencia(datos: PrediccionRequest, user: Usuario = Depends(profesor_o_admin)):
    """Simulador en vivo: calcula el puntaje (0-100) y estado inferido con Scikit-Learn."""
    modelo, scaler = _cargar_modelo_y_scaler()
    if modelo is None or scaler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo predictivo no está disponible. Verifique modelo_regresion.pkl y scaler_regresion.pkl."
        )

    # 1. Normalizar hora
    hora_minutos = _normalizar_hora(datos.hora_llegada)

    # 2. Escalar confianza y liveness a 0.0 - 1.0 si vinieron en porcentaje
    conf = datos.confianza / 100.0 if datos.confianza > 1.0 else datos.confianza
    conf = max(0.0, min(1.0, conf))

    live = datos.liveness_score / 100.0 if datos.liveness_score > 1.0 else datos.liveness_score
    live = max(0.0, min(1.0, live))

    # 3. Normalizar emociones para que sumen 1.0
    suma_emoc = datos.happy + datos.neutral + datos.sad + datos.angry
    if suma_emoc > 0:
        h = datos.happy / suma_emoc
        n = datos.neutral / suma_emoc
        s = datos.sad / suma_emoc
        a = datos.angry / suma_emoc
    else:
        h, n, s, a = 0.25, 0.25, 0.25, 0.25

    # 4. Construir DataFrame en el orden exacto esperado por el scaler
    fila_df = pd.DataFrame([{
        "dia_semana": int(datos.dia_semana),
        "hora_llegada": hora_minutos,
        "confianza": conf,
        "liveness_score": live,
        "happy": h,
        "neutral": n,
        "sad": s,
        "angry": a
    }])

    # 5. Transformar y predecir
    try:
        scaled_input = scaler.transform(fila_df)
        pred_raw = float(modelo.predict(scaled_input)[0])
        puntaje = round(float(np.clip(pred_raw, 0.0, 100.0)), 2)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en la inferencia del modelo: {str(e)}"
        )

    # 6. Clasificar según los umbrales definidos en Parte 2
    if puntaje >= 75.0:
        estado = "PRESENTE"
        color = "#16a34a"  # verde
        mensaje = "Excelente probabilidad de asistencia regular a tiempo."
    elif puntaje >= 45.0:
        estado = "TARDANZA"
        color = "#d97706"  # ambar
        mensaje = "Probabilidad de tardanza. Requiere seguimiento de horario de llegada."
    else:
        estado = "AUSENTE"
        color = "#dc2626"  # rojo
        mensaje = "Alto riesgo de inasistencia justificada o falta injustificada."

    # Convertir hora a formato HH:MM legible
    hh = int(hora_minutos // 60)
    mm = int(hora_minutos % 60)
    hora_legible = f"{hh:02d}:{mm:02d}"

    return {
        "puntaje": puntaje,
        "estado": estado,
        "color": color,
        "interpretacion": mensaje,
        "datos_normalizados": {
            "hora_llegada_minutos": hora_minutos,
            "hora_legible": hora_legible,
            "confianza_pct": round(conf * 100, 1),
            "liveness_pct": round(live * 100, 1),
            "emociones_normalizadas": {
                "happy": round(h, 3),
                "neutral": round(n, 3),
                "sad": round(s, 3),
                "angry": round(a, 3)
            }
        }
    }


@router.get("/grafico/{nombre}")
def obtener_grafico(nombre: str, user: Usuario = Depends(get_current_user)):
    """Sirve de forma segura los gráficos del modelo si están en la whitelist."""
    if nombre not in GRAFICOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gráfico '{nombre}' no está en la lista de imágenes permitidas."
        )

    img_path = REGRESION_DIR / nombre
    if not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El archivo gráfico '{nombre}' no existe en el directorio."
        )

    return FileResponse(img_path, media_type="image/png")
