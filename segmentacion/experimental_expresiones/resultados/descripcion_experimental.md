# Resultados experimentales: cuatro variables sintéticas

**No son estudiantes reales ni resultados obtenidos por EmoScan.**

Se agregaron 6750 sesiones en 150 perfiles ficticios.

K elegido: **3**, silueta **0.2374** entre k≥3. Mejor k global: **2**. Codo orientativo: **4**.

Se conserva k≥3 para comparar el procedimiento con la entrega académica. No demuestra un número natural de grupos. Si silueta y codo difieren, se informa la discrepancia; la elección usa silueta y el codo es apoyo exploratorio.

PCA conserva **73.8%** de la varianza estandarizada en dos dimensiones. K-Means se ajustó en cuatro dimensiones, antes de PCA.

## Características observadas en esta simulación

| Grupo | Perfiles | Asistencia | Tardanzas/sesiones | Nota media | Ratio de expresiones SINTÉTICO |
|---|---:|---:|---:|---:|---:|
| E1 | 45 | 35.6% | 3.7% | 11.10 | 40.8% |
| E2 | 60 | 71.5% | 7.9% | 14.65 | 71.4% |
| E3 | 45 | 76.0% | 11.4% | 15.38 | 34.6% |

Los grupos E1…Ek se numeran por asistencia media ascendente. No se emparejan automáticamente con S1…Sk de la modalidad original.

- E1: 45 perfiles; asistencia 35.6%, tardanzas 3.7%, nota media 11.10 y ratio simulado 40.8%. Son medias descriptivas de esta muestra ficticia.
- E2: 60 perfiles; asistencia 71.5%, tardanzas 7.9%, nota media 14.65 y ratio simulado 71.4%. Son medias descriptivas de esta muestra ficticia.
- E3: 45 perfiles; asistencia 76.0%, tardanzas 11.4%, nota media 15.38 y ratio simulado 34.6%. Son medias descriptivas de esta muestra ficticia.

## Procedencia e interpretación

La cuarta variable es conteo binomial simulado / 40 muestras ficticias por perfil. Se sorteó una probabilidad uniforme entre 0.05 y 0.95 por perfil y después un conteo binomial. No se derivó de fotografías, notas ni asistencia. No se importó ni invocó EmoScan.

«Positivas» es exclusivamente el nombre de una categoría ficticia de esta demostración. No afirma que una persona tenga emociones positivas ni permite interpretar atención, rendimiento futuro o riesgo de deserción.

La independencia del mecanismo generador no impide correlaciones accidentales en una muestra finita. StandardScaler da escala comparable a todas las variables: incluso una variable sintética puede cambiar la geometría y los grupos. Un cambio de silueta no demuestra utilidad de expresiones reales. Las inercias de tres y cuatro dimensiones no son directamente comparables.

El CSV académico debe declarar origen_datos=sintetico. Esa declaración no certifica por sí sola una fuente desconocida; usar solamente el archivo sintético distribuido o simulaciones propias.

## Reproducibilidad

Semilla K-Means: 42; semilla expresiones: 2026. n_init=30; max_iter=500; un hilo de cálculo; versiones y hash de entrada en metricas_experimentales.json.
