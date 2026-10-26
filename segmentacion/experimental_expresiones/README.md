# Parte 3: segunda modalidad experimental con expresiones sintéticas

Rama de trabajo: `parte-3-segmentacion`. La modalidad académica original de tres
variables y sus diez archivos se conservan sin cambios, incluidos sus resultados.
Todo lo añadido está en `segmentacion/experimental_expresiones/`.

## Qué demuestra

Se mantienen `asistencia_ratio`, `tardanzas_ratio` y `promedio_notas`; se añade
`expresiones_positivas_ratio`. **Todos los datos de esta demostración son
sintéticos. La cuarta variable no procede de EmoScan ni de estudiantes reales.**

EmoScan proporciona el contexto de una posible variable de expresiones estimadas,
pero este experimento no lo importa, no llama a su API ni utiliza su modelo.
No necesita cámara, MySQL, backend, frontend ni credenciales. No se cambió ningún
archivo de los compañeros para implementar esta modalidad.

## Datos y método

- Entrada predeterminada: el historial sintético ya distribuido en
  `segmentacion/datos_asistencia_sinteticos.csv`, 6750 sesiones / 150 perfiles.
- Una fila por usuario ficticio. Asistencia = (PRESENTE + TARDANZA) / sesiones;
  tardanzas = TARDANZA / sesiones; notas = promedio de la columna académica.
- No se imputan ausencias o notas. Se rechazan duplicados, faltantes, estados
  desconocidos y notas fuera de 0–20. Se exige `origen_datos=sintetico`.
- Se rechazan columnas de expresiones de entrada. La cuarta variable solo se
  genera en este programa: por perfil se sortea p ~ Uniforme(0.05, 0.95), después
  C ~ Binomial(40, p); ratio = C/40. Las 40 observaciones son ficticias y no
  corresponden a capturas ni a las 45 sesiones académicas.
- Semilla de expresiones 2026, separada de la semilla K-Means 42. El generador
  no consulta notas, asistencia, tardanzas ni etiquetas académicas. Puede haber
  correlaciones accidentales en una muestra finita.
- StandardScaler se ajusta sobre las cuatro variables. K-Means usa las cuatro
  columnas estandarizadas; excluye IDs, orígenes, conteos auxiliares y objetivos.
- Se evalúa k=2…8 con silueta e inercia. Se selecciona la mayor silueta entre
  k≥3 para conservar la política de la entrega original; también se informa el
  mejor k global. No se afirma que existan tres clases naturales.
- El método del codo se muestra gráficamente y se informa una sugerencia
  heurística: máxima distancia bajo la cuerda de la inercia normalizada frente
  al k normalizado, entre los extremos evaluados. No reemplaza la silueta ni
  prueba un número verdadero de grupos.
- PCA se ajusta después del agrupamiento y solo se usa para visualizar en 2D.
- E1…Ek se ordenan por asistencia media. No son etiquetas emocionales y no
  se corresponden automáticamente con los segmentos S1…Sk del original.

«Positivas» es el nombre de una categoría ficticia elegida para la demostración;
no permite atribuir emociones internas, atención, desempeño futuro ni riesgo de
deserción. El programa no recopila ni guarda expresiones de personas reales.

La marca de procedencia es una declaración, no una prueba de autenticidad. Usar
solo el archivo sintético distribuido o simulaciones propias; no renombrar ni
remarcar datos reales como sintéticos.

## Ejecutar ambas modalidades en Windows

Desde la raíz del repositorio, usando el entorno existente de Parte 3:

```powershell
git branch --show-current
.\segmentacion\.venv\Scripts\python.exe --version
```

La ejecución de verificación usó Python 3.14.7, NumPy 2.5.4, pandas 3.1.0,
scikit-learn 1.9.1 y Matplotlib 3.11.2. No se instaló ni modificó ningún entorno.
Se reutiliza `segmentacion/requirements.txt`, sin dependencias adicionales.

Para dirigir también la caché de Matplotlib al experimento:

```powershell
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'segmentacion/experimental_expresiones/.cache/matplotlib'
```

**Modalidad original, sin sobrescribir los entregables históricos:**

```powershell
.\segmentacion\.venv\Scripts\python.exe -B segmentacion/segmentacion_kmeans.py --dataset segmentacion/datos_asistencia_sinteticos.csv --output-dir segmentacion/experimental_expresiones/demo_original
```

El script original también funciona con sus argumentos habituales. Para la
exposición se recomienda el comando anterior porque escribe una copia separada.

**Modalidad experimental:**

```powershell
.\segmentacion\.venv\Scripts\python.exe -B segmentacion/experimental_expresiones/segmentacion_expresiones.py
```

Las salidas predeterminadas van a `experimental_expresiones/resultados/`. Se
rechaza cualquier salida fuera de `experimental_expresiones`, de modo que esta
modalidad no puede escribir encima de los resultados académicos originales.
La entrada también debe estar dentro de `segmentacion`.

Una segunda simulación, conservando la primera:

```powershell
.\segmentacion\.venv\Scripts\python.exe -B segmentacion/experimental_expresiones/segmentacion_expresiones.py --seed-expresiones 7 --output-dir segmentacion/experimental_expresiones/resultados_semilla7
```

No hace falta activar el entorno virtual. `-B` evita generar bytecode de módulos
del proyecto fuera de esta carpeta. La caché y la copia de demostración original
se excluyen de Git mediante el `.gitignore` local.

## Archivos añadidos

| Archivo | Contenido |
|---|---|
| `segmentacion_expresiones.py` | CLI, validación, simulación, StandardScaler, K-Means, silueta, codo y PCA |
| `test_expresiones.py` | Diez pruebas automatizadas de la modalidad y su independencia |
| `integridad_original.json` | SHA-256 de los diez archivos originales antes de modificar la entrega |
| `GUION_EXPOSICION.md` | Secuencia y explicación para presentar ambas modalidades |
| `RECUPERAR_EMOSCAN.md` | Resguardo local y recuperación segura sin commits |
| `resultados/datos_experimentales_sinteticos.csv` | 150 perfiles sintéticos con el conteo/denominador de expresiones |
| `resultados/segmentos_experimentales.csv` | Variables, procedencias, segmento y coordenadas PCA |
| `resultados/resumen_segmentos.csv` | Tamaños y medias observadas por grupo |
| `resultados/evaluacion_k_experimental.csv` | Silueta e inercia por k |
| `resultados/metricas_experimentales.json` | Semillas, escalado, métricas, PCA, versiones y hash de entrada |
| `resultados/visualizacion_experimental.png` | PCA, centroides estandarizados, silueta y codo |
| `resultados/descripcion_experimental.md` | Descripción calculada de los resultados y sus límites |

## Resultados calculados

| Modalidad | Variables | k elegido entre k≥3 | Silueta | Mejor k global | Varianza PCA 2D |
|---|---:|---:|---:|---:|---:|
| Académica original, conservada | 3 | 3 | 0.2953 | 2 | 88.3 % |
| Experimental sintética, semilla 2026 | 4 | 3 | 0.2374 | 2 | 73.8 % |

El codo orientativo experimental es k=4. Se muestra la discrepancia con la
elección por silueta, sin ocultar que el mejor global por silueta fue k=2.
Silueta no es exactitud. Cambiar el espacio de variables cambia las distancias;
no corresponde concluir que una modalidad es más válida o predictiva. Tampoco
se comparan directamente las inercias de espacios con distinta dimensionalidad.

| Grupo experimental | Perfiles ficticios | Asistencia media | Tardanzas/sesiones | Nota media | Ratio expresiones SINTÉTICO |
|---|---:|---:|---:|---:|---:|
| E1 | 45 | 35.6 % | 3.7 % | 11.10 | 40.8 % |
| E2 | 60 | 71.5 % | 7.9 % | 14.65 | 71.4 % |
| E3 | 45 | 76.0 % | 11.4 % | 15.38 | 34.6 % |

Estas son características observadas en una simulación, no perfiles psicológicos
o diagnósticos. El generador académico original ya incluye correlaciones entre
variables académicas. Añadir una cuarta variable con escala equivalente puede
reorganizar los grupos aunque su mecanismo de generación sea independiente.

## Pruebas ejecutadas

```powershell
.\segmentacion\.venv\Scripts\python.exe -B -m unittest discover -s segmentacion -p test_segmentacion.py -v
.\segmentacion\.venv\Scripts\python.exe -B -m unittest discover -s segmentacion/experimental_expresiones -p test_expresiones.py -v
```

Resultado: **7 pruebas originales y 10 nuevas aprobadas**. Se comprobaron
integridad SHA-256, fórmulas académicas, simulación reproducible y separada de
las variables académicas, rechazo de fuentes reales/no verificadas, uso efectivo
de las cuatro variables, selección de k, codo, PCA, CSV/PNG, repetibilidad y
ejecución de ambos CLI con salidas diferentes.

Los temporales de las nuevas pruebas se crean dentro del experimento y se
limpian al terminar. Se inspeccionó visualmente la figura generada. No se
ejecutaron modelos faciales, servicios web, consultas SQL, commits ni push.
