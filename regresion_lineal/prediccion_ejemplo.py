"""
prediccion_ejemplo.py
Carga el modelo entrenado y predice el puntaje de asistencia de un estudiante.
Uso: python prediccion_ejemplo.py
"""
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

# Cargar modelo y scaler
modelo = joblib.load(BASE_DIR / 'modelo_regresion.pkl')
scaler = joblib.load(BASE_DIR / 'scaler_regresion.pkl')


# --- Datos de entrada (modifica estos valores) ---
estudiante = {
    'dia_semana':    1,      # 0=lunes, 1=martes, ..., 4=viernes
    'hora_llegada':  487,    # minutos desde medianoche (480=8:00, 490=8:10)
    'confianza':     0.88,   # score reconocimiento facial (0.0 - 1.0)
    'liveness_score':0.91,   # score anti-spoofing       (0.0 - 1.0)
    'happy':         0.40,
    'neutral':       0.35,
    'sad':           0.15,
    'angry':         0.10
}

df_input = pd.DataFrame([estudiante])
df_scaled = scaler.transform(df_input)
puntaje   = float(np.clip(modelo.predict(df_scaled)[0], 0, 100))

if puntaje >= 75:
    estado = "PRESENTE"
elif puntaje >= 45:
    estado = "TARDANZA"
else:
    estado = "AUSENTE"

print(f"Puntaje predicho : {puntaje:.2f} / 100")
print(f"Estado inferido  : {estado}")
