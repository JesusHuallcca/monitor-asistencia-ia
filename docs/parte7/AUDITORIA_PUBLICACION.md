# Auditoría de publicación de Parte 7

Fecha de revisión: 2026-10-31. Resultado: **NO PUBLICAR**.

La rama local parte-7-chatbot-inteligente se conserva en monitor-asistencia-parte7. No se creó commit, no se hizo push, merge ni despliegue. No se ejecutaron migraciones ni conexiones a MySQL de producción. Los tres stash permanecen intactos.

## 1. Estado de Git y compatibilidad

- HEAD de Parte 7: 90e7ce75c34497350728b9aa02afd74c9e8ca188.
- origin/main después de fetch: 6557e65fdb3cf66b2f7e4f563c6b1fce891fe9c8.
- Parte 7 está dos commits detrás de origin/main. Los cambios de Parte 7 siguen sin commit; no se han incorporado a ese conteo.
- Commits nuevos del remoto: 4952ac4 (integración de Parte 6 con MySQL) y 6557e65 (frontend responsive).
- La rama remota parte-7-chatbot-inteligente no existe en el momento de la consulta.
- Índice vacío; no hay eliminaciones en esta entrega. No se sobrescribieron archivos de otros worktrees ni se modificaron sus HEAD.
- main local permanece en f53d56b97a7ef840df89e7b1913d2f27b706ca54.

Seis archivos coinciden entre las modificaciones de Parte 7 y los cambios recientes de origin/main:

1. backend/app/api/chatbot.py
2. backend/app/services/chatbot_service.py
3. frontend/components/chatbot.js
4. frontend/estudiante/ia.html
5. frontend/js/chatbot-init.js
6. frontend/js/panel-comun.js

La coincidencia de rutas no demuestra por sí sola un conflicto textual, pero impide afirmar compatibilidad sin una integración revisada. No se ejecutó merge, rebase, reset ni checkout de otros archivos. Es necesario conservar los cambios responsive del compañero y la nueva integración neuronal al reconciliar estas seis rutas.

No se copió la Parte 6 ni se instalaron sus dependencias. La inferencia neuronal continúa identificada como pendiente en esta rama. El main remoto ahora contiene el servicio esperado por el adaptador; su funcionamiento combinado no fue probado y la explicación educativa deberá actualizarse después de integrarlo.

## 2. Estado de las cinco fases

| Fase | Resultado local comprobado | Pendiente |
|---|---|---|
| 1. Seguridad | Ámbitos cerrados por defecto; alumno propio, profesor por matrícula/curso asignado y administrador con concesión explícita; historia y contexto se invalidan al cambiar permisos. | Los secretos y endpoints heredados impiden certificar la seguridad de toda la aplicación. |
| 2. Conversación y voz | Saludos, seguimiento, curso/estudiante/período temporal firmado; teclado y transcripción; síntesis configurable y exclusión entre micrófono/reproducción. Gemini es opcional y no decide permisos ni SQL. | Micrófono físico y proveedor Gemini real no se probaron; se utilizaron sustitutos controlados para audio. |
| 3. Reportes | Vista previa y exportación real XLSX/PDF/DOCX desde el mismo dataset autorizado; protección de descarga, vencimiento, límites e inyección de fórmulas. | Integración cloud y almacenamiento compartido si se escala el servicio web. |
| 4. ML | Lectura de resultados guardados: 150 perfiles sintéticos, K=3, silueta 0.2373692496101911. Explicaciones y reportes sin entrenar. Se diferencian asistencia y puntualidad. | Parte 6 no está incorporada aquí; falta artefacto de regresión. Se responde pendiente/no disponible, sin fabricar probabilidades. No hay comparación común para declarar un ganador. |
| 5. Proactividad | Fuentes verificadas, revisión/activación explícita, configuración, bandeja, recordatorios, reportes programados, deduplicación y comunicaciones solo como borrador. APScheduler ejecuta con Chrome cerrado. | Migración revisada en MySQL de desarrollo y servicio worker dedicado. Sin transporte externo de mensajes. |

Integración comprobada: un router del chatbot reutiliza conversación, reportes, ML y proactividad. Los reportes ML y los snapshots programados reutilizan el mismo generador de documentos. El centro de notificaciones abre la vista previa del chatbot. Todas estas rutas comparten autorización del backend; no dependen de controles visuales.

## 3. Pruebas de esta revisión

| Comprobación | Resultado |
|---|---|
| pytest backend/tests/parte7 -q -p no:cacheprovider --tb=short | **256 aprobadas**, 1 aviso de deprecación Starlette/TestClient con httpx. |
| frontend/tests/chatbot.voice.test.mjs | Aprobada: voz simulada, permisos denegados, transcripción, cancelación y alternativa de texto. |
| frontend/tests/parte7.chrome.test.mjs | **72 comprobaciones** en Chrome real, API/audio simulados. |
| frontend/tests/parte7.proactive.chrome.test.mjs | **42 comprobaciones** contra FastAPI, JWT y SQLite reales. Chrome se cerró antes de verificar la ejecución del servidor. |
| frontend/tests/parte7.reports.chrome.test.mjs | **44 comprobaciones**; vista previa, descargas reales, PDF imprimible, permisos, períodos y ausencia de datos. |
| frontend/tests/parte7.live-demo.test.mjs | Conversación real: saludo → cursos → ranking de tardanzas → registros de octubre. |
| frontend/tests/parte7.ml.chrome.test.mjs | **60 comprobaciones**; permisos, estados pendientes, tres documentos y datos ML guardados, sin entrenamiento. |
| backend/parte7_report_examples.py | XLSX/PDF/DOCX generados y abiertos con lectores independientes: 8 registros sintéticos autorizados; 7 asistencias/8 = 87.5 %. |
| backend/parte7_proactive_examples.py | APScheduler real, sin navegador, reloj lógico de prueba acelerado: recordatorio y reporte semanal; 2 registros, asistencia 50 %, tres formatos abiertos. Sin envíos externos. |
| python -m pip check | Sin dependencias rotas en el entorno aislado Python 3.12. |
| node --check de chatbot.js y proactive.js; git diff --check | Aprobadas. |
| Migración aditiva: revisión estática | 5 sentencias CREATE TABLE; nombres de columnas coinciden con los 5 modelos. Sin DROP, ALTER, DELETE, TRUNCATE ni escrituras sobre tablas académicas. No ejecutada en MySQL. |
| Suite heredada: backend/tests/test_chatbot.py y test_chatbot_auth.py, --maxfail=2 | **2 errores de preparación**: fixture client no encontrada; ejecución detenida en los dos primeros casos. No se evaluaron los casos restantes. |

Las comprobaciones de navegador suman 218 aserciones entre las cuatro suites que informan conteo, más las pruebas de voz y conversación. Resoluciones: 1366×768, 1920×1080 y 390×844. No se observaron errores JavaScript en las ejecuciones aprobadas.

La primera ejecución de la suite proactiva detectó una carrera en la prueba: comprobaba la selección antes de completarse la consulta asíncrona de estudiantes autorizados. Se añadió una espera de la condición real en el DOM; la repetición completa aprobó las 42 comprobaciones. No se cambió la lógica de autorización para hacer pasar una prueba.

La suite heredada necesita un harness seguro para client/headers y datos sintéticos. Además, algunas expectativas antiguas permiten lectura administrativa implícita y deben actualizarse para exigir la concesión institucional explícita. No se debe debilitar el backend para satisfacer esas expectativas. Los archivos de prueba de repositorios de asistencia/rostros contienen rutinas manuales que escriben en BD; no se ejecutaron.

No se certifica la suite global ni la aplicación combinada con el main remoto actualizado. No se arrancó app.main: su lifespan intenta crear tablas y descargar un modelo facial; se usó únicamente parte7_demo con SQLite en memoria, MySQL bloqueado y Gemini deshabilitado.

## 4. Seguridad: bloqueos de publicación

### S1 — Claves heredadas en el árbol Git

- render.yaml:27 contiene un valor estático para JWT_SECRET_KEY.
- backend/app/core/config.py:13 contiene un respaldo de contraseña codificado en Base64; Base64 no protege una credencial.
- backend/app/core/config.py:23 contiene una clave JWT predeterminada.
- backend/app/db/database.py:6–16 utiliza la contraseña de respaldo cuando falta la variable de entorno.

No se copiaron sus valores a este informe, registros ni nuevos archivos. La búsqueda de patrones y de copias de los secretos heredados no encontró coincidencias en los archivos pendientes, incluyendo XML de XLSX/DOCX. Eso no elimina el problema: un nuevo commit seguiría referenciando los archivos heredados sensibles en su árbol e historial.

Corrección necesaria por el responsable: rotar/revocar las credenciales expuestas y la clave de firma, invalidar sesiones según el procedimiento del sistema, retirar literales/respaldo del código y exigir configuración explícita. Guardar secretos en el gestor del despliegue. Eliminar una cadena del último archivo no equivale a revocarla ni a retirarla del historial; cualquier limpieza de historial debe coordinarse, sin force push unilateral. No se verificó vigencia de credenciales intentando acceder al proveedor.

### S2 — Diagnóstico público y errores sensibles

- backend/app/main.py:183–204: /api/health carece de autenticación y devuelve pass_prefix, pass_len, has_fallback, host, user y db_error; además consulta MySQL.
- backend/app/main.py:101: el manejador general devuelve el texto de la excepción al cliente.

Se confirmó estáticamente que las claves sensibles del diagnóstico también están presentes en origin/main. No se llamó ese endpoint de producción.

Corrección necesaria: health público mínimo, sin credenciales, conexión identificable ni errores del motor; diagnóstico operacional protegido; respuestas 500 genéricas y logs saneados. Evitar imprimir traceback/SQL con parámetros privados.

### S3 — Ámbito académico heredado fuera del chatbot

GET /api/attendance/ permite el rol profesor, pero llama attendance_service.get_all(db), que deriva a find_all sin filtro por cursos asignados. La revisión estática muestra ausencia de ámbito académico en ese recorrido. Requiere corrección y prueba con dos profesores de cursos diferentes antes de certificar aislamiento global.

El router legado backend/app/api/face.py contiene operaciones sin dependencia de autorización, pero NO está montado por el app.main revisado. No se presenta como una exposición pública confirmada; no debe montarse sin revisión. El router montado es face_auth y sí requiere usuario autenticado.

### S4 — Pruebas y configuración de ejecución incompletas

Los errores de fixtures heredados y la divergencia con origin/main son bloqueos adicionales. Resolverlos y repetir pruebas combinadas antes de publicar.

render.yaml instala solamente requirements.txt, que no incluye los exportadores ni el planificador de Parte 7. El archivo lock de Parte 7 quedó sincronizado con el entorno realmente probado, incorporando APScheduler, tzlocal y annotated-doc que faltaban; no se instalaron paquetes nuevos. Esta verificación local no sustituye una resolución conjunta Linux/TensorFlow después de reconciliar main.

### Riesgos operativos adicionales

- El engine MySQL actual no configura explícitamente CA/verificación TLS en connect_args. Validar y configurar cifrado y verificación de identidad del servidor según el proveedor antes de usar cloud; no se comprobó el servidor real.
- app.main crea tablas al arrancar. Separar DDL de arranque y del usuario de ejecución antes de certificar un despliegue sin migración automática.
- El contexto temporal firmado es legible, no cifrado; no incluir datos privados en él. Los permisos se vuelven a validar en servidor.
- Validar sub numérico del JWT para responder 401 en vez de 500 frente a claims malformados.
- Restringir CORS a orígenes institucionales concretos en el entorno final.
- ReportStore y las cuotas viven en memoria de UN proceso web: con múltiples procesos/réplicas habrá fallos de descarga y cuotas por instancia. Mantener una instancia web mientras se integra almacenamiento/limitación compartidos. Un reinicio invalida vistas previas/archivos temporales.
- Gemini real y audio físico no se probaron. La funcionalidad por texto funciona sin ellos.
- El alcance fue revisión de código, pruebas y búsqueda dirigida de secretos; no un pentest ni un análisis exhaustivo de vulnerabilidades de todas las dependencias.

## 5. MySQL: necesidades y propuesta aditiva

Archivo para revisión, NO aplicado: database/mysql/migrations/parte7/001_proactividad_additive.sql.

| Tabla nueva | Propósito |
|---|---|
| chatbot_proactive_actions | Propietario/destinatario, configuración, zona, frecuencia, estado, próxima ejecución UTC y revisión. |
| chatbot_proactive_preferences | Habilitación y zona horaria del usuario. |
| chatbot_proactive_notifications | Resultado privado, clave única de ejecución, lectura y vencimiento. |
| chatbot_proactive_audit | Códigos de evento y referencias mínimas. |
| chatbot_proactive_worker | Latido del planificador. |

Las referencias usan usuarios.id, cursos.id y estudiantes.id, INT conforme al esquema versionado. Antes de aplicar, el compañero debe verificar los tipos/signedness, InnoDB, charset/collation, índices, claves y CHECK en la versión REAL de desarrollo. La equivalencia de nombres de columnas no certifica equivalencia completa de DDL.

ProactiveBase es independiente: las tablas nuevas no se añaden a Base.metadata. La propuesta SQL agrega FK/CHECK/índices y utiliza MEDIUMTEXT para snapshots/configuración donde el ORM declara Text; no sustituir esa propuesta por create_all en MySQL. Probar tamaño, constraints, transacciones, row locks, concurrencia, reinicio y deduplicación en MySQL de desarrollo. La concurrencia local se probó con SQLite de archivo, no con MySQL.

Comprobar también la existencia previa de chat_historial y tablas académicas. database/mysql/05_chatbot.sql es una propuesta aditiva previa que debe revisarse si falta el historial; no se ejecutó. **No ejecutar 01_schema.sql ni 02_seed.sql sobre una base existente**: el primero contiene DROP TABLE y el segundo datos de inicialización.

Usar cuentas de aplicación/worker sin DDL; migración con cuenta técnica separada y aprobación humana. No crear otra base ni modificar la del compañero durante esta auditoría.

## 6. Worker y Render

Comando preparado: python backend/parte7_worker.py. Se ejecuta como UN servicio continuo separado del proceso web, con APScheduler 3.11.3 BlockingScheduler; no depende de Chrome. Consulta las acciones persistentes y guarda notificación/avance en una transacción, con identidad y clave de ejecución únicas. No hay transporte de correo, WhatsApp ni mensajes externos; las comunicaciones terminan en reviewed y external_delivery=false.

El ejemplo docs/parte7/despliegue/worker-render.example.yaml es para revisión, tiene autoDeploy:false y secretos sync:false. No modifica render.yaml, no crea servicios ni despliega nada. El Render actual solo declara el web; necesita un background worker independiente.

Variables requeridas para preparar el entorno, sin sus valores:

| Variables | Uso |
|---|---|
| DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD | Conexión de desarrollo explícita; posteriormente configuración privada administrada por el propietario. |
| JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES | Firma y vigencia; clave nueva segura y consistente con el backend. |
| APP_TIMEZONE | Zona institucional, por ejemplo America/Lima. |
| CHATBOT_INSTITUTIONAL_READ_USER_IDS | Concesión explícita de lectura institucional; vacío deniega a administradores. No es un campo del cliente. |
| CHATBOT_PROACTIVE_ENABLED=true | Habilitación explícita del proceso worker. |
| CHATBOT_PROACTIVE_MIGRATION_REVIEWED=true | Confirmación operacional posterior a revisión/aplicación autorizada, nunca un reemplazo de esa revisión. |
| GEMINI_API_KEY, GEMINI_MODEL | Opcionales; omitir para operar por intenciones locales. No publicar sus valores. |

El worker exige explícitamente las cuatro variables principales de DB antes de importar la conexión. Como endurecimiento, exigir también JWT_SECRET_KEY en la configuración validada y eliminar el respaldo heredado antes de desplegar. DB_PORT debe coincidir con el puerto privado del proveedor; no asumir el puerto local.

Instalación propuesta para staging, después de resolver seguridad y compatibilidad con main:

    python -m pip install -r requirements.txt -r requirements-parte7-proactivo.txt
    python -m pip check

Para pruebas, agregar requirements-parte7-pruebas.txt. El lock es evidencia del entorno Python 3.12 probado; no sustituye el lock conjunto con TensorFlow de main. Validar resolución, wheels y arranque en la imagen Linux final.

Inicialmente mantener un proceso web para la caché privada de reportes y un worker separado. No arrancar un planificador por worker Uvicorn. Supervisar latido, reinicios, vencimiento, errores saneados y métricas de ejecución. Revisar auto deploy y rama vinculada en Render antes de cualquier publicación futura; esta auditoría no consultó ni alteró esos ajustes privados.

Render documenta el servicio continuo en [Background Workers](https://render.com/docs/background-workers). Para secretos y la opción de guardarlos sin desplegar, consultar [Environment Variables and Secrets](https://render.com/docs/configure-environment-variables). La separación de procesos también es coherente con la [FAQ de APScheduler 3](https://apscheduler.readthedocs.io/en/3.x/faq.html); este módulo conserva las acciones en sus propias tablas y no comparte un job store de APScheduler entre procesos.

## 7. Pasos para el compañero

1. Revisar S1–S4. Rotar claves con el propietario, corregir diagnósticos/ámbito y quitar respaldos; no compartir credenciales en Git, chat o logs.
2. Reconciliar los seis archivos coincidentes con origin/main en una integración revisada, preservando el frontend responsive y los contratos de Parte 6. No sobrescribir main ni otras ramas.
3. Resolver dependencias conjuntas, recuperar el harness legado seguro y actualizar expectativas de permisos. Repetir suite Parte 7, legado y flujos combinados con Parte 6/Segmentación.
4. Revisar un dump solo de estructura autorizado o una base de desarrollo proporcionada por el propietario; verificar las tablas existentes y evaluar la migración aditiva.
5. Aplicar la migración SOLO en desarrollo autorizado y registrar su versión. Ejecutar pruebas MySQL: scopes, FK/CHECK, cancelación de fuentes, revocaciones, concurrencia, reinicio y duplicados.
6. Configurar variables privadas y TLS; comprobar que web y worker utilizan el mismo entorno autorizado y zona institucional.
7. Arrancar el web de staging sin DDL automático y un único worker dedicado. Confirmar latido, generar recordatorio/reporte sintéticos, cerrar Chrome y verificar una sola notificación. Verificar que comunicaciones sigan siendo borradores.
8. Aprobar el contenido exacto del commit tras escaneo final. Solo entonces crear commit y push de parte-7-chatbot-inteligente. La integración a main y cualquier despliegue/migración de producción requieren revisión posterior; no se realizaron aquí.

## 8. Evidencias y revisión local

La demo segura queda en http://127.0.0.1:8017/. Entrar con los botones de profesor/estudiante; son identidades sintéticas de SQLite RAM. Al reiniciar se borra esa demo. No usar app.main ni credenciales cloud para reproducir estas pruebas.

- Ejemplos de fase 3: docs/parte7/ejemplos/ejemplo-asistencia-autorizada.xlsx, .pdf y .docx.
- Ejemplos del worker: docs/parte7/ejemplos/fase5-reporte-semanal.xlsx, .pdf y .docx.
- Manifiestos con hashes y cálculos: VERIFICACION.json y FASE5_DEMOSTRACION.json en esa carpeta.
- Capturas de 1366, 1920 y 390 píxeles: docs/parte7/evidencias/.
- Únicos ajustes de esta auditoría: espera asíncrona en la prueba proactiva, sincronización del lock, regeneración de ejemplos/capturas y este informe. Sin cambios en algoritmos, EmoScan, MySQL, configuración local de servidores, render.yaml ni otros worktrees.

No se encontraron .env, credenciales copiadas, ONNX nuevos, bases locales, entornos virtuales o temporales entre los candidatos. Los documentos/capturas incluidos son evidencias sintéticas deliberadas. Hay modelos ONNX ya versionados en el repositorio heredado; no se añadieron, borraron ni modificaron. .gitignore no elimina archivos que ya estuvieran versionados.

**No hay hash de publicación ni enlace a una rama publicada: no se creó commit ni se hizo push.**

## 9. Inventario exacto de archivos pendientes

10 modificados y 70 nuevos; 80 en total. No hay eliminaciones. Índice sin archivos preparados.

Modificados:

```text
backend/app/api/chatbot.py
backend/app/schemas/chatbot.py
backend/app/services/chatbot_service.py
frontend/components/chatbot.js
frontend/css/chatbot.css
frontend/estudiante/ia.html
frontend/js/chatbot-init.js
frontend/js/panel-comun.js
frontend/package.json
frontend/tests/chatbot.voice.test.mjs
```

Nuevos:

```text
backend/app/api/chatbot_ml.py
backend/app/api/chatbot_proactive.py
backend/app/api/chatbot_reports.py
backend/app/db/proactive_models.py
backend/app/schemas/chatbot_proactive.py
backend/app/schemas/chatbot_reports.py
backend/app/services/chatbot_conversation.py
backend/app/services/chatbot_ml.py
backend/app/services/chatbot_proactive.py
backend/app/services/chatbot_proactive_scheduler.py
backend/app/services/chatbot_report_documents.py
backend/app/services/chatbot_report_store.py
backend/app/services/chatbot_reports.py
backend/app/services/chatbot_security.py
backend/parte7_demo.py
backend/parte7_proactive_examples.py
backend/parte7_report_examples.py
backend/parte7_worker.py
backend/tests/parte7/conftest.py
backend/tests/parte7/test_chatbot_security.py
backend/tests/parte7/test_conversation.py
backend/tests/parte7/test_demo.py
backend/tests/parte7/test_ml.py
backend/tests/parte7/test_proactive.py
backend/tests/parte7/test_reports.py
database/mysql/migrations/parte7/001_proactividad_additive.sql
docs/parte7/AUDITORIA_PUBLICACION.md
docs/parte7/FASE2_CONVERSACION_Y_VOZ.md
docs/parte7/FASE3_REPORTES_ACADEMICOS.md
docs/parte7/FASE4_INTEGRACION_ML.md
docs/parte7/FASE5_ASISTENTE_PROACTIVO.md
docs/parte7/PLAN_IMPLEMENTACION.md
docs/parte7/RESULTADOS_FASE4_ML.md
docs/parte7/RESULTADOS_FASE5.md
docs/parte7/despliegue/worker-render.example.yaml
docs/parte7/ejemplos/FASE5_DEMOSTRACION.json
docs/parte7/ejemplos/VERIFICACION.json
docs/parte7/ejemplos/ejemplo-asistencia-autorizada.docx
docs/parte7/ejemplos/ejemplo-asistencia-autorizada.pdf
docs/parte7/ejemplos/ejemplo-asistencia-autorizada.xlsx
docs/parte7/ejemplos/fase5-reporte-semanal.docx
docs/parte7/ejemplos/fase5-reporte-semanal.pdf
docs/parte7/ejemplos/fase5-reporte-semanal.xlsx
docs/parte7/evidencias/chatbot-1366.png
docs/parte7/evidencias/chatbot-1920.png
docs/parte7/evidencias/chatbot-390.png
docs/parte7/evidencias/demo-conversacion.png
docs/parte7/evidencias/ml-1366.png
docs/parte7/evidencias/ml-1920.png
docs/parte7/evidencias/ml-390.png
docs/parte7/evidencias/proactivo-1366.png
docs/parte7/evidencias/proactivo-1920.png
docs/parte7/evidencias/proactivo-390.png
docs/parte7/evidencias/reportes-1366.png
docs/parte7/evidencias/reportes-1920.png
docs/parte7/evidencias/reportes-390.png
frontend/components/proactive.js
frontend/css/proactive.css
frontend/package-lock.json
frontend/profesor/ia.html
frontend/tests/parte7-tools.mjs
frontend/tests/parte7.chrome.test.mjs
frontend/tests/parte7.live-demo.test.mjs
frontend/tests/parte7.ml.chrome.test.mjs
frontend/tests/parte7.proactive.chrome.test.mjs
frontend/tests/parte7.reports.chrome.test.mjs
requirements-parte7-lock.txt
requirements-parte7-proactivo.txt
requirements-parte7-pruebas.txt
requirements-parte7-reportes.txt
```
