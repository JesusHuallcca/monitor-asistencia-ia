# Matriz de variables — Parte 7 y backend integrado

Revisión estática: 2026-10-31, worktree monitor-asistencia-parte7, rama parte-7-chatbot-inteligente. No se consultaron valores efectivos de Render/Aiven, no se imprimieron contraseñas ni se exportó el entorno. Se comparó la configuración con origin/main disponible localmente (6557e65): los campos Settings son los mismos.

“Obligatoria” significa requisito operacional seguro; varias variables tienen defaults en código que NO deben utilizarse como credenciales de producción. La columna “Servicio” identifica al consumidor; no significa compartir todas las credenciales entre servicios. Usar cuentas MySQL distintas para web y worker.

## A. Variables que sí lee el backend: 24

| Nombre | Finalidad | Obligatoria / opcional | Servicio | ¿Secreto? / observaciones |
|---|---|---|---|---|
| DB_HOST | Host MySQL | Obligatoria explícita | Backend web y worker | No es contraseña, pero es configuración interna; no exponer públicamente. |
| DB_PORT | Puerto del servicio Aiven | Obligatoria explícita en cloud; existe default | Backend web y worker | No. No asumir el puerto local. |
| DB_NAME | Esquema existente | Obligatoria explícita | Backend web y worker | No; configuración interna. No crea una base. |
| DB_USER | Identidad técnica de conexión | Obligatoria explícita | Backend web y worker, usuarios separados | Identificador interno; tratar como configuración restringida. |
| DB_PASSWORD | Autenticación de MySQL | Obligatoria explícita | Backend web y worker | **Sí**. El respaldo heredado del código debe eliminarse. |
| JWT_SECRET_KEY | Firma de JWT, contexto temporal y pseudónimos de auditoría | Obligatoria segura | Backend web; worker también la usa para auditoría | **Sí**. El worker aún no exige su presencia en su gate inicial. No reutilizar la clave facial. |
| JWT_ALGORITHM | Algoritmo permitido al firmar/verificar | Opcional con default; fijar política | Backend web | No. No cambiar libremente por solicitud del cliente. Worker carga Settings, pero no firma tokens. |
| JWT_EXPIRE_MINUTES | Vigencia del access token | Opcional con default; fijar política | Backend web | No. No invalida por sí sola tokens ya emitidos. |
| FACE_ENCRYPTION_KEY | Cifrado Fernet de embeddings de rostros | Obligatoria si hay login/enrolamiento facial o datos cifrados que leer | Backend facial, **no** worker de Parte 7 ni frontend | **Sí, crítica para recuperación**. El código actual admite una sola clave. No cambiarla directamente. |
| FACE_THRESHOLD | Umbral de similitud facial | Opcional con default; preservar configuración validada | Backend facial | No. Parte 7 no lo usa ni requiere cambiarlo. |
| FACE_MODELS_DIR | Directorio de modelos faciales | Opcional con default; verificar ruta/artefactos | Backend facial | No. No es carpeta de reportes. |
| EMOSCAN_ENABLED | Habilita los servicios de expresiones existentes | Opcional con default; preservar decisión del módulo | Backend existente, no worker Parte 7 | No. No habilitarlo como parte de este despliegue. |
| EMOSCAN_MODEL_PATH | Ruta del ONNX de expresiones | Condicional si EmoScan está habilitado | Backend existente | No. Nunca conectar esos resultados al riesgo académico. |
| EMOSCAN_QUEUE_SIZE | Capacidad de cola de expresiones | Opcional con default | Backend existente | No. No es la cola del planificador académico. |
| EMOSCAN_JOB_TTL_SECONDS | Vencimiento de un trabajo de expresiones | Opcional con default | Backend existente | No. No controla los recordatorios. |
| EMOSCAN_RESULT_TTL_SECONDS | Vencimiento de resultados de expresiones | Opcional con default | Backend existente | No. No controla los documentos del chatbot. |
| EMOSCAN_MAX_RESULTS | Capacidad de resultados de expresiones | Opcional con default | Backend existente | No. No es límite de reportes. |
| GEMINI_API_KEY | API opcional de redacción sobre resultados autorizados | Condicional: solo si se habilita Gemini | **Backend web exclusivamente** | **Sí**. Nunca frontend, worker ni query string. |
| GEMINI_MODEL | Identificador de modelo Gemini | Condicional junto a GEMINI_API_KEY | Backend web | No. Verificar disponibilidad con el proveedor en staging autorizado. No se eligió un modelo ni se llamó la API. |
| APP_TIMEZONE | Zona IANA institucional para períodos, fechas y consultas | Configurar explícitamente; default existente | Backend web y worker, coherente | No. Las ejecuciones se guardan en UTC; la zona de cada recordatorio está en la BD. |
| CHATBOT_DEMO_MODE | Etiqueta de modalidad sintética | Opcional; mantener false/ausente en producción | Backend web y worker | No. **No sustituye autenticación ni activa un sandbox.** La demo aislada impone SQLite y bloquea MySQL por código aparte. |
| CHATBOT_INSTITUTIONAL_READ_USER_IDS | Concesión explícita de lectura a administradores institucionales | Opcional; vacío deniega a admin/superadmin | Backend web y worker para revalidar ámbito | No es clave; contiene IDs internos y requiere gestión restringida. Lista de enteros positivos; configuración malformada deniega. |
| CHATBOT_PROACTIVE_ENABLED | Permiso operacional de iniciar el worker | Obligatoria = true para iniciarlo | **Worker exclusivamente** | No. La API web no lee este gate: false en el web NO desactiva sus endpoints. |
| CHATBOT_PROACTIVE_MIGRATION_REVIEWED | Gate operacional tras revisión de migración | Obligatoria = true para iniciar el worker | **Worker exclusivamente** | No. No ejecuta ni valida toda la migración; el worker comprueba existencia de tablas. |

Fuentes: backend/app/core/config.py:16–49, backend/app/api/chatbot.py:68–99, backend/app/services/chatbot_security.py:14–40 y backend/parte7_worker.py:8–12.

Los 20 campos Settings se leen con pydantic-settings y env_file, extra=ignore. Las lecturas adicionales usan os.getenv/os.environ. Gemini se declara en Settings, pero el endpoint consulta os.getenv directamente: definirlo solamente en un archivo leído por pydantic no garantiza que el endpoint lo vea. En Render debe ser una variable real del proceso. La ruta del archivo local de configuración no se publica ni se modifica.

## B. Plataforma y frontend: no confundir con variables del backend

| Nombre/configuración | Finalidad | Obligatoria / opcional | Servicio | ¿Secreto? |
|---|---|---|---|---|
| PORT | Puerto de escucha consumido por el start command | Asignado por Render al web | Backend web y frontend si sigue como Node web | No. Worker no escucha un puerto. |
| PYTHON_VERSION | Selección del runtime de Render | Fijar una versión Python 3.12 compatible y probar la imagen final | Backend web y worker | No. No es un campo Settings. Prueba local: 3.12.10. |
| NODE_VERSION | Selección de Node en Render | Fijar si se conserva frontend Node web | Frontend | No. Herramientas locales probadas con Node 24.22.2. |
| WEB_CONCURRENCY | Default que puede consumir Uvicorn/plataforma | No necesario con --workers 1 explícito | Backend web | No. No usarlo para escalar reportes antes de externalizar la caché. |
| PYTHONPATH | Búsqueda de módulos app / backend.app | Definido por el start command propuesto | Backend web | No. |
| API_URL (localStorage del navegador) | Override público de dirección de API | Opcional; **NO es variable de entorno Render** | Navegador | No. El JS utiliza hostname y URLs públicas de respaldo. Nunca poner credenciales aquí. |

El frontend actual no consume VITE_API_URL, REACT_APP_API_URL ni una variable Render llamada API_URL. Añadirlas al panel no cambia frontend/js/config.js. Revisar el origen de API, CORS y retirar overrides locales de navegador en staging. No se modificó config.js.

Render documenta [PORT y las variables de runtime](https://render.com/docs/environment-variables).

## C. Nuevas variables por funcionalidad

- Gemini: GEMINI_API_KEY y GEMINI_MODEL ya están implementadas; solo son necesarias si se activa esa opción. El flujo local funciona sin ambas.
- Reportes: **no hay variables nuevas obligatorias**. TTL=600 s, 32 entradas, 24 MiB de caché, 8 MiB por archivo, dataset 2 MiB y dos renders simultáneos son constantes en chatbot_report_store.py. Definir REPORT_TTL o REPORTS_DIRECTORY en Render no cambia esos límites.
- Recordatorios y automatizaciones: los dos gates CHATBOT_PROACTIVE_* son del worker. APP_TIMEZONE y la concesión institucional deben ser coherentes. Destinatario, zona por acción, frecuencia y estado están en las tablas, no en variables por estudiante.
- No se necesita SMTP_PASSWORD, SMTP_HOST, Twilio, WhatsApp ni webhooks: no existe un transporte de mensajes externos y las comunicaciones son borradores.

## D. Propuestas necesarias para endurecer producción, NO implementadas

Estas variables son nombres propuestos para trabajo posterior. **El código actual las ignorará**; no basta con configurarlas en Render.

| Nombre propuesto | Finalidad | Necesidad | Servicio | ¿Secreto? |
|---|---|---|---|---|
| DB_SSL_CA | Ruta a la CA de Aiven montada como archivo administrado | Necesaria para introducir verificación TLS explícita en el engine | Backend web y worker | Ruta no secreta; certificado CA no es clave privada. |
| CORS_ALLOWED_ORIGINS | Sustituir orígenes genéricos por una allowlist institucional | Necesaria para endurecimiento | Backend web | No. |
| DB_AUTO_CREATE_SCHEMA | Gate, apagado en producción, para retirar DDL implícito del lifespan | Requiere primero implementar el control o eliminar esa llamada | Backend web | No. Hoy configurar false NO evita create_all. |
| FACE_ENCRYPTION_PREVIOUS_KEYS | Lectura temporal de claves anteriores durante una rotación | Condicional a implementar keyring/migrador y aprobar la rotación | Backend facial solamente | **Sí**. Hoy NO existe soporte. No cargarla aún como supuesto reemplazo seguro. |

Para escalar reportes sería necesario implementar almacenamiento compartido privado y limitación compartida, después definir su contrato de configuración. No se inventan ahora REDIS_URL/S3_* como si ya se utilizaran.

## E. Desarrollo y utilidades: no configurar en Render de producción

| Nombre | Lector / finalidad | Servicio | Secreto |
|---|---|---|---|
| MONITOR_TEST_NODE_MODULES | frontend/tests/parte7-tools.mjs; dependencias de prueba externas | Herramientas locales | No. |
| MONITOR_LIVE_DEMO_URL | Suites Chrome Parte 7; solo loopback | Herramientas locales | No. |
| SEGMENTATION_FIXTURE | frontend/tests/integracion-final.test.cjs; fixture de pruebas | Herramientas locales | No. |
| MPLCONFIGDIR | Script experimental sintético de segmentación; caché Matplotlib | Utilidad offline | No. |
| EMOSCAN_CAMERA_INDEX | Configuración del programa legado independiente de EmoScan | No participa del app.main revisado | No. |
| EMOSCAN_WEB_PORT | Puerto del programa legado independiente | No participa del app.main revisado | No. |
| EMOSCAN_DEBUG_MODE | Depuración del programa legado independiente | No participa del app.main revisado | No. |

Las tres últimas se generan mediante get_env_setting; no confundirlas con los seis campos EMOSCAN_* del backend. No se modificó ni se arrancó ese programa. No se enumeran como contrato del proyecto las variables internas de NumPy, TensorFlow, Node u otras bibliotecas; deben revisarse en la imagen final si se ajustan recursos.

## Gestión de secretos

Configurar secretos por servicio/entorno, fuera del repo y frontend, sin valores en comandos ni archivos de diagnóstico. El ejemplo de Render usa sync:false y autoDeployTrigger:off, sin conectarse a cuentas reales. sync:false es un marcador inicial; agregarlo a un Blueprint existente no reemplaza automáticamente secretos anteriores. Revisar ese comportamiento en la [referencia oficial](https://render.com/docs/blueprint-spec#prompting-for-secret-values).
