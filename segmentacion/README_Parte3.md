# Parte 3: K-Means con cuatro variables sintéticas

La versión principal agrupa **150 perfiles sintéticos** usando asistencia,
tardanzas, promedio de notas y expresiones positivas sintéticas. El modelo está
en `segmentacion_kmeans.py`; sus gráficos, métricas e informes están en `resultados/`.
La versión anterior de tres variables se puede recuperar desde Git. La carpeta
actual contiene únicamente el modelo de cuatro variables y sus archivos necesarios.

## Ejecutar desde la raíz del worktree

Con Python y las dependencias de `segmentacion/requirements.txt` instaladas:

```powershell
python -B segmentacion/segmentacion_kmeans.py
python -B -m unittest discover -s segmentacion -t . -v
```

Si necesitas un entorno local:

```powershell
python -m venv segmentacion/.venv
.\segmentacion\.venv\Scripts\python.exe -m pip install -r segmentacion/requirements.txt
.\segmentacion\.venv\Scripts\python.exe -B segmentacion/segmentacion_kmeans.py
.\segmentacion\.venv\Scripts\python.exe -B -m unittest discover -s segmentacion -t . -v
```

## Datos y método

- Entrada predeterminada: `datos_asistencia_sinteticos.csv`.
  Se reutilizan sin modificar sus 6750 sesiones: 150 usuarios ficticios, 45 sesiones cada uno.
- Asistencia = (PRESENTE + TARDANZA) / sesiones; tardanzas = TARDANZA / sesiones;
  promedio de notas = media académica, en escala de 0 a 20.
- La cuarta variable es `expresiones_positivas_ratio`: conteo binomial simulado / 40
  observaciones ficticias por perfil, con probabilidad uniforme entre 0.05 y 0.95.
  Su generador usa semilla 2026 y no consulta las otras variables ni etiquetas.
- StandardScaler y K-Means trabajan con las **cuatro columnas**. No se usan IDs,
  etiquetas ni conteos auxiliares como variables de entrenamiento.
- Semilla K-Means 42, 30 inicializaciones y 500 iteraciones máximas. Se evalúa k=2…8;
  se elige la mayor silueta entre k≥3, por requisito de la entrega. El mejor k global
  y el codo orientativo se informan por separado. PCA solo sirve para visualizar.
- Se rechazan fuentes no sintéticas, expresiones externas, duplicados, faltantes
  y valores fuera de rango. La entrada debe estar dentro de `segmentacion/` y la
  salida dentro de esa carpeta.

Todos los datos son sintéticos. No hay conexión con EmoScan, cámara, base de datos,
backend ni frontend. «Positivas» es una categoría ficticia; no mide emociones internas,
atención ni riesgo de deserción. La silueta mide separación interna, no exactitud.

## Resultados principales

| Archivo en `resultados/` | Contenido |
|---|---|
| `datos_perfiles_sinteticos.csv` | 150 perfiles, cuatro variables y procedencia sintética |
| `segmentos_asignados.csv` | Perfiles, segmentos E1…Ek y coordenadas PCA |
| `resumen_segmentos.csv` | Tamaño y medias por segmento |
| `evaluacion_k.csv` | Silueta e inercia para cada k |
| `metricas_segmentacion.json` | Variables, semillas, hash de entrada, escalado, PCA y versiones |
| `visualizacion_clusters.png` | PCA, centroides de cuatro variables, silueta y codo |
| `descripcion_segmentos.md` | Informe calculado e interpretación |

Con las semillas predeterminadas: k=3, silueta 0.2374, grupos de 45, 60 y 45 perfiles;
mejor k global 2, codo orientativo 4 y varianza PCA 2D 73.8 %.
Consulta los archivos calculados para los valores completos.

Una ejecución alternativa conserva los resultados principales:

```powershell
python -B segmentacion/segmentacion_kmeans.py --seed-expresiones 7 --output-dir segmentacion/resultados_semilla7
```

## Recuperar la versión anterior desde Git

Antes de eliminar las copias antiguas se verificaron los diez archivos originales
contra el commit `5a0f2a54d87aa2c61a6cb338922a29b0aa0f0a47`: sus hashes SHA-256
coinciden con el manifiesto previo considerando la normalización LF/CRLF de Git.
La documentación y los resultados de la antigua carpeta experimental también
coinciden con los guardados en `b33ed020e7972ad7b1e1808381ecec1969e47bd2`.
El CSV compartido se conserva sin cambiar sus bytes; no se necesitan copias locales
de los scripts, pruebas, gráficos ni manifiestos antiguos.

Para consultar o exportar la entrega original sin cambiar la rama ni los archivos
actuales, ejecutar desde la raíz:

```powershell
git show 5a0f2a5:segmentacion/segmentacion_kmeans.py
git archive --format=zip --output=segmentacion/.cache/parte3-original.zip 5a0f2a5 segmentacion/
```

El segundo comando requiere que exista `segmentacion/.cache/`; se puede crear con
`New-Item -ItemType Directory -Force segmentacion/.cache`.

`GUION_EXPOSICION.md` presenta exclusivamente la versión principal. El informe de
verificación está en `RESULTADOS_PRUEBAS.md`.
