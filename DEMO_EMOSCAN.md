# DEMO EMOSCAN — Guía de Ejecución y Demostración

Documento de la Parte 4 (OpenCV + Visión Computacional) del Plan de Integración ML/DL.

---

## 1. Arquitectura y Tecnologías
- **Modelo:** Red neuronal FERPlus en formato ONNX (`emotion-ferplus-8.onnx`), optimizada para inferencia rápida sin requerir TensorFlow.
- **Visión Computacional:** OpenCV (`haarcascade_frontalface_default.xml`) para encuadre y recorte facial en escala de grises a 64x64 píxeles.
- **Clasificación de 8 Expresiones:** Neutral, Felicidad (Happy), Sorpresa (Surprise), Tristeza (Sad), Ira (Angry), Asco (Disgust), Miedo (Fear), Desprecio (Contempt).
- **Persistencia en la Nube:** Base de datos MySQL en Aiven Cloud (`emoscan_historial`), registrando las emociones asociadas a cada `estudiante_id`.

---

## 2. Cómo ejecutar el sistema en local

### Paso 1: Levantar el Backend (FastAPI :8000)
```powershell
cd monitor-asistencia-ia
$env:PYTHONPATH = "$PWD;$PWD\backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### Paso 2: Levantar el Frontend (Servidor Web :8001)
En otra terminal PowerShell:
```powershell
cd monitor-asistencia-ia
.\.venv\Scripts\Activate.ps1
python -m http.server 8001 --directory frontend
```

---

## 3. Pasos para Probar la Detección Emocional en Vivo

1. **Abrir en el navegador:**
   👉 `http://127.0.0.1:8001/login.html`

2. **Iniciar sesión como estudiante de prueba:**
   - **Usuario:** `alumno1`
   - **Contraseña:** `Senati2026!`

3. **Acceder al módulo EmoScan:**
   - En el menú lateral izquierdo, haz clic en **EmoScan**.
   - O ingresa directamente a: `http://127.0.0.1:8001/estudiante/emoscan.html`.

4. **Aceptar Consentimiento y Activar Cámara:**
   - Lee el consentimiento informado y pulsa **Aceptar**.
   - Haz clic en **Activar cámara** y concede el permiso en el navegador.

5. **Analizar Expresión:**
   - Encuadra tu rostro en la pantalla y haz clic en **Analizar expresión**.
   - El sistema capturará el fotograma, procesará la expresión con el modelo ONNX y te mostrará la emoción predominante junto con los porcentajes.
   - En ese mismo instante, el resultado queda guardado en la base de datos de Aiven MySQL vinculado a tu `estudiante_id`.

---

## 4. Consulta del Historial Emocional por el Profesor

1. **Cerrar sesión e iniciar como profesor:**
   - **Usuario:** `prof.ramirez`
   - **Contraseña:** `Senati2026!`

2. **Consultar API de historial por `estudiante_id`:**
   - Endpoint: `GET /api/emoscan-personal/estudiante/1/historial`
   - Endpoint: `GET /api/emoscan-personal/estudiante/1/resumen`
   - Permite al docente o administrador auditar el estado emocional de cada alumno.
