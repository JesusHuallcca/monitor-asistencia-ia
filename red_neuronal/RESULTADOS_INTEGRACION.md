> Registro histórico de una iteración anterior. La entrega vigente está en RESULTADOS_PUBLICACION.md e INTEGRACION_MYSQL.md. MySQL continúa pendiente; los asistentes locales descritos aquí fueron retirados.

# Resultados de la integración académica de Parte 6

Verificación local: 29 de octubre de 2026. Worktree `monitor-asistencia-parte6`, rama `parte-6-red-neuronal`. Sin commits, pushes ni merges.

## Pruebas efectivamente ejecutadas

- Suite final: **58 aprobadas**, una advertencia de deprecación AnyIO/Starlette. Incluye preparación original, escalador, inferencia real, JWT, autorización por curso, acceso cruzado rechazado, fechas futuras, duplicados, historial insuficiente, identidad activa y rechazo de producción.
- Chrome contra FastAPI + SQLAlchemy en **SQLite RAM**, JWT firmado y modelo Keras real: **1366×768, 1920×1080, 390×844 aprobadas**. Login, selección, historial, nueve variables, predicción, bloqueo por datos insuficientes y regreso a demostración. Sin desbordamientos ni errores JavaScript.
- Regresión del servidor sintético original en 8006: las tres resoluciones aprobadas, curvas/zoom/predicción y estados de error conservados.
- Servidor integrado final en 8007: MySQL deshabilitado cuando no está configurado; demostración y predicción sintéticas aprobadas; cookie sintética rechazada para leer datos académicos (401).
- Asistente PowerShell: análisis sintáctico aprobado; no se introdujeron credenciales reales ni se ejecutó su conexión.
- `check_mysql`: **NO EJECUTADA la conexión real**. La protección devolvió que falta configuración local explícita. No se comprobó el contenido de tablas MySQL con registros reales ni se afirma que estas pruebas estén aprobadas.

- Integridad: 78 archivos protegidos conservan su SHA-256, incluidos pesos Keras, StandardScaler, logística, dataset sintético, métricas y predicciones originales, Segmentación IA, EmoScan y modelos anteriores.
- Las cuatro ramas existentes y los tres stash conservan sus hashes. No se ha creado `.env` ni añadido credenciales.

## Archivos de esta integración

Nuevos:

- `backend/app/api/parte6_system.py`
- `backend/app/services/parte6_service.py`
- `backend/app/services/parte6_database.py`
- `red_neuronal/system_features.py`
- `frontend/js/parte6-system.js`
- `red_neuronal/check_mysql.py` y `configure_dev.ps1`
- `red_neuronal/requirements-integracion.txt` y `requirements-integracion-lock.txt`
- `red_neuronal/tests/conftest.py`, `test_system.py`, `system_fixture_app.py`
- `red_neuronal/browser_system_check.py`, `run_system_ui_tests.py`
- `red_neuronal/INTEGRACION_MYSQL.md` y este informe.

Modificados dentro de Parte 6:

- `backend/app/parte6.py`: aplicación integrada de solo lectura, sin importar main.
- `red_neuronal/predict.py`: inferencia sobre nueve variables y validación de arquitectura/scaler; pesos intactos.
- `red_neuronal/api.py`: instancia del modelo protegida con lock y caché.
- `frontend/profesor/red-neuronal.html`, `frontend/css/red-neuronal.css`, `frontend/js/red-neuronal.js`: modos y separación del origen de los resultados.
- `frontend/js/panel-comun.js`: un enlace a Parte 6 en el menú del profesor.
- `red_neuronal/README.md`: remite a la integración vigente.

## Capturas

En `.cache/integracion/browser/`: escritorio y móvil, historial suficiente e insuficiente. Todas están marcadas **SQLITE EN MEMORIA, NO MYSQL**. No contienen estudiantes reales.

En `.cache/integracion/`: `servidor-final-sin-credenciales.png` y `servidor-final-demostracion.png` muestran el servidor efectivo de 8007. Los archivos cache son locales/ignorados.

## Inicio y pendientes

Dashboard: http://127.0.0.1:8007/profesor/red-neuronal.html. La demostración puede iniciarse sin MySQL. Para la base de desarrollo, seguir `INTEGRACION_MYSQL.md` y ejecutar el asistente en tu propia terminal; `-Port 8009` permite conservar los servidores existentes.

Pendiente: credenciales válidas y registros autorizados de la base local existente, comprobación real de conexión/tablas/columnas/zona horaria, acceso del profesor real y casos de historial suficiente/insuficiente en MySQL. No hay evaluación etiquetada de rendimiento real ni calibración validada.

El esquema no permite reconstruir versiones históricas completas: se limita la inferencia a la próxima sesión futura con corte actual. Las notas reales son evaluaciones, frente a notas simuladas por sesión: se conserva la media aritmética disponible, se advierte el cambio de dominio y no se inventa una correspondencia entre evaluaciones y sesiones.
