import pandas as pd
import numpy as np

np.random.seed(42)
N = 200

dias_semana = np.random.randint(0, 5, N)

hora_llegada = np.random.normal(490, 15, N).clip(460, 540).astype(int)

confianza = np.random.beta(8, 2, N).round(6)

liveness_score = np.random.beta(7, 2, N).round(6)

happy   = np.random.beta(3, 5, N).round(4)
neutral = np.random.beta(5, 3, N).round(4)
sad     = np.random.beta(2, 8, N).round(4)
angry   = np.random.beta(1, 10, N).round(4)

total = happy + neutral + sad + angry + 0.01
happy   = (happy   / total).round(4)
neutral = (neutral / total).round(4)
sad     = (sad     / total).round(4)
angry   = (angry   / total).round(4)

puntaje = np.zeros(N)

for i in range(N):
    base = 0.0
    if hora_llegada[i] <= 485:
        base += 40
    elif hora_llegada[i] <= 500:
        base += 25
    else:
        base += 5
    base += confianza[i] * 35
    base += liveness_score[i] * 15
    base += (happy[i] + neutral[i]) * 10
    base += np.random.normal(0, 3)
    puntaje[i] = round(np.clip(base, 0, 100), 2)

df = pd.DataFrame({
    'dia_semana':    dias_semana,
    'hora_llegada':  hora_llegada,
    'confianza':     confianza,
    'liveness_score': liveness_score,
    'happy':         happy,
    'neutral':       neutral,
    'sad':           sad,
    'angry':         angry,
    'puntaje_asistencia': puntaje
})

df.to_csv('dataset_asistencia.csv', index=False)
print(f"Dataset generado: {len(df)} filas")
print(df.head())