# EmoScan en el registro de asistencia

Implementado en `integracion-emoscan`, 25 de octubre de 2026. Desactivado por defecto.

## Flujo y garantías

1. `frontend/components/camera.js` conserva su cámara y su JPEG habitual.
2. Los endpoints `/api/attendance/check-in` y `/api/attendance/camera/check-in`
   conservan YuNet + SFace, coincidencia con el usuario autenticado y presencia.
3. `attendance_service.register()` conserva sesión activa, duplicados, tolerancia
   y presente/tardanza. Su repositorio confirma la transacción antes de EmoScan.
4. Solo un resultado nuevo `success=true, status=REGISTERED` puede iniciar análisis.
   No se procesa en intentos fallidos, identidades diferentes ni asistencias duplicadas.
5. Con consentimiento específico vigente, el servicio copia en RAM el mismo
   fotograma ya recibido. No se captura ni se envía otra fotografía desde el navegador.
6. Un trabajador procesa la cola secuencialmente. Cada tarea utiliza un proceso
   hijo `spawn`, Haar para recortar un único rostro y `EmotionONNX`, con un hilo
   de cálculo ONNX. El reconocimiento de identidad del Monitor no se modifica.
7. La respuesta de asistencia vuelve sin esperar a FERPlus. La interfaz muestra
   asistencia confirmada y consulta el análisis opcional por separado.

Faltas de consentimiento/modelo/dependencias, excepciones, procesos bloqueados,
cola llena o vencimiento no revierten ni cambian la asistencia. No hay etiquetas
aleatorias ni clase predeterminada cuando falla la inferencia.

## Consentimiento y privacidad

El permiso biométrico de `rostros` no activa EmoScan. El consentimiento específico
se acepta mediante una casilla voluntaria sin marcar inicialmente y puede
revocarse sin impedir la asistencia. La API requiere el rol estudiante y JWT.

Solo se persisten los campos de `consentimientos_expresiones`: usuario, aceptación,
versión del texto, revisión aleatoria y fecha UTC de actualización. Cada cambio
renueva la revisión. No hay columnas de imágenes, expresiones ni puntuaciones.
La migración no toca las tablas faciales o de asistencia.

La cola, las copias de fotogramas y los resultados son temporales en memoria.
No se usan CSV, archivos de imagen, logs de puntuaciones, navegador localStorage
ni tablas de resultados. No se llama a `EmoScan.app.process_frame()`, que mantiene
registros para su interfaz independiente. No se inicia el servidor Flask.

El consentimiento se comprueba al admitir, antes de ejecutar, al publicar y al
consultar. Revocar elimina tareas/resultados locales y detiene el proceso activo
en el siguiente ciclo de supervisión. Las revisiones antiguas siguen invalidadas
aunque el estudiante vuelva a aceptar. La supervisión del límite del modelo y
la limpieza de RAM no dependen de esperar consultas a la base.

La consulta usa el usuario del JWT; no acepta un usuario_id del cliente. Las tareas
tienen identificadores opacos y otro usuario obtiene 404. Las respuestas de
resultados incluyen `Cache-Control: no-store`. No hay consultas de profesor/admin.
El navegador borra el resultado al caducar, revocar, ocultar o abandonar la página,
y avisa a otras pestañas del mismo origen cuando cambia el permiso. Esto no
puede impedir que una persona copie información que ya haya visto.

## Límites predeterminados

| Ajuste | Valor |
| --- | --- |
| `EMOSCAN_ENABLED` | `false` |
| `EMOSCAN_QUEUE_SIZE` | 4 tareas, incluyendo la activa |
| `EMOSCAN_JOB_TTL_SECONDS` | 10 segundos desde admisión, incluida espera e inicio |
| `EMOSCAN_RESULT_TTL_SECONDS` | 30 segundos desde finalización; admite valores >0 y <=30 |
| `EMOSCAN_MAX_RESULTS` | 32 entradas totales, incluyendo pendientes |
| `EMOSCAN_MODEL_PATH` | `integraciones/emoscan/emotion-ferplus-8.onnx`, ruta absoluta calculada |

Se admite una sola tarea activa/pendiente por usuario. Los fotogramas retenidos
deben ser BGR uint8 y de como máximo 1280 × 1280 píxeles equivalentes. El frontend
habitual utiliza 640 × 480. Un limpiador independiente elimina datos vencidos;
el supervisor termina el proceso hijo si vence su tarea o se revoca. Al cerrar
FastAPI se vacían los datos temporales y se detiene el trabajador.

## Activación local

Trabajar desde la raíz del repositorio, con las dependencias habituales del Monitor
instaladas. El archivo adicional incluye ONNX Runtime y Flask para conservar
la interfaz independiente y ejecutar su prueba de regresión:

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-emoscan.txt
```

Para un entorno nuevo, instalar también los requisitos existentes del Monitor.
Conservar una sola distribución de OpenCV, la que ya utiliza el proyecto.

Antes de habilitar EmoScan, ejecutar en una base de desarrollo la migración
`database/mysql/emoscan_consentimiento.sql` mediante el cliente SQL habitual.
Solo crea una tabla de metadatos de consentimiento. **No se ha ejecutado esta
migración contra la base real durante la implementación.**

En el `.env` local (no versionarlo), configurar:

```dotenv
EMOSCAN_ENABLED=true
EMOSCAN_QUEUE_SIZE=4
EMOSCAN_JOB_TTL_SECONDS=10
EMOSCAN_RESULT_TTL_SECONDS=30
EMOSCAN_MAX_RESULTS=32
```

Desde la raíz, iniciar con **un solo worker**:

```powershell
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

Servir el frontend con su mecanismo habitual y abrir
`frontend/estudiante/asistencia.html` con una sesión de estudiante. Esta página
conserva la URL de asistencia local existente en el puerto 8000; la API opcional
se deriva de esa misma URL. Leer y aceptar el consentimiento si se desea activar
el análisis. Sin aceptación la asistencia funciona igual.

Para servirlo en Windows sin Node, desde la raíz y en otra terminal:

```powershell
.\.venv312\Scripts\python.exe -m http.server 8001 --bind 127.0.0.1 --directory frontend
```

La versión publicada conserva Railway en `frontend/js/config.js`. Antes de
iniciar una sesión completamente local, sustituir esa URL solo en la copia de
desarrollo por `http://127.0.0.1:8000`; no publicar ese cambio local.
El backend carga `.env` desde la raíz con `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER`, `DB_PASSWORD` y claves JWT/Fernet propias. `DATABASE_URL` no sustituye
a esas variables. Definir `FACE_MODELS_DIR=models` para los modelos de identidad
incluidos; ver [MODELOS.md](MODELOS.md).

No iniciar `integraciones/emoscan/app.py` para esta integración: su interfaz
original se conserva como aplicación independiente, pero no participa en el flujo.

Si la tabla no existe o no se puede consultar, no se admite análisis. La pantalla
de consentimiento informa indisponibilidad; el registro de asistencia continúa.

## API nueva

| Método y ruta | Función |
| --- | --- |
| `GET /api/expressions/consent` | Texto vigente, versión, aceptación y disponibilidad |
| `PUT /api/expressions/consent` | `{ "accepted": true/false, "text_version": "emoscan-2026-10-25-v1" }` |
| `GET /api/expressions/jobs/{job_id}` | Estado/resultado propio, si no ha caducado y conserva el permiso |

Aceptar exige la versión actual; revocar también funciona desde una página con
versión antigua. No hay endpoint para enviar imágenes directamente a EmoScan.
La respuesta de un registro nuevo añade `expression_analysis`, con estados
`DISABLED`, `NO_CONSENT`, `BUSY`, `UNAVAILABLE` o `QUEUED` y `job_id`.
La consulta posterior puede devolver `QUEUED`, `RUNNING`, `READY`, `NO_SINGLE_FACE`
o `UNAVAILABLE`; tareas vencidas/revocadas/no propias devuelven 404.

## Verificación ejecutada

Python 3.12.10, `.venv312` existente de la raíz:

```powershell
.\.venv312\Scripts\python.exe integraciones\emoscan\descargar_imagen_prueba.py
.\.venv312\Scripts\python.exe -m pytest backend/tests/emoscan -q -p no:cacheprovider
```

Resultado: **29 pruebas aprobadas**. Una advertencia de deprecación de
Starlette/httpx no afecta a los resultados.

La suite utiliza usuarios ficticios, SQLite exclusivamente en memoria y un bloqueo
explícito de conexiones MySQL. No ejecuta los scripts antiguos de repositorio
que podrían escribir datos reales. Las identidades/presencia son dobles de prueba;
la foto pública verifica FERPlus, sin enrolarla como estudiante real.

Se verificaron aceptación/revocación/versiones, autenticación/roles, separación
entre usuarios, coincidencia del JPEG, registro antes del encolado, transacción
real en SQLite que sobrevive al fallo opcional, duplicados, presente/tardanza,
sesión inactiva, ausencia de consentimiento, cola llena, proceso bloqueado o
cerrado, modelo ausente, caducidad de imágenes/resultados y limpieza aun con
consulta de consentimiento lenta.
También se verifica que la interfaz Flask original responde correctamente con
el modelo cargado, bloqueando cualquier intento de abrir la cámara.

La fotografía pública `imagenes_prueba/astronauta.png` pasó por la cola y el
proceso reales: `READY`, clase `happy`, ocho puntuaciones que suman uno. No se
generaron nuevos JPG ni registros de estudiantes durante estas pruebas.
La fotografía no se sube al repositorio. Después de clonar, ejecutar primero el
preparador explícito indicado arriba: valida SHA-256 y conserva archivos existentes
si son iguales; rechaza sobrescribirlos si difieren. Su origen está documentado
en `imagenes_prueba/ORIGEN.md`.

`frontend/tests/emoscan.test.js` contiene pruebas JavaScript sin dependencias:

```powershell
node frontend/tests/emoscan.test.js
```

Se ejecutaron sus **14 comprobaciones en V8 mediante las herramientas**; Node
no está instalado en este equipo. Verifican aceptación explícita, revocación,
respuesta tardía descartada, borrado por caducidad/ocultación, texto estimado,
no-cache y confirmación de asistencia antes del análisis opcional. Son pruebas
con DOM y transporte simulados; no equivalen a probar el diseño en un navegador real.

Se comprobó además el arranque/importación de FastAPI con conexiones de base
bloqueadas: `/` devuelve 200 y consentimiento sin JWT devuelve 401. Se instalaron
en `.venv312` los requisitos base de pruebas y `joblib`, ya declarado por el Monitor,
que faltaba para importar la aplicación completa.

## Limitaciones

- La cola y sus resultados son locales al proceso: usar un solo worker/réplica.
  Reiniciar o recargar el servidor descarta tareas/resultados; el consentimiento
  persiste. No se ofrece persistencia ni coordinación entre réplicas.
- Se carga FERPlus por tarea para aislar y poder finalizar un modelo bloqueado.
  Hay coste de arranque; tareas pueden caducar en equipos lentos.
- Haar solo clasifica cuando encuentra un rostro adecuado. Puede omitir rostros
  pequeños/girados aunque SFace haya identificado correctamente a la persona;
  esto no afecta a la asistencia.
- Se mantiene el detector de presencia existente basado en diferencia de frames,
  incluido su estado global. No se ha reforzado su detección contra suplantación
  ni su aislamiento entre usuarios concurrentes en esta integración.
- La consulta de consentimiento después del commit puede añadir latencia de base
  de datos; nunca se espera la inferencia del modelo. Si la base no responde,
  también aplican los tiempos de conexión del Monitor.
- No se probó la cámara física ni el flujo visual completo en un navegador.
  Tampoco se aplicó/probó la migración en un servidor MySQL real.
- La puntuación softmax no demuestra emociones internas ni precisión general.
  No se usa para notas, sanciones, atención ni predicciones académicas.

Se conservaron `segmentacion`, Parte 3, YuNet + SFace, sus umbrales, embeddings,
reglas de asistencia y la interfaz web original de EmoScan. La publicación requiere
autorización explícita; los scripts no ejecutan commits, push ni migraciones.
