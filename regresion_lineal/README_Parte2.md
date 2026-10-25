# README — Parte 2: Regresión Lineal Simple + Predicción

## Descripción
Modelo de regresión lineal que predice el **puntaje de asistencia** (0-100) de un estudiante a partir de:
- Datos del Monitor de Asistencia: hora de llegada, confianza facial, liveness score, día de semana
- Datos de EmoScan: distribución de emociones (happy, neutral, sad, angry)

## Archivos
| Archivo | Descripción |
|---|---|
| `regresion_lineal_colab.ipynb` | Notebook completo (abrir en Google Colab) |
| `dataset_asistencia.csv` | Dataset sintético de 200 registros |
| `modelo_regresion.pkl` | Modelo serializado con joblib |
| `scaler_regresion.pkl` | Scaler para normalizar las features |
| `coef.json` | Coeficientes y métricas en JSON |
| `prediccion_ejemplo.py` | Script mínimo de predicción |
| `metricas_modelo.md` | R², MAE, MSE e interpretación |

## Cómo ejecutar en Google Colab
1. Subir al Colab: `dataset_asistencia.csv` + `regresion_lineal_colab.ipynb`
2. Ejecutar todas las celdas (Runtime → Run all)
3. Los archivos `.pkl` y `.json` se generan automáticamente

## Cómo usar el modelo exportado
```python
import joblib, numpy as np, pandas as pd

modelo = joblib.load('modelo_regresion.pkl')
scaler = joblib.load('scaler_regresion.pkl')

entrada = pd.DataFrame([{
    'dia_semana': 0, 'hora_llegada': 485,
    'confianza': 0.90, 'liveness_score': 0.88,
    'happy': 0.45, 'neutral': 0.35, 'sad': 0.15, 'angry': 0.05
}])

puntaje = float(np.clip(modelo.predict(scaler.transform(entrada))[0], 0, 100))
print(f"Puntaje: {puntaje:.2f}")
```

## Conectar con el frontend (Parte 5)
El endpoint que consume esta predicción devuelve:
```json
{ "puntaje": 86.13, "estado": "PRESENTE" }
```
Cambiar la URL del fetch en `indicadores_ml.html` cuando el backend esté activo.
