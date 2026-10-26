# Parte 3: descripción de segmentos

**Origen: SINTETICO.** Generador existente ai/ml/generate_dataset.py (150 estudiantes x 45 sesiones).

Se analizaron 6750 registros y 150 estudiantes. Cada estudiante participa una sola vez en K-Means.

## Método y elección de k

Se agregaron asistencia (PRESENTE o TARDANZA / sesiones observadas), tardanzas (TARDANZA / sesiones observadas) y promedio de notas (0–20). StandardScaler lleva cada variable a media 0 y desviación estándar 1. No se utilizan usuario_id, curso_id, perfil ni asistira para entrenar. Las notas repetidas por sesión se promedian: el CSV debe contener un promedio académico comparable, no notas individuales por evaluación.

Se evaluó k de 2 a 8. Mejor k global por silueta: **2**. Mejor k entre los admisibles (k ≥ 3): **3**, silueta **0.2953**. El mínimo de tres grupos es una restricción de la entrega; no prueba que existan tres clases naturales. La inercia se reporta como apoyo visual y no determina automáticamente el codo.

| k | Silueta | Inercia |
|---|---:|---:|
| 2 | 0.3709 | 252.48 |
| 3 | 0.2953 | 194.44 |
| 4 | 0.2948 | 158.58 |
| 5 | 0.2915 | 132.75 |
| 6 | 0.2867 | 118.61 |
| 7 | 0.2769 | 105.19 |
| 8 | 0.2797 | 94.40 |

## Segmentos encontrados

Los nombres son relativos a esta muestra y se asignan después del agrupamiento; no son umbrales institucionales ni diagnósticos.

| Segmento | Estudiantes | Asistencia media | Tardanzas / sesiones | Nota media |
|---|---:|---:|---:|---:|
| S1: asistencia relativa baja | 45 | 34.7% | 3.9% | 10.88 |
| S2: asistencia relativa intermedia | 70 | 68.2% | 7.0% | 14.93 |
| S3: asistencia relativa alta | 35 | 85.0% | 13.8% | 15.31 |

### Interpretación y acciones propuestas

- **S1: asistencia relativa baja**: asistencia media 34.7%, tardanzas 3.9% y notas 10.88. Revisar barreras de asistencia y ofrecer acompañamiento individual.
- **S2: asistencia relativa intermedia**: asistencia media 68.2%, tardanzas 7.0% y notas 14.93. Realizar seguimiento preventivo y conversar sobre puntualidad y hábitos.
- **S3: asistencia relativa alta**: asistencia media 85.0%, tardanzas 13.8% y notas 15.31. Mantener seguimiento y reconocer la continuidad. Este grupo tiene la mayor proporción de tardanzas por sesión; revisar también la puntualidad.

## Guion para la exposición (2 minutos)

1. «Mi objetivo es descubrir grupos de estudiantes con comportamientos similares, sin una etiqueta objetivo.»
2. «La fuente es sintetico; usamos 150 estudiantes. Agrupamos las sesiones para evitar que un estudiante con más registros pese más.»
3. «Usamos asistencia, tardanzas y notas. Estandarizamos porque las notas van de 0 a 20 y las proporciones de 0 a 1.»
4. «Comparamos varios k con silueta. Elegimos 3 entre los valores de al menos tres; la silueta fue 0.2953. El mejor k sin esa restricción fue 2.»
5. «En la tabla explico tamaño y promedios de cada segmento y propongo acompañamiento según el patrón observado.»
6. «El gráfico PCA solo resume el espacio en dos dimensiones; el agrupamiento usa las tres variables originales estandarizadas.»

## Alcances y límites

- La silueta mide separación interna (−1 a 1); no es exactitud, probabilidad ni porcentaje de aciertos.
- Revisar valores de silueta cercanos entre distintos k: una diferencia pequeña no demuestra una superioridad robusta. Hay solapamiento entre perfiles.
- Si el origen es sintético, estos resultados demuestran el procedimiento y no describen alumnos reales. El generador ya introduce patrones y correlaciones entre asistencia y notas.
- No se predice la próxima asistencia ni se reutiliza la regresión logística de ai/ml/train.py.
- Las tasas usan solo sesiones registradas. No inferimos ausencias de registros inexistentes; un CSV real debe incluir explícitamente todas las sesiones esperadas y sus ausencias.
- Se combinan cursos y periodos del CSV. Para comparar estudiantes reales, filtrar un periodo y poblaciones con oportunidades de asistencia comparables antes de ejecutar.
- No se imputan notas ni se mezclan datos reales con sintéticos: entradas incompletas se rechazan.
- K-Means favorece grupos compactos y es sensible a escalas, atípicos y semilla. La estabilidad con otras muestras debe validarse antes de uso institucional.
- Semilla 42; n_init=30; max_iter=500. Versiones en metricas_segmentacion.json.
