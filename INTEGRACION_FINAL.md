# Integración local: Segmentación IA y EmoScan personal

Worktree independiente: `monitor-asistencia-integracion-segmentacion`.
Rama nueva: `integracion-segmentacion-ia`. Sin commits, merges ni pushes.

## Procedencia y separación

- Parte 3 se copia de la versión definitiva sin confirmar de
  `monitor-asistencia-parte3`: cuatro variables, expresiones exclusivamente sintéticas,
  StandardScaler, K-Means, silueta y PCA. No se usa la implementación antigua del HEAD.
- EmoScan y su integración opcional con asistencia se copian del commit `542698f`
  de `integracion-emoscan`. No se cambian sus archivos en el worktree de origen.
- El reconocimiento YuNet/SFace, el login y las funciones administrativas se conservan.
  No se añade análisis de expresiones al login.
- El consentimiento personal es independiente del consentimiento posterior a asistencia.
  Ambas modalidades reutilizan `ExpressionService`, el worker y el mismo archivo FERPlus ONNX;
  tienen colas y revisiones de consentimiento separadas. Un permiso no autoriza el otro.
- No se ejecutan migraciones automáticamente. Las pruebas bloquean conexiones MySQL.
  Las imágenes y las puntuaciones permanecen en RAM y caducan; solo se persiste
  la aceptación/revocación, versión, revisión y fecha del consentimiento por usuario.

## Iniciar en desarrollo

Usar una base MySQL **de desarrollo**, con el esquema habitual del Monitor y cuentas
de prueba de profesor y estudiante. No apuntar esta copia a una base de producción.
El inicio de sesión normal necesita esa base y sus usuarios; las pantallas no incluyen
credenciales ni un mecanismo para saltarse la autenticación.

Desde la raíz del worktree de integración, crear un entorno nuevo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-integracion.txt
```

Preparar un `.env` local usando `.env.example`. No copiar secretos de otros worktrees
ni añadir ese archivo a Git. Configurar `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `JWT_SECRET_KEY`, y los modelos de identidad de acuerdo con la instalación
existente. Para EmoScan habilitado:

```dotenv
EMOSCAN_ENABLED=true
```

La ruta FERPlus predeterminada es `integraciones/emoscan/emotion-ferplus-8.onnx`.
Para el reconocimiento facial, `FACE_MODELS_DIR` debe señalar la carpeta que contenga
YuNet y SFace de la instalación. No se duplican ni cambian los modelos de identidad.

Revisar y aplicar explícitamente, **solo en la base de desarrollo**, los scripts de
consentimiento necesarios:

- `database/mysql/emoscan_consentimiento.sql`: funcionalidad opcional de asistencia existente.
- `database/mysql/emoscan_personal_consentimiento.sql`: permiso de la nueva sección personal.

No ejecutar estos scripts en producción. La integración no ha aplicado ninguno a MySQL.
Si falta una tabla de consentimiento, EmoScan devuelve un mensaje de indisponibilidad;
la asistencia conserva su flujo y el análisis opcional no puede revertir una marcación.

Iniciar backend desde la raíz, para que se pueda importar `segmentacion/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

En otra terminal, en la misma raíz:

```powershell
.\.venv\Scripts\python.exe -m http.server 8001 --bind 127.0.0.1 --directory frontend
```

En localhost, la configuración del frontend dirige las peticiones al backend local
del puerto 8000. En los dominios publicados conserva la URL existente de Railway.
No se ha publicado esta integración. Para despliegues futuros hay que configurar
la URL y CORS adecuados. La cámara funciona en localhost o HTTPS.

## Probar desde el navegador

1. Abrir `http://127.0.0.1:8001/login.html` e iniciar sesión como profesor de prueba.
2. Elegir **Segmentación IA**, o abrir
   `http://127.0.0.1:8001/profesor/segmentacion.html`.
3. Pulsar **Ver demostración**: el servidor calcula los resultados de los 150 perfiles
   definitivos de Parte 3 sin subir archivos.
4. Para probar la carga, descargar el CSV sintético de ejemplo desde la pantalla,
   seleccionarlo o arrastrarlo al apartado de carga, y pulsar **Procesar segmentación**.
   Se informa nombre, tamaño, registros detectados y estado de validación.
5. Explorar las pestañas Resumen, Explorar clusters, Comparar variables y Evaluación K-Means. Cada cluster tiene
   su color; el selector filtra los grupos y los puntos muestran valores al pasar el cursor.
   Las curvas de inercia y silueta muestran los resultados calculados para cada K.
6. **Descargar resultados CSV** genera una descarga local con todos los perfiles,
   cuatro variables, procedencia, cluster y coordenadas PCA. No crea archivos en el servidor.
7. Cerrar sesión e ingresar como estudiante de prueba; elegir **EmoScan**, o abrir
   `http://127.0.0.1:8001/estudiante/emoscan.html`.
8. Leer y aceptar el consentimiento personal. Pulsar **Activar cámara**, permitir
   el acceso en el navegador y encuadrar un rostro. **Analizar expresión** envía
   un único JPEG al backend. **Repetir análisis** vuelve a analizar voluntariamente;
   ninguno de esos botones registra asistencia.
9. **Retirar consentimiento** detiene la cámara, limpia resultados y revoca el permiso
   en el servidor. **Desactivar cámara**, ocultar la pestaña o salir también detiene
   las pistas y descarta los resultados. La consulta solo permite el usuario propietario.
10. El administrador conserva su panel. Los endpoints exigen rol, además de la protección
    de las pantallas; no basta cambiar la URL o el menú para obtener acceso.

## Contrato CSV y API

Entrada de sesiones, una fila por usuario/curso/sesión, UTF-8 y separador coma:

```csv
usuario_id,sesion,estado,promedio_notas,origen_datos
1,1,PRESENTE,15.5,sintetico
```

El ejemplo de una fila solo ilustra el formato; para procesar hacen falta entre
4 y 500 perfiles y al menos tres perfiles numéricos distintos. Se admite `sesion_id`
en lugar de `sesion`, exactamente una de las dos. `curso_id` es opcional.
Los identificadores son enteros positivos de hasta 15 dígitos. Notas finitas 0–20,
estados PRESENTE/TARDANZA/AUSENTE, sin duplicados ni faltantes obligatorios.
La lista de columnas auxiliares académicas admitidas está en `segmentacion_service.py`.
Se rechazan columnas desconocidas, faciales o de expresiones de entrada.
Máximo 2 MiB, 10000 filas y 128 caracteres por campo.

Cada fila debe declarar `origen_datos=sintetico`. La declaración es un requisito,
no una certificación automática de la procedencia: usar únicamente simulaciones
propias o el ejemplo distribuido. Las expresiones se generan con el procedimiento
definitivo: conteo binomial de 40 muestras, probabilidad uniforme 0.05–0.95 y semilla 2026,
independiente de notas y asistencia. No se aceptan expresiones reales.

K se calcula por máxima silueta entre K≥3, evaluando 2…8 cuando la muestra lo permite;
se informan el mejor K global y el codo por separado. No se fija K=3 para archivos nuevos.
PCA solo visualiza el ajuste realizado sobre las cuatro variables estandarizadas.

| Ruta | Método | Permiso y contenido |
|---|---|---|
| `/api/segmentacion/demo` | GET | Profesor; calcula la demostración incluida |
| `/api/segmentacion/procesar` | POST | Profesor; cuerpo CSV, `Content-Type: text/csv`, `X-CSV-Filename: ejemplo.csv` |
| `/api/emoscan-personal/consent` | GET / PUT | Estudiante; estado y aceptación/revocación personal versionada |
| `/api/emoscan-personal/analizar` | POST | Estudiante con consentimiento; cuerpo `image/jpeg`, máximo 300 KiB y 1280×1280 |
| `/api/emoscan-personal/jobs/{id}` | GET | Estudiante propietario y permiso vigente; resultado temporal |
| `/api/emoscan-personal/jobs` | DELETE | Estudiante; descarta sus propios trabajos personales |

Todas requieren JWT Bearer válido y usuario activo. La respuesta de segmentación
incluye puntos, medias por cluster, métricas, evaluación de K y CSV generado en memoria.
El navegador descarga este CSV desde un Blob sin rutas de archivo controladas por el usuario.
Una petición simultánea de K-Means puede devolver 503 con `Retry-After`; el profesor
puede reintentar. Se acota el procesamiento por tamaño, filas, perfiles y un ajuste a la vez.

## Archivos y comprobaciones

Nuevos: API y servicio `segmentacion`, API/servicio/consentimiento `emoscan_personal`,
las dos pantallas, sus JS/CSS, CSV sintético de ejemplo, SQL de consentimiento personal,
pruebas `backend/tests/integracion_final/`, prueba de navegador
`frontend/tests/integracion-final.test.cjs`, requisitos y esta guía.

Modificados para conectar la integración: `backend/app/main.py` (registro y cierre de
servicios), `frontend/js/panel-comun.js` (menús según rol), `frontend/js/config.js`
(backend local), `frontend/package.json` (prueba de navegador).
Los archivos de EmoScan y asistencia importados de `542698f` se conservan.
El directorio `segmentacion/` reproduce la versión definitiva de cuatro variables.

Consultar `RESULTADOS_INTEGRACION.md` para las pruebas realmente ejecutadas y sus límites.

Para repetir las pruebas Python en un entorno con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -B -m unittest discover -s segmentacion -t . -v
.\.venv\Scripts\python.exe -B -m pytest backend/tests/integracion_final backend/tests/emoscan -q -p no:cacheprovider
node frontend/tests/emoscan.test.js
```

La regresión real de FERPlus usa una imagen pública de NASA, excluida de Git.
Prepararla con `python integraciones/emoscan/descargar_imagen_prueba.py` si falta.
Las pruebas de navegador necesitan Playwright y Chrome/Chromium y una fixture JSON
calculada con el algoritmo, no una tabla de resultados inventados. Desde la raíz:

```powershell
$env:PYTHONPATH = "$PWD\backend;$PWD"
New-Item -ItemType Directory -Force segmentacion/.cache
python -B frontend/tests/preparar_segmentacion.py
cd frontend
npm install
npx playwright install chromium
npm run test:integration
```

El test levanta y cierra su propio servidor estático. Usa el JSON calculado para
K-Means y dobles de prueba para autenticación, cámara e inferencia personal;
las rutas autenticadas reales se comprueban por separado en Python.

La guía actual de la página única y sus verificaciones está en [DASHBOARD_SEGMENTACION.md](DASHBOARD_SEGMENTACION.md).

La ampliación de categorías es opcional y exclusivamente sintética. Consultar
[CATEGORIAS_SINTETICAS.md](CATEGORIAS_SINTETICAS.md). El frontend mantiene compatibilidad
con CSV clásicos; la demostración genera un desglose adicional que no altera K-Means.