# Resultados de la integración final

La verificación posterior del dashboard interactivo se documenta en [REDISENO_SEGMENTACION.md](REDISENO_SEGMENTACION.md).

Fecha: 26 de octubre de 2026, America/Lima.
Worktree: `monitor-asistencia-integracion-segmentacion`.
Rama: `integracion-segmentacion-ia`, basada en `b33ed02` y sin confirmar cambios.

## Verificación ejecutada sobre el worktree final

| Comprobación | Resultado |
|---|---|
| Python: integración nueva y regresiones EmoScan | **63 pruebas aprobadas**, 9.74 s |
| Python: K-Means definitivo | **10 pruebas aprobadas**, 11.315 s |
| Programa CLI de K-Means | **Salida 0**, resultados regenerados |
| JavaScript en Chrome sin ventana | **30 comprobaciones aprobadas** |
| JavaScript de regresión de asistencia opcional | **14 comprobaciones aprobadas** |
| Total | **73 pruebas Python y 44 comprobaciones JavaScript** |

Python ejecutado con `-B`; las pruebas usan SQLite en memoria, cuentas ficticias y
un bloqueo explícito de conexiones MySQL. Los endpoints se verifican en la aplicación
FastAPI completa, con la dependencia de base de datos sustituida por SQLite.
Se usa el JWT real de la aplicación y el rol almacenado del usuario, sin confiar
en un rol inventado en el token. No se conectó a una base de producción.

Se ejecutaron:

```powershell
python -B -m pytest backend/tests/integracion_final backend/tests/emoscan -q -p no:cacheprovider
python -B -m unittest discover -s segmentacion -t . -v
python -B segmentacion/segmentacion_kmeans.py
node frontend/tests/integracion-final.test.cjs
node frontend/tests/emoscan.test.js
```

Para repetirlos, la preparación de dependencias y la fixture calculada del navegador
están documentadas en [INTEGRACION_FINAL.md](INTEGRACION_FINAL.md).

## K-Means y carga CSV

La demostración y la carga del CSV incluido devuelven los mismos resultados,
comparados con `prepare_students` y `fit_segments` del algoritmo definitivo.
Los archivos nuevos se calculan, sin fijar K ni las métricas de la demostración.

| Resultado calculado | Valor |
|---|---|
| Sesiones | 6750 |
| Perfiles | 150 |
| Variables | 4 |
| K elegido entre K≥3 | 3 |
| Silueta | 0.2373692496101911 |
| Tamaños E1 / E2 / E3 | 45 / 60 / 45 |
| Mejor K global | 2 |
| Codo orientativo | 4 |
| Varianza PCA 2D | 73.8058 % |

Se verificaron errores por tipo/extensión, UTF-8 inválido, cabeceras o filas mal
formadas, columnas duplicadas o desconocidas, origen no sintético, expresiones
externas, faltantes, notas no numéricas/no finitas/fuera de rango, identificadores
inválidos, sesiones duplicadas, pocos perfiles, más de 500 perfiles, más de 10000
filas y más de 2 MiB. El límite de bytes se comprueba también sobre el flujo de
entrada, sin depender de Content-Length. El cálculo no crea archivos ni registros
de estudiantes en el servidor.

La prueba de navegador usa un JSON calculado por el modelo real como respuesta de
prueba. Comprueba cuatro dispersiones, 600 puntos para los 150 perfiles, filtro de
cluster, valores al pasar el cursor, cinco gráficos de barras, dos curvas de K,
tarjetas, descarga exacta del CSV y borrado de resultados anteriores ante errores.
Se comprobó el diseño en escritorio y a 390 píxeles de ancho.

## EmoScan, consentimiento y asistencia

Las pruebas nuevas cubren protección de cada ruta personal, consentimiento específico
versionado, independencia del consentimiento de asistencia, límites de imagen, formato
JPEG, servicio desactivado/ocupado, resultados privados por usuario, caducidad,
revocación y descarte. Analizar y repetir no invocan el servicio de registro de asistencia.

Se conservaron y ejecutaron las regresiones de la rama EmoScan: asistencia confirmada
antes de encolar el análisis opcional, fallos que no revierten la asistencia,
identidad/liveness inválidos sin análisis, colas acotadas, expiración, aislamiento,
revocación de trabajos y la interfaz Flask existente sin abrir una cámara.

**Se ejecutó inferencia FERPlus real** en el worker aislado con el modelo existente
y la imagen pública de NASA preparada para las pruebas originales. La fotografía
se mantiene ignorada por Git; no es una captura de estudiantes. También se probó
la indisponibilidad ante modelo ausente.

La prueba de navegador de la pantalla personal usa vídeo generado por canvas y
puntuaciones de prueba. Comprueba aceptación, vista previa sin análisis automático,
ocho barras, repetición, ausencia de llamadas de asistencia, revocación con respuesta
atrasada, apagado al salir y error recuperable de permiso de cámara. Comprueba también
redirecciones de estudiante y administrador desde pantallas de otro rol.

## Entorno y límites

El equipo no ofrecía `python` ni `node` utilizables por su alias habitual. Se usó el
intérprete existente `../monitor-asistencia-ia/segmentacion/.venv/Scripts/python.exe`
sin modificarlo, con dependencias de prueba descargadas a la caché ignorada de Parte 3;
JavaScript se ejecutó con el runtime incluido en Playwright. Chrome estaba instalado.
No se incluyeron entornos virtuales, librerías descargadas, secretos, logs ni imágenes
de prueba en los cambios que se preparan para Git.

Python 3.14.7; NumPy 2.5.4; pandas 3.1.0; scikit-learn 1.9.1; Matplotlib 3.11.2;
OpenCV 4.11.0; ONNX Runtime 1.31.1. Para la integración se exige OpenCV <5:
la primera descarga de OpenCV 5 carecía de CascadeClassifier, utilizado por el worker
existente. Se corrigió la dependencia y la suite final quedó completamente aprobada.
Las advertencias no bloqueantes finales corresponden a TestClient/httpx y al perfil
de color PNG de la fotografía pública.

**No se probó una cámara física**, un rostro enrolado real, una marcación real ni el
login conectado a una base de desarrollo operativa. Esas comprobaciones necesitan
hardware, cuentas y modelos de identidad configurados. No se ejecutó la suite completa
de módulos ajenos a esta integración ni se afirma que esté aprobada. El navegador
usa dobles de transporte; los endpoints reales, el JWT y los roles se verificaron
separadamente en Python. No se aplicaron scripts SQL a MySQL.

Los registros locales de la ejecución están en `segmentacion/.cache/`:
`backend_tests.log`, `kmeans_tests.log`, `kmeans_cli.log`, `browser_tests.log` y
`emoscan_js_tests.log`. La captura del profesor está en
`segmentacion/.cache/qa/segmentacion-profesor.png`.

## Git y conservación

Se verifican las referencias de Git, incluidos `main`, `parte-3-segmentacion`,
`integracion-emoscan` y la nueva rama. Los tres stashes se conservan:

```text
ea354b5c14574be861b11e6d4326124d7547e163
7560d9d4c6d3d220af3f720fc9763d3cf355d9e0
3949fd59ab553975ad9e0ad4d477af833e04e28a
```

Se comprueban los diffs de los dos worktrees de origen contra los guardados antes
de la integración y la igualdad del algoritmo definitivo, el login y los módulos
faciales conservados. Los archivos importados de EmoScan conservan el contenido del
commit `542698f`, salvo el registro de routers y cierre de servicios de `app/main.py`.
`git diff --check` finalizó sin errores. No hay commits, merges ni pushes.
