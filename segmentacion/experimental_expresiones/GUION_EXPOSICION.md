# Demostración de Parte 3: modalidad académica y experimental

Duración sugerida: 4–5 minutos. Abrir previamente ambas figuras para poder
presentar también sin ejecutar comandos en directo.

## 1. Presentar el objetivo y la conservación del original (30 segundos)

«Mi Parte 3 original agrupa perfiles mediante asistencia, tardanzas y promedio
de notas. Ese trabajo y sus resultados se conservan. Añadí una modalidad
experimental separada con una cuarta variable completamente sintética.»

Mostrar `segmentacion/visualizacion_clusters.png` y `descripcion_segmentos.md`.
El original eligió k=3 entre k≥3: 45, 70 y 35 perfiles, con silueta 0.2953.
Todos esos datos de demostración ya eran sintéticos.

## 2. Explicar la nueva variable (45 segundos)

«El nombre expresiones_positivas_ratio es una convención de la simulación.
Para cada perfil ficticio simulé 40 observaciones y dividí el conteo de la
categoría ficticia entre 40. No son fotografías, inferencias de EmoScan ni
mediciones de estudiantes. No representan emociones internas.»

Mostrar `resultados/datos_experimentales_sinteticos.csv`: ratio, conteo,
denominador y columnas `origen_datos` / `origen_expresiones` = `sintetico`.
Explicar que el generador no usa notas, asistencia ni tardanzas para obtener
la cuarta variable. No se usan etiquetas de entrenamiento ni IDs como variables.

## 3. Explicar StandardScaler y elección de k (1 minuto)

«Las proporciones van de 0 a 1 y las notas de 0 a 20. StandardScaler evita que
la escala de las notas domine las distancias. K-Means usa las cuatro variables
estandarizadas, con semilla fija y 30 inicializaciones.»

Mostrar `resultados/evaluacion_k_experimental.csv` y los paneles inferiores:

- Se evaluaron k=2…8.
- El mejor global por silueta fue k=2, aproximadamente 0.2972.
- Para mantener la política de al menos tres grupos de la entrega original,
  se eligió k=3, silueta 0.2374.
- El codo orientativo señaló k=4. Es una heurística y apoyo visual; no se
  afirma que coincida con la silueta ni que determine un número verdadero.
- Una silueta de 0.2374 no significa 23.74 % de aciertos.

## 4. Leer grupos y proyección PCA (1 minuto)

Mostrar `resultados/visualizacion_experimental.png` y `resumen_segmentos.csv`.

«PCA proyecta cuatro dimensiones en dos para visualizar. Conserva el 73.8 %
de la varianza estandarizada; el modelo no fue entrenado sobre este dibujo.»

«E1 contiene 45 perfiles, con asistencia media 35.6 %, tardanzas 3.7 %, nota
11.10 y ratio simulado 40.8 %. E2 contiene 60 perfiles, con 71.5 %, 7.9 %, 14.65
y 71.4 %. E3 contiene 45 perfiles, con 76.0 %, 11.4 %, 15.38 y 34.6 %. Son
promedios observados en datos ficticios, sin atribuciones psicológicas.»

No asociar E1 automáticamente con S1, ni presentar un ratio mayor como una
mejor persona, mayor atención, mayor aprendizaje, pronóstico o menor deserción.

## 5. Comparar y cerrar el alcance (45 segundos)

«Añadir una variable, incluso independiente y sintética, puede cambiar los
grupos porque modifica las distancias. Esta demostración explica el proceso;
no demuestra que las expresiones reales mejoren una segmentación ni autoriza
recoger datos faciales. No hay conexión al Monitor ni almacenamiento facial.»

Mostrar las pruebas: 7 originales y 10 nuevas. El archivo
`integridad_original.json` permite verificar que los diez originales no cambiaron.

## Comandos para la demostración

Desde la raíz, ejecutar los dos comandos documentados en README.md. El original
se dirige a `experimental_expresiones/demo_original`, para evitar sobrescribir
la entrega histórica; el nuevo utiliza `experimental_expresiones/resultados`.
No son necesarios backend, frontend, cámara ni base de datos.
