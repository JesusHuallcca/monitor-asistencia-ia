# Parte 1 — Datos + Estadística Básica

## Ejecución
Desde esta carpeta, ejecutar:

```powershell
py -3.12 stats_empresa_v2.py
```

## Fuentes de datos
- `dataset_asistencia_sintetico.csv`: datos de asistencia sintéticos.
- CSV de EmoScan encontrados en `EmoScan - copia (2)/logs`.

## Métodos estadísticos
Se calculan media, mediana, varianza muestral y desviación estándar muestral.
Las probabilidades son frecuencias empíricas observadas en los datos disponibles.
Se utilizan Pandas para limpiar y resumir datos, NumPy para estadística numérica
y Matplotlib para generar gráficos.

## Definiciones
PRESENTE y TARDANZA se consideran asistencia; AUSENTE, inasistencia.
El ratio histórico de 30 días se analiza por separado.
Los registros emocionales con puntajes todos cero se contabilizan y se señalan
como observaciones que requieren interpretación técnica.

## Entregables
- `dataset_ejemplo.csv`: fuentes reunidas en un archivo, diferenciadas por `tipo_registro`.
- `reporte_kpis.json`: estadísticas, probabilidades, calidad de datos y limitaciones.
- `graficos_estadisticos.png`: cuatro gráficos descriptivos.

## Limitaciones
La asistencia es sintética, no un registro real del centro educativo.
Las observaciones emocionales no son diagnósticos clínicos. No se vinculan
emociones con estudiantes porque no existe una clave común validada.
Las frecuencias observadas no predicen resultados futuros.
Los puntajes emocionales no se normalizan porque su escala no está confirmada.
