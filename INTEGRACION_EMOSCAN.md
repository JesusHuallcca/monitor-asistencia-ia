# Integración EmoScan ↔ Monitor Inteligente de Asistencia con IA

Documento de la fusión (Fase 1) según el manual técnico de integración.

## Objetivo

Permitir que un **estudiante** autenticado acceda al análisis de expresiones faciales (EmoScan) desde el menú del Monitor, sin reescribir Flask dentro de FastAPI y sin alterar asistencia facial, predicciones, chatbot ni MySQL.

## Arquitectura

| Servicio | Tecnología | Puerto local | Rol |
|----------|------------|--------------|-----|
| Monitor (API) | FastAPI | 8000 | Backend principal, JWT, MySQL |
| Monitor (frontend) | HTML/CSS/JS | 8001 | Interfaz y menú del estudiante |
| EmoScan | Flask | 5000 | Detección emocional + CSV |

Flujo:

1. Estudiante inicia sesión en el Monitor.
2. En el menú (solo rol `estudiante`) aparece **Análisis emocional**.
3. Se abre `frontend/estudiante/emoscan.html`.
4. Esa página embebe EmoScan con un **iframe** (`http://127.0.0.1:5000` en desarrollo).
5. Si EmoScan no responde, se muestra un mensaje de error y el Monitor sigue operativo.

## Archivos de la integración

### Nuevos o específicos de la fusión

| Archivo | Descripción |
|---------|-------------|
| `monitor-asistencia-ia/frontend/estudiante/emoscan.html` | Página de integración (iframe, carga, error, volver) |
| `monitor-asistencia-ia/frontend/js/panel-comun.js` | Menú con opción «Análisis emocional» solo para estudiante |
| `EmoScan - copia (2)/app.py` | Cabeceras para iframe + control básico de acceso por Referer |
| `INTEGRACION_EMOSCAN.md` | Este documento |

### Qué no se modificó (a propósito)

- Lógica de asistencia facial del Monitor
- Modelo de predicciones / regresión
- Chatbot
- Esquema MySQL del Monitor
- Almacenamiento de emociones: sigue en CSV de EmoScan (`logs/`)

## Cómo ejecutar en local

### 1. Backend Monitor

```powershell
cd monitor-asistencia-ia
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD;$PWD\backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 2. Frontend Monitor

```powershell
cd monitor-asistencia-ia\frontend
python -m http.server 8001
```

Abrir: http://localhost:8001/login.html

### 3. EmoScan

```powershell
cd "EmoScan - copia (2)"
# activar su venv si existe
python app.py
```

Abrir (solo para prueba directa): http://127.0.0.1:5000

## Uso

1. Iniciar sesión como **estudiante**.
2. En el menú lateral: **Análisis emocional**.
3. Esperar la carga del módulo; si falla, usar **Reintentar conexión**.
4. **Volver al dashboard** con el botón de la página o el menú.

## Limitaciones conocidas (Fase 1)

1. **Cámara del servidor:** EmoScan usa `cv2.VideoCapture` (cámara de la máquina donde corre Flask), no necesariamente la del navegador del estudiante.
2. **URL del iframe:** En `emoscan.html` está fijada a `http://127.0.0.1:5000`. Cambiar la variable `EMOSCAN_URL` para otro entorno.
3. **Seguridad:** El bloqueo por `Referer` en Flask es una medida básica de desarrollo. No sustituye un proxy inverso con validación JWT. Documentado como pendiente para producción.
4. **Datos emocionales:** No se guardan en MySQL; solo CSV en la carpeta `logs/` de EmoScan.
5. **Producción:** Hace falta HTTPS, proxy (p. ej. `/emoscan/` → Flask) y no publicar el puerto 5000 a Internet.

## Criterios de aceptación cubiertos en esta entrega

- [x] Opción de menú solo para estudiante
- [x] Página de integración dentro del Monitor
- [x] iframe con `allow="camera"`
- [x] Indicador de carga
- [x] Mensaje de error si EmoScan no está disponible
- [x] Botón volver al dashboard
- [x] Servicios separados
- [x] Documentación de la integración y limitaciones
- [ ] Proxy + JWT en producción (pendiente)
- [ ] Cámara del navegador / getUserMedia (fase posterior)

## Producción (notas)

- Cambiar `EMOSCAN_URL` en `emoscan.html` a la URL pública de EmoScan (o ruta del proxy).
- Configurar proxy inverso, por ejemplo:
  - `/` → frontend Monitor
  - `/api/` → FastAPI :8000
  - `/emoscan/` → Flask :5000
- No exponer `logs/` como archivos estáticos públicos.
- Sustituir el control por Referer por autenticación real en el borde (proxy).
