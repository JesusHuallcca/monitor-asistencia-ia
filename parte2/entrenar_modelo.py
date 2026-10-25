import pandas as pd
import numpy as np
import joblib
import json
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('dataset_asistencia.csv')
y = df['puntaje_asistencia']
features = ['dia_semana','hora_llegada','confianza','liveness_score','happy','neutral','sad','angry']
X = df[features]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

modelo = LinearRegression().fit(X_train_s, y_train)
y_pred = modelo.predict(X_test_s)

joblib.dump(modelo, 'modelo_regresion.pkl')
joblib.dump(scaler, 'scaler_regresion.pkl')

print(f"R²  = {r2_score(y_test, y_pred):.4f}")
print(f"MAE = {mean_absolute_error(y_test, y_pred):.4f}")
print("✅ modelo_regresion.pkl y scaler_regresion.pkl actualizados")