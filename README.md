# Monitor Inteligente de Asistencia con IA

Sistema de asistencia académica con:

* FastAPI + SQLAlchemy
* MySQL/MariaDB
* JWT + roles
* Reconocimiento facial
* Detección facial y liveness
* Machine Learning para predicción de asistencia
* Chatbot conectado a datos reales
* Frontend web en HTML/CSS/JavaScript

---

# 1. ¿QUÉ NECESITO DESCARGAR?

Antes de clonar el proyecto, instalar:

### 1. Git

Para clonar y actualizar el repositorio.

### 2. Python 3.10

Se recomienda Python 3.10 para mantener compatibilidad con el entorno utilizado por el proyecto.

### 3. XAMPP

Se utiliza para ejecutar:

* MySQL/MariaDB
* Base de datos del sistema

### 4. Navegador

Chrome, Edge o Firefox.

## Frontend

El frontend actual es estático, por lo que **no necesita Node.js ni Angular CLI para ejecutarse**.

Se levanta mediante:

```powershell
python -m http.server
```

---

# 2. CLONAR EL PROYECTO

Clonar la rama actual:

```powershell
git clone -b feature/rouss-asistencia-ia https://github.com/JesusHuallcca/monitor-asistencia-ia.git
```

Entrar:

```powershell
cd monitor-asistencia-ia
```

---

# 3. CREAR EL ENTORNO VIRTUAL

Desde la raíz del proyecto:

```powershell
python -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

y nuevamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Debe aparecer:

```text
(.venv)
```

---

# 4. INSTALAR DEPENDENCIAS

Actualizar pip:

```powershell
python -m pip install --upgrade pip
```

Instalar dependencias generales:

```powershell
pip install -r requirements.txt
```

Instalar Machine Learning:

```powershell
pip install -r requirements-ml.txt
```

Instalar chatbot:

```powershell
pip install -r requirements-chatbot.txt
```

## Dependencias principales

El proyecto utiliza, entre otras:

```text
FastAPI
Uvicorn
SQLAlchemy
PyMySQL
python-dotenv
pydantic
pydantic-settings
python-jose
passlib
pandas
numpy
scikit-learn
joblib
OpenCV
TensorFlow
```

El reconocimiento facial puede utilizar además las bibliotecas/modelos que estén definidos en la configuración actual del módulo facial.

---

# 5. RECONOCIMIENTO FACIAL / OPENCV / MODELOS

El módulo facial utiliza OpenCV y modelos de IA para detección/reconocimiento/liveness.

## IMPORTANTE

Antes de ejecutar el sistema hay que verificar que los modelos faciales requeridos existan en la carpeta indicada por el proyecto.

Revisar:

```text
ai/
```

y:

```text
models/
```

También revisar las variables:

```env
FACE_MODEL_PATH=
FACE_THRESHOLD=
```

en `.env`.

### YuNet

Si la versión del módulo facial utiliza **OpenCV YuNet**, debe existir el archivo ONNX de detección facial requerido por esa implementación.

Por ejemplo, un proyecto puede utilizar un archivo similar a:

```text
face_detection_yunet_2023mar.onnx
```

El archivo debe colocarse exactamente en la ruta que espere el código del módulo facial.

**No cambiar el nombre ni la ruta del modelo sin revisar primero el código de detección.**

---

# 6. MODELO DE MACHINE LEARNING

El modelo de predicción de asistencia ya está incluido en el repositorio.

No es necesario descargarlo manualmente.

Se encuentra en:

```text
models/
├── asistencia_logreg.joblib
├── coeficientes.json
└── metricas_modelo.json
```

El archivo principal es:

```text
models/asistencia_logreg.joblib
```

El modelo utilizado actualmente es:

```text
LogisticRegression
```

Variables utilizadas:

```text
asistencia_ratio_30d
asistencias_consecutivas
ausencias_consecutivas
dia_semana
hora_inicio_clase
es_inicio_ciclo
promedio_notas
tardanzas_ratio
```

## Comprobar que el modelo funciona

Con `.venv` activo:

```powershell
python -c "import joblib; m=joblib.load('models/asistencia_logreg.joblib'); print(type(m)); print('MODELO OK')"
```

También:

```powershell
python -c "import sklearn, pandas, numpy, joblib; print('ML OK'); print('scikit-learn:', sklearn.__version__)"
```

---

# 7. BASE DE DATOS

El sistema utiliza MySQL/MariaDB.

La base de datos debe estar encendida antes de iniciar el backend.

## XAMPP

Abrir XAMPP y encender:

```text
MySQL
```

El puerto utilizado normalmente es:

```text
3306
```

---

# 8. CREAR LA BASE DE DATOS

Ejemplo:

```sql
CREATE DATABASE monitor_ia;
```

Después ejecutar los scripts SQL del proyecto ubicados en:

```text
database/mysql/
```

Los scripts deben crear las tablas necesarias para:

* usuarios
* profesores
* estudiantes
* cursos
* matrículas
* sesiones
* asistencias
* evaluaciones
* notas
* predicciones
* métricas
* chatbot

## IMPORTANTE

La base de datos local **no se clona con Git**.

Git solamente descarga los archivos del proyecto.

Por eso, en una PC nueva se debe:

1. instalar MySQL/MariaDB
2. crear la base de datos
3. ejecutar los scripts SQL
4. configurar el `.env`

---

# 9. ARCHIVO .ENV

El `.env` es local.

**No debe subirse a GitHub.**

Crear:

```text
.env
```

Ejemplo:

```env
APP_ENV=development

SECRET_KEY=CAMBIAR_EN_LOCAL

DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/monitor_ia

JWT_EXPIRE_MINUTES=60

APP_TIMEZONE=America/Lima

MODEL_PATH=models/asistencia_logreg.joblib

FACE_MODEL_PATH=ai/models/face_model/

FACE_THRESHOLD=0.60
```

## DATABASE_URL

Cambiar:

```text
root
password
monitor_ia
```

por los datos reales de la instalación local.

Ejemplo si MySQL no tiene contraseña:

```env
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/monitor_ia
```

---

# 10. CLAVE SECRETA JWT

Cada instalación local debe tener su propia `SECRET_KEY`.

Generar una nueva:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiar el resultado y colocarlo en:

```env
SECRET_KEY=PEGA_AQUI_LA_CLAVE_GENERADA
```

Ejemplo:

```env
SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## IMPORTANTE

Nunca subir a GitHub:

```text
SECRET_KEY real
password de MySQL
tokens JWT
claves API
.env
```

---

# 11. LEVANTAR EL BACKEND

Abrir una terminal.

Desde la raíz:

```powershell
cd monitor-asistencia-ia
```

Activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Configurar `PYTHONPATH`:

```powershell
$env:PYTHONPATH="$PWD\backend;$PWD"
```

Iniciar FastAPI:

```powershell
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

Health:

```text
http://127.0.0.1:8000/api/health
```

Debe aparecer que el backend está funcionando y que la base de datos está conectada.

---

# 12. LEVANTAR EL FRONTEND

Abrir otra terminal.

Entrar al proyecto:

```powershell
cd monitor-asistencia-ia
```

Levantar el servidor:

```powershell
python -m http.server 8001 --directory frontend
```

Frontend:

```text
http://127.0.0.1:8001
```

## IMPORTANTE

El frontend utiliza:

```text
http://127.0.0.1:8000
```

para comunicarse con FastAPI.

La configuración está en:

```text
frontend/js/config.js
```

Ejemplo:

```javascript
const API_URL = "http://127.0.0.1:8000";
```

---

# 13. ORDEN CORRECTO PARA ARRANCAR TODO

Cada vez que se quiera ejecutar el proyecto:

## Terminal 1 — XAMPP

Encender:

```text
MySQL
```

## Terminal 2 — Backend

```powershell
cd monitor-asistencia-ia
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\backend;$PWD"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Terminal 3 — Frontend

```powershell
cd monitor-asistencia-ia
python -m http.server 8001 --directory frontend
```

Abrir:

```text
http://127.0.0.1:8001
```

---

# 14. LOGIN

El sistema utiliza:

```text
JWT
```

para autenticar al usuario.

Flujo:

```text
Login
  ↓
Backend valida usuario
  ↓
JWT
  ↓
Frontend guarda sesión
  ↓
Requests protegidos con Authorization
```

Roles:

```text
ADMIN
PROFESOR
ESTUDIANTE
```

Los permisos se validan en el backend.

---

# 15. PRUEBA RÁPIDA DE LOGIN

Swagger:

```text
http://127.0.0.1:8000/docs
```

Buscar:

```text
POST /api/auth/login
```

Ejemplo:

```json
{
  "identificador": "Alumno1",
  "password": "TU_PASSWORD",
  "recordarme": false
}
```

El backend debe devolver un JWT.

**No compartir públicamente ese token.**

---

# 16. ENDPOINTS PRINCIPALES

### Usuario autenticado

```text
GET /api/users/me
```

### Asistencia

```text
GET /api/attendance/today
```

### Asistencia de estudiante

```text
GET /api/attendance/student/{id}
```

### Analítica

```text
GET /api/analytics/course/{id}
```

### Predicción ML

```text
GET /api/predictions/student/{id}
```

### Chatbot

```text
POST /api/chatbot/message
```

---

# 17. CHATBOT

El chatbot funciona con:

```text
Pregunta
   ↓
Detección de intención
   ↓
Consulta permitida
   ↓
Base de datos / ML
   ↓
Respuesta
```

No se ejecuta SQL escrito directamente por el usuario.

Ejemplos:

```text
¿Cuál es mi porcentaje de asistencia?
```

```text
¿Cuál es mi próxima clase?
```

```text
¿Cuál es mi riesgo de faltar?
```

El riesgo utiliza el modelo ML real.

---

# 18. MACHINE LEARNING + CHATBOT

El flujo de predicción es:

```text
Estudiante
   ↓
Historial real
   ↓
Feature engineering
   ↓
LogisticRegression
   ↓
Probabilidad
   ↓
Chatbot
   ↓
Frontend
```

Ejemplo de respuesta:

```text
Probabilidad estimada de asistir: 71.9%
Riesgo estimado de faltar: 28.1%
Predicción: Asistirá
```

La predicción es una **estimación del modelo**, no una certeza.

---

# 19. RECONOCIMIENTO FACIAL

Flujo general:

```text
Cámara
   ↓
Detección facial
   ↓
Control de calidad
   ↓
Liveness
   ↓
Reconocimiento
   ↓
Validación de sesión
   ↓
Registro de asistencia
```

El sistema también debe verificar:

* usuario autorizado
* sesión válida
* horario
* duplicados
* permisos

---

# 20. COMPROBACIÓN FINAL

Después de arrancar todo, comprobar:

### Backend

```text
http://127.0.0.1:8000/api/health
```

### Swagger

```text
http://127.0.0.1:8000/docs
```

### Frontend

```text
http://127.0.0.1:8001
```

### ML

```powershell
python -c "import joblib; m=joblib.load('models/asistencia_logreg.joblib'); print('MODELO OK')"
```

### Base de datos

Debe estar:

```text
MySQL/MariaDB = ACTIVO
Puerto = 3306
```

---

# 21. ¿QUÉ VIENE CON GIT Y QUÉ NO?

## Viene con el repositorio

```text
Código backend
Código frontend
Código ML
Código chatbot
Scripts SQL
Modelo .joblib
Coeficientes del modelo
Métricas del modelo
requirements.txt
requirements-ml.txt
requirements-chatbot.txt
```

## NO viene con Git

```text
.env
Base de datos local funcionando
Credenciales de MySQL
JWT generado en una sesión
Claves secretas locales
```

## Modelos externos

Si algún módulo facial requiere un archivo de modelo ONNX que no esté incluido en el repositorio, debe descargarse y colocarse en la ruta indicada por ese módulo.

---

# 22. ACTUALIZAR EL PROYECTO

Antes de trabajar:

```powershell
git pull origin feature/rouss-asistencia-ia
```

Después de realizar cambios:

```powershell
git status
git add .
git commit -m "descripcion del cambio"
git push origin feature/rouss-asistencia-ia
```

---

# 23. RESUMEN DE INSTALACIÓN

```text
1. Instalar Git
2. Instalar Python 3.10
3. Instalar XAMPP
4. Clonar repositorio
5. Crear .venv
6. Activar .venv
7. Instalar requirements
8. Crear BD MySQL/MariaDB
9. Ejecutar scripts SQL
10. Crear .env
11. Generar SECRET_KEY
12. Verificar modelos faciales
13. Verificar modelo ML
14. Arrancar backend
15. Arrancar frontend
16. Iniciar sesión
17. Probar chatbot
```

---

# 24. PUERTOS

```text
Frontend  → 8001
Backend   → 8000
MySQL     → 3306
