# Exposición de Parte 3: cuatro variables sintéticas

Duración sugerida: 3–4 minutos. Abrir `resultados/visualizacion_clusters.png`
y `resultados/resumen_segmentos.csv` antes de comenzar.

1. **Objetivo y fuente.** «Agrupo 150 perfiles ficticios sin etiquetas de entrenamiento.
   Agrego 6750 sesiones en una fila por perfil y uso asistencia, tardanzas, promedio
   de notas y expresiones positivas sintéticas».
2. **Cuarta variable.** «Simulo 40 observaciones por perfil. El ratio es el conteo
   simulado dividido entre 40. No procede de fotografías, EmoScan ni personas reales.
   La simulación no consulta asistencia, tardanzas ni notas».
3. **Modelo.** «Estandarizo las cuatro variables para comparar sus escalas. K-Means
   trabaja en cuatro dimensiones con semilla fija. PCA se aplica después para dibujar».
4. **Elección de k.** Mostrar `resultados/evaluacion_k.csv`. «Comparé k=2…8. Por el
   requisito de al menos tres grupos, elegí k=3 con silueta 0.2374. El mejor global
   fue k=2 y el codo orientativo k=4. Silueta no es porcentaje de aciertos».
5. **Resultados.** «E1 reúne 45 perfiles, E2 reúne 60 y E3 reúne 45. La tabla muestra
   las medias de las cuatro variables. PCA conserva aproximadamente 73.8 % de la
   varianza. Son patrones de esta simulación, sin interpretaciones psicológicas».
6. **Alcance y reproducibilidad.** «Las semillas y versiones están en las métricas.
   Los datos son completamente sintéticos. El análisis anterior de tres variables
   se puede recuperar desde Git; la entrega principal usa cuatro».

Desde la raíz:

```powershell
python -B segmentacion/segmentacion_kmeans.py
python -B -m unittest discover -s segmentacion -t . -v
```
