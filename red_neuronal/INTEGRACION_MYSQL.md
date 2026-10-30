# Contrato de integración — Parte 6 / MySQL en la nube

**Estado: PREPARADA, PENDIENTE DE INTEGRACIÓN.** No se ha conectado ni evaluado la base real del compañero. No se requieren credenciales de nube en la computadora de quien desarrolla Parte 6. No se publican usuarios, contraseñas, claves ni tokens.

## Modelo y dependencias

Modelo ya entrenado: `red_neuronal/artifacts/best.keras`; escalador: `scaler.joblib`; comparación: `logistic.joblib`; evaluación sintética: `report.json`. Los tres binarios pequeños se incluyen en Git; no necesitan descargas privadas ni reentrenamiento. `model_manifest.json` identifica versión, SHA-256 de binarios y hash canónico del reporte. La carga verifica integridad antes de deserializar. Usar exclusivamente los artefactos confiables de este repositorio.

Python 3.12 de 64 bits, TensorFlow 2.20.0, Keras 3.15.1, NumPy, Pandas y scikit-learn. Instalar `pip install -r red_neuronal/requirements.txt`. El adaptador de referencia FastAPI/SQLAlchemy añade `requirements-integracion.txt`; las versiones completas verificadas están en `requirements-integracion-lock.txt`. En Windows usar un venv con ruta corta, por ejemplo `$env:USERPROFILE/.venvs/p6`, debido al límite de rutas de TensorFlow.

Arquitectura real: 9 → Dense(32, ReLU) → Dense(16, ReLU) → Dense(1, sigmoide), 865 parámetros. EarlyStopping, épocas configurables y evaluación cronológica con estudiantes separados están implementados en los scripts de entrenamiento originales. No llamar a train/fit durante una solicitud. Los pesos y las métricas existentes se conservaron.

## Servicio interno, separado de HTTP y de MySQL

```python
from red_neuronal.inference import AttendanceInference

service = AttendanceInference()  # Carga diferida y caché con lock por proceso.
result = service.predict(
    values_from_authorized_backend,
    source="mysql_experimental",
    cutoff=information_cutoff,
    session_at=next_session_datetime,
)
```

`values_from_authorized_backend` DEBE ser construido por el servidor tras verificar usuario, curso, matrícula y sesión. No procede del cuerpo enviado por el navegador. El servicio no recibe credenciales ni abre MySQL; puede llamarse desde el backend del compañero, donde la conexión ya existe. `red_neuronal/system_features.py` y `backend/app/services/parte6_service.py` son referencias de preparación/consultas sujetas a revisión del esquema real. El guard de desarrollo local no se debe desactivar para reutilizar contraseñas heredadas ni apuntar a producción.

### Orden, fórmulas y unidades

| Orden | Campo | Definición |
|---|---|---|
| 1 | asistencia_30d | PRESENTE o TARDANZA / total de sesiones anteriores en [objetivo−30 días, objetivo); fracción 0–1 |
| 2 | tardanzas_30d | TARDANZA / ese mismo total; fracción 0–1, menor o igual a asistencia_30d |
| 3 | asistencia_ultimas5 | PRESENTE o TARDANZA / cinco últimas sesiones previas; fracción 0–1 |
| 4 | sesiones_previas | Número entero de sesiones previas elegibles; se exige al menos 5 y como máximo 1000 en el contrato actual |
| 5 | promedio_previo | Media aritmética de notas conocidas antes del corte; escala 0–20, sin ponderación |
| 6 | sin_notas | Entero 0/1; si no hay notas conocidas es 1 y promedio_previo=0, codificación explícita del modelo |
| 7 | dia_sin | sin(2π × weekday/7), lunes=0, de la sesión programada |
| 8 | dia_cos | cos(2π × weekday/7), mismo día que dia_sin |
| 9 | hora | Hora programada + minutos/60; horas 0 ≤ valor < 24 |

Los identificadores, notas futuras, asistencia objetivo y datos faciales nunca son entradas. TARDANZA cuenta como asistencia; no se aplica el factor 0,5 que pueda usar otro modelo del proyecto. El historial vacío, incompleto, duplicado o sin fechas fiables bloquea la inferencia; la falta de registro NO significa AUSENTE. Si la ventana de 30 días no contiene sesiones conocidas, las dos proporciones se codifican como cero según la preparación original; el historial completo todavía necesita cinco sesiones.

La ausencia de notas es una codificación existente, no una nota observada cero. Debe advertirse que sin_notas=1 no está representado en el dataset sintético actual. No imputar medias de otros estudiantes. Todos los valores deben ser finitos; se rechazan campos extra, NaN, ratios fuera de rango y seno/coseno incompatibles.

### Preprocesamiento

Construir el vector exactamente en `prepare.FEATURES`. Se ejecuta el **mismo StandardScaler ya ajustado exclusivamente en entrenamiento**, con `transform`, y se convierte a float32. No volver a normalizar notas dividiéndolas por 20, no recalcular el escalador con MySQL y no usar el pipeline de regresión logística de otros módulos. Se llama al modelo con `training=False`; la sigmoide devuelve P(asiste). La comparación logística usa el mismo vector escalado.

### Contratos JSON internos

Los nombres se utilizan como un objeto, validado por `HistoricalInputs`; la clase ordena el vector de manera canónica. Ejemplo exclusivamente sintético:

```json
{
  "asistencia_30d": 0.8,
  "tardanzas_30d": 0.2,
  "asistencia_ultimas5": 0.8,
  "sesiones_previas": 10,
  "promedio_previo": 14.0,
  "sin_notas": 0,
  "dia_sin": 0.0,
  "dia_cos": 1.0,
  "hora": 8.0
}
```

Contexto separado: `source` = `sintetico` o `mysql_experimental`; `cutoff` y `session_at` son fechas ISO con zona consistente y cutoff < session_at. El backend debe garantizar que cada observación era conocida al corte: no basta con que la fecha de la clase sea anterior.

La respuesta del servicio contiene `probabilidad` (float 0–1 calculado), `logistica_probabilidad`, `umbral`, `model_version`, `model_sha256`, `scaler_sha256`, `training_origin=sintetico`, `feature_order`, `source`, `cutoff`, `session_at`, `experimental=true` y `validation_scope`. No inventar una probabilidad si faltan datos. No convertir la salida en una etiqueta de capacidad, responsabilidad o riesgo. La versión actual es `parte6-dense-9x32x16x1-v1`; cambiarla exige un nuevo modelo evaluado y un nuevo manifiesto.

## Integración protegida que debe realizar el compañero

1. En SU backend, reutilizar su Session/engine SQLAlchemy y la autenticación JWT ya operativa. Verificar los nombres y relaciones reales de las tablas; no copiar credenciales al frontend o a este repositorio.
2. Aceptar únicamente IDs positivos de curso, estudiante y sesión. Verificar rol profesor activo, asignación del profesor al curso, matrícula del estudiante en ESE curso y que sea la próxima sesión activa. No confiar en el rol declarado por el navegador o en que conoció un ID.
3. Obtener datos conocidos al corte, con una transacción coherente, resolver la zona horaria real y construir las nueve variables. Si no existe evidencia fiable de ausencias, matrícula, disponibilidad o notas, devolver motivos y bloquear.
4. Invocar `AttendanceInference.predict` con el vector construido internamente y la procedencia. Nunca montar una ruta pública que acepte libremente las nueve variables para datos reales.
5. Devolver JSON compatible con los endpoints de referencia y conservar mensajes de origen/experimentalidad. No guardar predicciones ni crear/modificar tablas sin autorización independiente.
6. Probar permisos e inferencia con datos autorizados en un entorno de integración, no modificar producción para una demostración. Solo después marcar la integración como operativa en su API de estado.

Tablas PROBABLES según el esquema local revisado, sujetas a verificación en la nube: usuarios(id, rol, estado); profesores(usuario_id); asignaciones_profesor(profesor_id, curso_id); cursos; estudiantes(usuario_id); matriculas(curso_id, estudiante_id, matriculado_en); sesiones_clase(curso_id, fecha, hora_inicio/fin, estado, fecha_registro); asistencias(usuario_id, sesion_id, estado, fecha_registro); evaluaciones(curso_id, creado_en); notas(estudiante_id, evaluacion_id, nota, estado, registrada_en). No se necesitan tablas de EmoScan, rostros ni embeddings.

**Límites del esquema local:** las notas son por evaluación, mientras que el generador produce observaciones por sesión. La media de notas disponibles conserva la fórmula, pero no se presume equivalencia de distribución; no se duplican evaluaciones por asistencia ni se inventa su vínculo a sesiones. `registrada_en` representa la última modificación, no un historial completo. El adaptador de referencia solo admite una próxima sesión futura con corte actual; una reconstrucción retrospectiva necesita snapshots/versiones auditadas y se bloquea sin ellos. La zona horaria y la disponibilidad deben verificarse con el esquema real antes de activar MySQL.

## Rutas existentes y estado pendiente

La demostración local funciona con `red_neuronal.app:app` (8006) o con `app.parte6:app` (8007). El servidor integrado **por defecto devuelve Pendiente de integración**, no consulta MySQL ni habilita acceso académico. Los selectores quedan vacíos y deshabilitados. La sesión de demostración no concede autorización académica.

Rutas públicas existentes de demostración: POST `/api/parte6/demo/session`, GET `/api/parte6/report`, POST `/api/parte6/predict`. Esta última solo acepta origen sintético y un historial fechado; no es el servicio interno de nueve valores.

Contratos preparados para el backend responsable: GET `/api/parte6/system/courses`, GET `/system/courses/{course}/students`, GET `/system/courses/{course}/sessions`, POST `/system/context`, POST `/system/predict`, GET `/system/status` (todas bajo `/api/parte6`). POST académico recibe solo `{"curso_id":1,"estudiante_id":1,"sesion_id":8}`. Contexto devuelve ready, history, features o null, blockers, warnings, origen, cutoff y sesión. Predicción devuelve esos datos y la salida del servicio interno. Sin permisos: 401/403 o 404 sin revelar identidades; datos incompletos/sesión caducada: 409. No activar por un mero flag sin verificar la conexión y los datos.

`backend/app/parte6.py` incluye un acceso JWT de referencia y consultas de solo lectura para pruebas aisladas. No sustituye el login de nube ni afirma que la base real esté conectada. La única activación de prueba utilizada en el navegador usa una fixture **SQLite RAM**, marcada visiblemente como tal. El código de pruebas nunca se monta en la aplicación normal.

## Ejecutar sin producción

```powershell
py -3.12 -m venv "$env:USERPROFILE/.venvs/p6"
$pythonP6 = "$env:USERPROFILE/.venvs/p6/Scripts/python.exe"
& $pythonP6 -m pip install -r red_neuronal/requirements-integracion.txt
& $pythonP6 -m red_neuronal.validate_artifacts
& $pythonP6 -m pytest red_neuronal/tests -q -p no:cacheprovider
& $pythonP6 -m red_neuronal.run_system_ui_tests
& ./red_neuronal/start_parte6.ps1 -Port 8007
```

Abrir http://127.0.0.1:8007/profesor/red-neuronal.html. Seleccionar Demostración sintética e iniciar la sesión local. Las métricas pertenecen a 4.200 ejemplos sintéticos supervisados (2.520 entrenamiento, 840 validación, 840 prueba), no a MySQL. Las curvas, matrices y predicciones se leen del modelo/artefactos reales; no son porcentajes de JavaScript.

El runner de interfaz usa Chrome instalado en Windows y un puerto temporal; cierra su propia fixture. Para otra plataforma adaptar la ruta del navegador, no alterar las métricas. Las dependencias/artefactos se verifican desde una copia limpia durante la publicación; consultar `RESULTADOS_PUBLICACION.md` para pruebas efectivamente ejecutadas y límites.
