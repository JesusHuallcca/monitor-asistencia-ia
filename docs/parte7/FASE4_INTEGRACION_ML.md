# Fase 4 — integración ML de solo lectura

Worktree: monitor-asistencia-parte7. Rama: parte-7-chatbot-inteligente.
Sin commits, pushes, merges, entrenamiento, conexiones MySQL ni modificaciones de modelos.

## Inventario y hallazgos

| Módulo | Evidencia disponible | Integración |
|---|---|---|
| K-Means | segmentacion/resultados/: cuatro variables, 150 perfiles sintéticos, K=3, silueta 0.2373692496101911. | Lee y valida resultados guardados; devuelve solamente agregados, sin identificadores. No ajusta K-Means, StandardScaler ni PCA. |
| Servicio CSV de segmentación | Ejecuta ajuste de modelos. Además, el script principal de esta rama declara tres variables, mientras los resultados guardados y el servicio describen cuatro. | No se invoca ni modifica ese flujo. Se documenta la discrepancia para resolverla en su módulo, evitando duplicar o reentrenar. |
| Regresión | Predictor de asistencia de regresión LOGÍSTICA, no lineal. Hay métricas archivadas, pero falta models/asistencia_logreg.joblib. | Muestra evaluación archivada; inferencia no disponible. No reconstruye probabilidades a partir de métricas ni crea otro modelo. |
| Procedencia de regresión | El generador predeterminado es sintético; el JSON de métricas no contiene manifiesto, huella de dataset o versión vinculada de pesos. | origin=no_verificado, model_version=null y report_version con SHA256 del reporte. No se inventa procedencia ni versión del modelo. |
| Parte 6 | Revisada origin/parte-6-red-neuronal, commit 68430e14d481c37b4f898969f40a36bb0abadc27. Esa rama tiene servicio MySQL experimental; no está integrado en Parte 7. | PENDIENTE aquí. No se copian código, pesos ni evaluaciones de esa rama. No se simulan probabilidades reales. |

Métricas archivadas de regresión: accuracy 0.6748, precision 0.7564, recall 0.7023, F1 0.7284, ROC-AUC 0.7374, n_test=1688. Se leen del JSON, nunca de valores fijos en JavaScript. El script de entrenamiento existente divide registros aleatoriamente con estratificación: puede mezclar sesiones del mismo estudiante. No equivale a una prueba temporal de Parte 6. No se declara un modelo ganador.

La versión del resultado K-Means es la huella de los artefactos consultados, no una versión ficticia de pesos. Se validan origen sintético por fila, hash del CSV fuente, variables, unicidad de perfiles, conteos, medias del resumen y K. Las descripciones de grupos se obtienen ordenando sus medias reales de asistencia, sin cambiar asignaciones.

## Variables y objetivo

- K-Means: asistencia_ratio, tardanzas_ratio, promedio_notas, expresiones_positivas_ratio. La última es exclusivamente sintética; no representa emociones reales ni procede de EmoScan. No es un clasificador de riesgo.
- Regresión logística: asistencia_ratio_30d, asistencias_consecutivas, ausencias_consecutivas, dia_semana, hora_inicio_clase, es_inicio_ciclo, promedio_notas, tardanzas_ratio.
- Parte 6: asistencia_30d, tardanzas_30d, asistencia_ultimas5, sesiones_previas, promedio_previo, sin_notas, dia_sin, dia_cos, hora. Arquitectura revisada: 9 → 32 ReLU → 16 ReLU → 1 sigmoide, 865 parámetros; es una explicación del contrato remoto, no una ejecución local.

En ai/ml/generate_dataset.py, asistira=1 incluye PRESENTE y TARDANZA. **P(asistir) no es P(llegar temprano)**. El peso 0.5 de las tardanzas en una variable histórica del predictor antiguo no cambia esa etiqueta. No se calcula puntualidad restando probabilidades de modelos diferentes.

## Arquitectura y archivos

Se reutilizan autenticación, SQLAlchemy, ámbito académico, conversación firmada, voz, historial, snapshots temporales y exportadores existentes.

- services/chatbot_ml.py: intenciones cerradas ML, lectores validados y adaptadores de inferencia, sin entrenamiento.
- api/chatbot_ml.py: catálogo, consultas y reportes autenticados.
- chatbot_conversation.py y api/chatbot.py: intenciones ML antes de reglas genéricas; validación de selecciones antes de consultar proveedores. Las predicciones genéricas también usan el adaptador seguro.
- chatbot_reports.py, chatbot_report_documents.py y api/chatbot_reports.py: tipo separado ml_evaluation. No confunde métricas con asistencias; conserva retorno a reportes académicos.
- frontend/components/chatbot.js y css/chatbot.css: tarjetas de origen/estado/versión/variables y vista previa ML con descargas, conservando SENATI.
- backend/tests/parte7/test_ml.py y actualización del caso de seguridad de predicciones.
- frontend/tests/parte7.ml.chrome.test.mjs; script test:ml en package.json.

Gemini no recibe ni redacta resultados ML: se conservan cantidades, límites y advertencias en respuestas deterministas.

## Contratos de API

Todos requieren la sesión autenticada existente. No se incluyen tokens en URLs. Un administrador necesita la concesión institucional explícita ya definida por el chatbot.

### GET /api/chatbot/ml/catalog

Devuelve models, comparable=false, winner=null y comparison_reason. Son evaluaciones públicas de artefactos sintéticos/archivados, no datos individuales de la institución.

Cada modelo declara model, status (available/pending/unavailable), reason, origin, model_version y variables. Según disponibilidad: metrics, report_version, source, target, limitations. Un reporte disponible no garantiza que exista su artefacto de inferencia.

### POST /api/chatbot/ml/query

Ejemplo JSON:

    {"model":"kmeans","operation":"results","course_id":null,"student_id":null}

model: kmeans, regresion_logistica, red_neuronal_parte6.
operation: explain, results, predict.
IDs opcionales positivos; campos adicionales prohibidos. No acepta features calculadas por el cliente, SQL, rutas de modelos, URLs, origen alegado ni sesiones futuras sin validación.

- explain: explicación educativa.
- results: agregados K-Means, métricas archivadas de regresión o estado pendiente de Parte 6.
- predict: servicio supervisado autorizado; K-Means rechaza esta operación con 422.
- Una selección individual K-Means devuelve pendiente: los IDs sintéticos nunca se relacionan con estudiantes reales. Las consultas de segmentación del sistema o del curso no se sustituyen por asignaciones de demostración.
- La respuesta conversacional incluye reply, intent, data=[], provider=local y ml. El endpoint de mensajes añade contexto firmado e historial.
- Inferencia disponible: probability, target, origin, training_origin, model_version, variables, cutoff, session_at y advertencias.
- Sin servicio/datos suficientes: NO incluye probability.
- 401 sin sesión, 403 fuera de ámbito/rol, 422 contrato inválido. La ausencia de artefactos se expresa mediante estado.

### POST /api/chatbot/ml/reports

Crea vista previa kind=ml_evaluation con métricas archivadas y estados pendientes, no una evaluación nueva. Incluye origen y versión por fila, metodología, comparable=false y winner=null. Las métricas globales no se filtran por curso ni se presentan como rendimiento del curso seleccionado.

Reutiliza las rutas de fase 3:

- GET /api/chatbot/reports/{id}
- POST /api/chatbot/reports/{id}/exports/{xlsx|pdf|docx}
- GET /api/chatbot/reports/{id}/files/{xlsx|pdf|docx}

Propiedad por cuenta, huella del ámbito vigente, TTL diez minutos, cuotas, archivos RAM y auditoría minimizada. Se revalidan permisos al descargar y después del renderizado. Excel conserva valores sin fórmulas peligrosas; PDF/Word muestran hasta seis decimales en métricas ML. Pedir «Ahora el mismo en PDF» conserva el snapshot.

### POST /api/chatbot/message

Contrato existente, ampliado con ML_EXPLAIN, ML_SEGMENTS, ML_NEURAL, ML_REGRESSION, ML_REPORT, ML_TARGET y ML_SAFETY. Conserva saludos, cursos, reportes académicos, voz y contexto firmado. El modelo seleccionado también se conserva en memoria firmada (ml_model), permitiendo «¿Y qué variables utiliza?» y «¿Y mi probabilidad?» sin cambiar inadvertidamente de predictor.

## Parte 6: contrato revisado y dependencias pendientes

Contratos de la rama remota, SIN instalar ni habilitar aquí:

1. GET /api/parte6/system/courses, /courses/{id}/students y /courses/{id}/sessions: listados del profesor asignado.
2. POST /api/parte6/system/context y /predict: selección estricta {curso_id,estudiante_id,sesion_id}, solo profesor. Devuelve ready, blockers, features, cutoff, session_at y advertencias.
3. AttendanceInference.predict(features, source='mysql_experimental', cutoff=..., session_at=...): nueve entradas ordenadas; corte anterior a sesión; modelo y escalador validados con manifiesto; entrenamiento y validación sintéticos.

El adaptador opcional utiliza esos servicios internos autorizados SOLO si sus módulos se integran expresamente en un trabajo posterior. No abre URLs ni reenvía JWT a otros servidores. Resuelve la próxima sesión en backend, vuelve a comprobar curso/estudiante y respeta ready=false. Valida probabilidad finita, orden de variables, versión, hash, origen y consistencia temporal de la respuesta. No acepta features desde el chatbot.

Se conserva el contrato de Parte 6 de SOLO PROFESOR para inferencia. Un estudiante puede consultar explicaciones, pero no invocar ese servicio por un canal alternativo. ADMIN no suplanta al profesor a través de este adaptador.

Antes de activarlo faltan: integración revisada de servicios y esquema histórico, TensorFlow compatible/artefactos/manifiesto, pruebas en base de desarrollo autorizada y contrato de evaluación versionada. No se solicitan credenciales de nube ni se modifica producción.

Regresión pendiente: instalar el artefacto existente confiable y compatible, vincular manifiesto/dataset/versión y validar cambio de dominio. El adaptador ya restringe historial al curso/estudiante y al corte, excluye notas futuras o pendientes, no imputa 14 ni consulta otros cursos. Rechaza datos insuficientes o inconsistentes. Los artefactos deben ser inmutables durante el proceso: reiniciar el servicio al cambiarlos porque el predictor existente usa caché. No cargar joblib de usuarios.

## Pruebas y cómo demostrarlo

Python virtual independiente de Parte 7; dependencias ya presentes en requirements-parte7-pruebas.txt y requirements-parte7-reportes.txt. No se añade TensorFlow ni se cambia Parte 6.

Desde el worktree, usando el Python virtual correspondiente:

    python -B -m pytest backend/tests/parte7 -q -p no:cacheprovider

Desde frontend:

    npm run test:chatbot
    npm run test:reports
    npm run test:ml

Las dos suites de descargas requieren la demo segura y cuotas reales. Dejar un minuto entre ellas con la misma cuenta o reiniciar exclusivamente la demo propia tras identificar su proceso. MONITOR_TEST_NODE_MODULES permite las herramientas externas locales sin modificar otras instalaciones.

Inicio seguro, sin app.main ni su arranque MySQL:

    python -B -m uvicorn parte7_demo:app --app-dir backend --host 127.0.0.1 --port 8017

Abrir **http://127.0.0.1:8017/** → **Probar como profesor** → abrir Asistente IA.

Preguntas:

1. ¿Qué es K-Means?
2. Muestra los resultados K-Means sintéticos.
3. Diferencias entre regresión y red neuronal.
4. Consulta la probabilidad de asistencia con Parte 6. Debe indicar pendiente, sin porcentaje inventado.
5. Genera reporte de evaluación y comparación de regresión y K-Means. Revisar cada origen y descargar Excel, PDF o Word.
6. Ahora el mismo reporte en PDF.
7. ¿Asistir es igual que llegar temprano?

La demo usa cuentas sintéticas y SQLite RAM, MySQL bloqueado, Gemini desactivado. No demuestra conexión con producción. Los casos de inferencia disponible de las pruebas usan dobles explícitos: **no son ejecuciones ni predicciones reales del modelo neuronal**. K-Means y las métricas archivadas sí se leen de artefactos existentes.

Evidencias Chrome: evidencias/ml-1366.png, ml-1920.png y ml-390.png. Archivos exportados verificados abriéndolos con openpyxl, pypdf y python-docx, además de su flujo real de descarga en Chrome.

Resultados finales: [RESULTADOS_FASE4_ML.md](RESULTADOS_FASE4_ML.md). Backend: 198 pruebas aprobadas; Chrome: 72 de interfaz, 44 de reportes y 60 de integración ML.
