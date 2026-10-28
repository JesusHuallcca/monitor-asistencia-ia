# Parte 3 — Segmentación no supervisada con K-Means

Esta entrega funciona de forma independiente dentro de `segmentacion/`. No modifica
el backend, frontend, modelos supervisados ni los archivos de otros integrantes.
No requiere MySQL, reconocimiento facial, servidor web ni conexión a GitHub.

## Análisis del proyecto y fuente de datos

- `backend/app/db/models.py` define usuarios, sesiones, asistencias y notas.
- `ai/ml/train.py` implementa regresión logística supervisada; esta parte tiene un objetivo diferente: describir grupos.
- No se encontró un CSV histórico en la copia inicial del proyecto. `database/mysql/02_seed.sql`
  contiene cinco alumnos ficticios y sesiones, pero no un historial de asistencias suficiente.
- Se reutiliza **sin modificar** la función `generate_synthetic_attendance` de
  `ai/ml/generate_dataset.py`: 150 estudiantes × 45 sesiones = 6750 registros,
  con semilla 42. Sus perfiles internos no se usan como etiquetas ni variables.
- Estos datos son **SINTÉTICOS**. No representan estudiantes reales y no permiten
  sacar conclusiones sobre la institución. La procedencia aparece en CSV, figura e informe.

## Instalación y ejecución (PowerShell, desde la raíz del proyecto)

Python 3.10 o superior. Se recomienda un entorno independiente para esta entrega:

```powershell
python -m venv segmentacion/.venv
./segmentacion/.venv/Scripts/python.exe -m pip install -r segmentacion/requirements.txt
./segmentacion/.venv/Scripts/python.exe segmentacion/segmentacion_kmeans.py
./segmentacion/.venv/Scripts/python.exe -m unittest discover -s segmentacion -p "test_segmentacion.py" -v
```

Si ya tienes las dependencias instaladas, puedes sustituir la ruta al intérprete por
`python`. Si el alias de Windows no funciona, utiliza la ruta completa de tu instalación
de Python. No es necesario instalar los requisitos del backend.

El script resuelve las rutas desde su propia ubicación. También funciona desde otra
carpeta usando la ruta completa a `segmentacion_kmeans.py`. Por defecto escribe aquí.
`--output-dir` permite una subcarpeta dentro de `segmentacion`; para conservar dos
ejecuciones, usa subcarpetas distintas.

## Cómo funciona

1. Busca `data/dataset_asistencias.csv` y luego `data/dataset_asistencias_sintetico.csv`.
   Si ninguno existe, reutiliza el generador del proyecto. Un CSV existente inválido
   produce un error explícito; no se sustituye silenciosamente por datos inventados.
2. Valida identificadores, sesiones únicas, estados, procedencia y notas en 0–20.
   Rechaza faltantes y fuentes mezcladas. No imputa ausencias ni calificaciones.
3. Agrega una fila por `usuario_id`: asistencia (incluye tardanzas), tardanzas sobre
   sesiones observadas y promedio de notas. La cantidad de sesiones se conserva para auditoría.
4. Aplica `StandardScaler` a las tres variables. IDs, fechas, cursos, `perfil` y
   `asistira` quedan fuera del entrenamiento. No se duplican variables complementarias
   como asistencia y ausencia, que darían doble peso a la misma información.
5. Ejecuta K-Means con semilla 42, 30 inicializaciones y hasta 500 iteraciones.
   Evalúa k=2…8 (limitado por cantidad de estudiantes y perfiles distintos).
6. Elige la mayor silueta entre k≥3 por el requisito de la entrega. También informa
   el mejor k global, incluyendo k=2, y la inercia para la curva del codo.
7. Ordena los segmentos por asistencia media y les pone nombres relativos después
   de entrenar. PCA solo se usa para visualizar; no cambia las variables de K-Means.

## Entregables

| Archivo | Contenido |
|---|---|
| `segmentacion_kmeans.py` | Flujo reproducible y argumentos de ejecución |
| `segmentos_asignados.csv` | Una fila por estudiante: variables, origen, segmento y coordenadas PCA |
| `visualizacion_clusters.png` | Dispersión, PCA, silueta y codo en cuatro paneles |
| `descripcion_segmentos.md` | Resultados calculados, interpretación, acciones y guion para exponer |
| `README_Parte3.md` | Instrucciones y decisiones de esta entrega |
| `datos_asistencia_sinteticos.csv` | Historial sintético reutilizado para reproducir el análisis |
| `evaluacion_k.csv` | Silueta e inercia por cada k evaluado |
| `metricas_segmentacion.json` | Procedencia, parámetros, versiones y métricas |
| `test_segmentacion.py` | Pruebas con unittest, sin dependencias del backend |
| `requirements.txt` | Dependencias exclusivas de esta parte |

## Usar un CSV propio

```powershell
python segmentacion/segmentacion_kmeans.py --dataset ruta/al/historial.csv --origen real --output-dir segmentacion/resultados_reales
```

`--origen real` es una declaración del usuario sobre su fuente; el script no puede
verificarla. Sin declaración ni columna de procedencia se marca `no_verificado`.
Un archivo con `sintetico` en el nombre se marca sintético si falta la columna.
Si ya existe `origen_datos`, esa columna es la fuente de procedencia y se valida.

Contrato mínimo (filas por estudiante y sesión):

```csv
usuario_id,sesion_id,estado,promedio_notas,origen_datos
101,1,PRESENTE,15.5,real
101,2,AUSENTE,15.5,real
```

El ejemplo solo muestra el formato: se necesitan al menos cuatro estudiantes y
tres perfiles numéricos diferentes. `sesion` puede sustituir a `sesion_id`;
si hay `curso_id`, se incluye en la clave de duplicados. `promedio_notas` debe
ser el promedio académico comparable de ese estudiante; no una nota aislada.
Se aceptan PRESENTE, TARDANZA y AUSENTE (normalizados a mayúsculas).
Los datos históricos reales deben incluir ausencias explícitas de todas las clases
esperadas y un periodo comparable. Un export solo de marcaciones positivas no
sirve para medir asistencia. No se ejecuta SQL ni se consulta la base de datos.

## Pruebas y exposición

Las pruebas verifican las fórmulas de agregación, rechazo de datos inválidos,
duplicados y fuentes mezcladas, ausencia de etiquetas objetivo en el entrenamiento,
reproducibilidad, selección de al menos tres grupos, archivos y formato PNG.
La prueba de integración escribe únicamente en una carpeta temporal bajo `segmentacion`
y la elimina al finalizar.

Consulta `descripcion_segmentos.md` para los valores efectivamente calculados y un
guion de dos minutos. Explica que la silueta mide separación interna, **no exactitud**,
y que imponer k≥3 es un requisito del trabajo. Los segmentos son descriptivos:
no equivalen a un diagnóstico ni a la predicción de la siguiente asistencia.

No se realizan commits, pushes ni publicaciones automáticamente.

## Resultado de la ejecución de entrega

Ejecución verificada con Python 3.14.7, NumPy 2.5.2, Pandas 3.0.5,
scikit-learn 1.9.0 y Matplotlib 3.11.1. **7 pruebas aprobadas** con unittest,
incluida la generación completa y la igualdad del CSV al repetir la ejecución.
También se inspeccionó visualmente la figura generada.

| Segmento | Estudiantes | Asistencia media | Tardanzas / sesiones | Nota media |
|---|---:|---:|---:|---:|
| S1: asistencia relativa baja | 45 | 34,7 % | 3,9 % | 10,88 |
| S2: asistencia relativa intermedia | 70 | 68,2 % | 7,0 % | 14,93 |
| S3: asistencia relativa alta | 35 | 85,0 % | 13,8 % | 15,31 |

Se eligió **k=3**, con silueta **0,2953**, entre los valores admisibles de al menos
tres segmentos. El mejor global fue k=2, con 0,3709; k=4 obtuvo 0,2948,
muy cerca de k=3. La separación es limitada y hay solapamiento: no se presenta
como una clasificación exacta. Las dos componentes PCA conservan el 88,3 %
de la varianza estandarizada. S3 tiene la mayor asistencia, pero también más
tardanzas por sesión; conviene mencionarlo al proponer seguimiento de puntualidad.

Esta tabla resume la ejecución con semilla 42 y datos sintéticos. Si cambias
los datos o parámetros, consulta los informes regenerados; esta sección del README
conserva el resultado de la entrega original.
