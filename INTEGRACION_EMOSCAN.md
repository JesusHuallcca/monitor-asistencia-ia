# Monitor de Asistencia IA + EmoScan

La integración reutiliza el JPEG de `frontend/components/camera.js`. Después de
identificar al usuario con YuNet + SFace y confirmar la asistencia, FERPlus puede
estimar la expresión en un proceso opcional, solo con consentimiento específico.
No abre otra cámara ni persiste imágenes o puntuaciones de estudiantes. Un fallo
del análisis no revierte la asistencia.

Guía completa: [INTEGRACION_ASISTENCIA.md](integraciones/emoscan/INTEGRACION_ASISTENCIA.md).
Modelos y checksums: [MODELOS.md](integraciones/emoscan/MODELOS.md).

## Arranque local (PowerShell, desde la raíz)

Configurar un `.env` local a partir de `.env.example`, con una base de desarrollo
aislada y claves propias. Se utilizan `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER` y `DB_PASSWORD`; no `DATABASE_URL`. Aplicar explícitamente la
migración de consentimiento en desarrollo antes de habilitar EmoScan. No se
ejecutan migraciones automáticamente.

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-emoscan.txt
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

En otra terminal:

```powershell
.\.venv312\Scripts\python.exe -m http.server 8001 --bind 127.0.0.1 --directory frontend
```

La versión publicada conserva Railway en `frontend/js/config.js`. Para una
prueba local, sustituir esa URL solo en la copia local por
`http://127.0.0.1:8000`; no publicar esa sustitución. La página de asistencia
conserva sus URLs locales existentes en el puerto 8000. Usar `FACE_MODELS_DIR=models`
para los modelos de identidad incluidos. No iniciar Flask para esta integración.

## Preparar y ejecutar las pruebas

La fotografía pública de NASA no se versiona. Prepararla explícitamente:

```powershell
.\.venv312\Scripts\python.exe integraciones/emoscan/descargar_imagen_prueba.py
.\.venv312\Scripts\python.exe -B -m pytest backend/tests/emoscan -q -p no:cacheprovider
node frontend/tests/emoscan.test.js
```

Las pruebas usan datos ficticios y SQLite en memoria; bloquean conexiones MySQL.
La inferencia real requiere el modelo y la fotografía preparada. La regresión de
la interfaz original requiere Flask, incluido en `requirements-emoscan.txt`.
Para un entorno nuevo, instalar también los requisitos habituales del Monitor y
`requirements-base.txt` (incluye pytest); conservar una sola distribución OpenCV.

Para una marcación en navegador hacen falta una cuenta de prueba con rostro
autorizado, sesión activa, cámara operativa y consentimiento voluntario.
`GET /api/expressions/consent` exige JWT y rol estudiante e informa `enabled`
y `accepted`. Las expresiones estimadas no prueban emociones internas ni atención.
