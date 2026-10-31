# Integración de Parte 7 con main: revisión vigente

Esta revisión sustituye como estado actual a los informes históricos de Parte 7. Esos informes y las propuestas YAML anteriores se conservan como evidencias de su fecha; NO son instrucciones listas para desplegar esta integración. No se modificaron cuentas Render, Aiven ni bases existentes.

## Ramas y alcance

Parte 7 publicada: parte-7-chatbot-inteligente, cuatro commits 458d933, eef7023, 369bc8f y ea76572.
Integración: integracion-parte7-main, creada desde origin/main 6557e65fdb3cf66b2f7e4f563c6b1fce891fe9c8. Se incorpora Parte 7 mediante merge exclusivamente en esta rama. main y los tres stash se conservan.

Las cinco fases permanecen conectadas al chatbot existente: ámbitos y auditoría, conversación/contexto/voz, reportes verificables XLSX/PDF/DOCX, adaptadores ML de consulta y recordatorios/borradores con worker. Se conserva el rediseño amplio, el botón flotante y las páginas recientes de main.

## Conflictos resueltos

| Archivo | Resolución |
|---|---|
| backend/app/services/chatbot_service.py | Consulta estructurada y permisos Parte 7; conservar intención de ausencias añadida en main. |
| frontend/components/chatbot.js | Componente Parte 7; sesión vencida por HTTP 401 y adaptación al dashboard actual. |
| frontend/estudiante/asistencia.html | Conservar página más reciente de main, incluida cámara dentro del navegador. |
| frontend/estudiante/ia.html | Mantener espacio conversacional amplio Parte 7. |
| frontend/js/panel-comun.js | Conservar rutas y páginas ML actuales de main; montaje idempotente del asistente, navegación responsive y exportación Panel. |

Solapamientos semánticos: backend/app/api/chatbot.py y frontend/js/chatbot-init.js. Se unifica la validación de roles con dependencia autenticada; ADMIN/SUPERADMIN necesitan además concesión institucional explícita. Se conserva montaje único y control de sesión. No se otorgan permisos desde el JWT ni desde Gemini.

Correcciones adicionales demostradas:
- DEFAULT_DATA: el servicio importaba desde el módulo de tres variables. Nuevo adaptador segmentacion/modelo_cuatro_variables.py reutiliza el algoritmo experimental definitivo de cuatro variables y cambia solamente la etiqueta de modalidad.
- Configuración Parte 6: retirar import de contraseña de respaldo eliminada; exigir contraseña explícita sin restaurar secretos.
- Cola EmoScan heredada: se recupera supervisión por proceso con deadline y cancelación. No cambia inferencia, modelo ni pesos; el cambio síncrono de main impedía recuperar un trabajo bloqueado.
- Pruebas antiguas de chatbot: JWT reales y SQLite con fixtures actuales; compilación INTEGER de BIGINT exclusivamente en SQLite de pruebas, sin migración de modelos MySQL.
- Listado general de asistencias de profesor: filtrar por cursos asignados y matrícula actual; revocación cubierta por prueba.
- CSV de perfiles: exigir declaración de origen sintético, rangos e IDs válidos y rechazar campos faciales; no asignar origen sintético a datos sin procedencia.
- Segmentación: restaurar contenedores y llamadas existentes de silueta, codo y mapa de calor retirados en main; ampliar solamente con botón, pues abrir modal al seleccionar un punto bloqueaba la interacción. No se modifican cálculos.

## Resultados y límites

- Publicación Parte 7 aislada: 260 pruebas backend aprobadas.
- Integración backend + Parte 6: 447 aprobadas, 1 omitida, 31 advertencias de deprecación. Evidencia PRUEBAS_BACKEND.xml.
- Inferencia TensorFlow real con fixture histórica autorizada; comparación con resultado del servicio y denegación después de revocar asignación. No se entrenó ningún modelo.
- Regresión Chrome Segmentación/EmoScan: 281 comprobaciones aprobadas con cámara explícitamente simulada. Incluye tres dispersores, centroides, filtros, tooltips extremos, CSV y consentimiento; no prueba cámara física.
- Chrome Parte 7: 583 comprobaciones contadas (336 páginas/navegación, 72 interfaz, 44 reportes, 42 proactividad, 60 ML, 29 espacio amplio); conversación contextual y voz simulada adicionales. Escritorio 1366x768, 1920x1080, tablet 820x1180 y móvil 390x844.
- Reportes reales descargados, abiertos/verificados con openpyxl, pypdf y python-docx; ejemplos sintéticos en docs/parte7/ejemplos.
- MySQL 8.0.46 temporal nativo: cinco tablas, claves foráneas/CHECK, rollback vacío, dos ejecuciones concurrentes sin duplicación y recuperación tras reconexión. MYSQL_DESARROLLO.json. Copia ESTRUCTURAL desde modelos versionados; no es un volcado ni validación del esquema real de Aiven.
- K-Means académico original: 7 pruebas aprobadas, sin modificar sus tres variables. El adaptador de cuatro variables conserva 150 perfiles, K=3 y silueta 0.2373692496101911.
- pip check: sin dependencias rotas en Python 3.12.10 Windows, TensorFlow 2.20.0, Keras 3.15.1, NumPy 2.2.6, Pandas 2.3.3, sklearn 1.7.2 y FastAPI 0.119.1. Linux Render pendiente.
- No se probó cámara/micrófono físicos, Gemini real ni correos externos. Una prueba real ONNX se omite por artefactos de prueba ausentes. La voz y cámara simuladas se identifican como tales.

## Clasificación de fallos

Los 25 errores originales fueron dos importaciones DEFAULT_DATA, una importación obsoleta de face_repository y 22 errores de fixtures antiguas. Los tres fallos originales de EmoScan correspondían a archivos públicos/modelo ausentes y al bloqueo de la cola heredada. No eran fallos del clasificador de intenciones Parte 7. La prueba manual de repositorio facial sigue requiriendo revisión separada; no se restaura el acceso legado inseguro a DB.

En la integración aparecieron incompatibilidades nuevas de configuración de Parte 6, roles compartidos y diseño responsive: corregidas y cubiertas por las pruebas anteriores.

Pendiente: test_original_files_unchanged del experimento reporta cuatro discrepancias respecto de un manifiesto histórico (CSV de evaluación, métricas, asignaciones y PNG) ya cambiado en main. Los demás nueve métodos pasan. No se cambió el manifiesto ni se eliminó esa comprobación: autorización de actualización rechazada. Requiere revisión del propietario y una prueba de inmutabilidad de la ejecución, sin modificar algoritmos.


## Migraciones MySQL pendientes de producción

Archivo: database/mysql/migrations/parte7/001_proactividad_additive.sql.
Cinco tablas nuevas: chatbot_proactive_actions, chatbot_proactive_preferences, chatbot_proactive_notifications, chatbot_proactive_audit, chatbot_proactive_worker. SQLAlchemy coincide con estas tablas.

No ejecutar CREATE DATABASE, DROP, TRUNCATE ni create_all contra Aiven. El responsable debe comparar primero el esquema real (usuarios, cursos, estudiantes y referencias; tipos, signedness, índices, collation y versión) con la copia estructural probada. Repetir la migración sobre un clon autorizado y cifrado, y verificar tablas previas intactas. No contiene IF NOT EXISTS: registrar su aplicación una sola vez; una repetición debe ser revisada, no ignorada.

Rollback lógico: detener worker y deshabilitar exposición de funciones nuevas, conservando las tablas/datos. No borrar acciones/notificaciones para volver atrás. Rollback físico probado solamente en copia vacía, en orden dependiente: notifications, audit, worker, preferences, actions; rechazar si contienen datos. Producción requiere aprobación y respaldo previo del responsable.

## Variables efectivamente consumidas: matriz vigente

La matriz anterior es histórica: DB_SSL_CA, DB_SSL_REQUIRED y CORS_ALLOWED_ORIGINS ya están implementadas; el arranque ya no hace DDL ni descarga modelos y el worker ahora exige JWT explícito.

| Variable | Uso | Obligatoria | Servicio | Secreto |
|---|---|---|---|---|
| DB_HOST | Host del esquema existente | Sí | Web/worker | No |
| DB_PORT | Puerto Aiven | Sí | Web/worker | No |
| DB_NAME | Base existente | Sí | Web/worker | No |
| DB_USER | Cuenta restringida por servicio | Sí | Web/worker | Identidad interna |
| DB_PASSWORD | Autenticación | Sí | Web/worker | Sí |
| DB_SSL_CA | Ruta del certificado CA montado | Sí para Aiven | Web/worker | No, no es una clave privada |
| DB_SSL_REQUIRED | Exigir TLS | true en cloud | Web/worker | No |
| JWT_SECRET_KEY | Firma/contexto/auditoría | Sí | Web/worker | Sí |
| JWT_ALGORITHM | Algoritmo permitido | Opcional; mantener política HS256 | Web | No |
| JWT_EXPIRE_MINUTES | Duración token | Opcional | Web | No |
| CORS_ALLOWED_ORIGINS | Lista de orígenes exactos, separados por comas | Configurar en cloud | Web | No |
| FACE_ENCRYPTION_KEY | Descifrar/cifrar embeddings existentes | Si se usa facial | Web; nunca worker | Sí, preservar recuperación |
| FACE_THRESHOLD | Umbral facial existente | Opcional; conservar | Web | No |
| FACE_MODELS_DIR | Ruta YuNet/SFace provisionados | Condicional | Web | No |
| EMOSCAN_ENABLED | Política existente, no activar por Parte 7 | Opcional | Web | No |
| EMOSCAN_MODEL_PATH | Ruta FERPlus ONNX | Si está habilitado | Web | No |
| EMOSCAN_QUEUE_SIZE | Capacidad cola | Opcional | Web | No |
| EMOSCAN_JOB_TTL_SECONDS | Deadline trabajo | Opcional | Web | No |
| EMOSCAN_RESULT_TTL_SECONDS | Caducidad resultado | Opcional | Web | No |
| EMOSCAN_MAX_RESULTS | Capacidad resultados | Opcional | Web | No |
| GEMINI_API_KEY | Redacción opcional autorizada | Solo al habilitar Gemini | Web | Sí |
| GEMINI_MODEL | Modelo del proveedor disponible | Junto con API key | Web | No |
| APP_TIMEZONE | Zona institucional IANA | Coherente; America/Lima | Web/worker | No |
| CHATBOT_DEMO_MODE | Etiqueta de origen, NO sandbox | false en cloud | Web/worker | No |
| CHATBOT_INSTITUTIONAL_READ_USER_IDS | Concesión explícita admin/superadmin | Vacío deniega acceso institucional | Web/worker | IDs internos restringidos |
| CHATBOT_PROACTIVE_ENABLED | Gate de arranque | true solo tras aprobación | Worker | No |
| CHATBOT_PROACTIVE_MIGRATION_REVIEWED | Gate migración revisada | true tras validación manual | Worker | No |

PORT lo consume el comando web de Render; PYTHON_VERSION selecciona Python 3.12; NODE_VERSION selecciona Node. No son campos de Settings.
PARTE6_ALLOW_DEV_DB pertenece únicamente al servidor standalone local Parte 6; no habilitarlo para el main cloud.
API_URL es override público de localStorage, NO variable Render consumida por el frontend actual. No poner secretos en frontend/js/config.js.
DB_AUTO_CREATE_SCHEMA y FACE_ENCRYPTION_PREVIOUS_KEYS no están implementadas. No configurarlas esperando comportamiento.
Reportes no requieren ruta persistente ni SMTP, Redis o S3 actualmente. Sus límites son constantes, no variables inventadas.

## Worker y reportes

Recomendación: un Background Worker dedicado, no Cron Job. El proceso BlockingScheduler no finaliza y consulta cada 30 segundos. Cron requeriría un comando de una pasada que todavía no existe. Referencias: [workers Render](https://render.com/docs/background-workers), [Cron Jobs](https://render.com/docs/cronjobs).

Una instancia, max_instances=1, coalesce y transacciones con SELECT FOR UPDATE. UNIQUE de identidad de acción y clave de ejecución; next_run, estado y notificación se confirman juntos. MySQL temporal probó carreras y reinicio sin duplicar. La tabla worker aporta estado, no una elección de líder distribuido ni un servicio de alta disponibilidad. No se promete reproducir todos los períodos omitidos durante una caída: revisar alertas y ventanas pendientes. Chrome puede estar cerrado.

Solo notificaciones internas; comunicaciones permanecen en draft/reviewed. No hay transporte a terceros ni decisiones disciplinarias.

Reportes web: memoria privada por usuario, TTL 600 segundos, 32 entradas, 24 MiB globales y 8 MiB por documento; un proceso y una instancia. Reiniciar invalida enlaces temporales: regenerar con autorización. Los reportes programados guardan dataset en MySQL y se renderizan al solicitar descarga, sin depender de disco persistente. Para escalar a varias réplicas hace falta almacenamiento privado y cuotas compartidas antes.

## Pasos exactos para el responsable en Render (NO ejecutados)

1. Mantener despliegue automático apagado en los servicios existentes mientras el PR esté en borrador. No sincronizar los YAML históricos como Blueprint.
2. Resolver las pruebas pendientes y aprobar el PR; después integrar mediante el proceso habitual, sin este agente haciendo merge. Crear staging con recursos y credenciales propios; nunca apuntarlo a producción por defecto.
3. Respaldar esquema/datos y embeddings cifrados de Aiven mediante procedimiento del propietario. Inventariar fecha/clave usada sin imprimirla. Comparar y probar migración en clon autorizado.
4. Configurar Python 3.12 en backend. Desde raíz, build: python -m pip install -r requirements-integracion-parte7.txt. Ejecutar pip check y pruebas en Linux antes de promover. El archivo usa tensorflow en Windows y tensorflow-cpu en Linux; no instalar ambos.
5. Provisionar explícitamente los artefactos faciales de confianza antes del start: FACE_MODELS_DIR debe contener face_detection_yunet_2023mar.onnx y face_recognition_sface_2021dec.onnx; verificar procedencia/checksum/licencia. Si EmoScan está habilitado, provisionar también su ONNX. No guardarlos en este PR ni descargarlos desde lifespan. Falta validar este paso en imagen Linux; sin él reconocimiento facial responde no disponible.
6. Montar CA Aiven como archivo administrado (por ejemplo /etc/secrets/aiven-ca.pem); DB_SSL_CA apunta a ese archivo, DB_SSL_REQUIRED=true. Configurar DB_* con cuenta web sin DDL y CORS_ALLOWED_ORIGINS con URL exacta del frontend. Introducir secretos en panel seguro, nunca comandos/chat/logs. JWT debe tener entropía suficiente.
7. Backend start desde raíz: PYTHONPATH=.:backend python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "$PORT" --workers 1. Una instancia. Health /api/health comprueba vida, NO readiness de DB. Probar por separado login, roles y conexión TLS autorizada.
8. Frontend existente: rootDir frontend; build npm ci --omit=dev; start npm start. Verificar frontend/js/config.js y el dominio real; limpiar overrides API_URL del navegador de staging. No añadir variables VITE_* que este frontend no lee.
9. Tras revisión de clon y ventana aprobada, el propietario aplica una sola vez la migración aditiva con cuenta administrativa separada. Web/worker conservan cuentas sin permisos DDL; no hay preDeployCommand de migración automática.
10. Crear un Background Worker dedicado: build python -m pip install -r requirements-parte7-proactivo.txt; start python backend/parte7_worker.py. Una instancia. Configurar cuenta MySQL worker, CA/TLS, JWT, zona y concesiones necesarias. Poner ambos gates CHATBOT_PROACTIVE_* en true solamente tras migración revisada.
11. Medir RSS y picos con TensorFlow, ONNX y exportaciones concurrentes en Linux. Los 157 MiB de la antigua demo NO incluyen TensorFlow/ONNX; no justifican un plan de 512 MiB. Presupuestar staging con margen (p. ej. 2 GiB provisional) y ajustar con mediciones. Limitar hilos si las mediciones lo requieren; no afirmar capacidad sin carga.
12. Smoke tests: login por cada rol; rechazo cruzado de cursos/IDs; descarga ajena denegada; tres formatos; clase/fecha existente; reminder con navegador cerrado; reiniciar worker y verificar una notificación; comunicación sin envío; modelos existentes y cámara con consentimiento. Verificar que ningún log muestre SQL/secretos.
13. Solo promover después de autorización, resolver pendientes y resultados de staging. No se realizó despliegue durante este trabajo.

## Secretos y reversión

Las credenciales heredadas de conexión, JWT y clave facial se retiraron del árbol actual, no del historial público. La limpieza del código NO revoca secretos: propietario debe rotarlos en los proveedores y revisar accesos. No se publican valores ni copias nuevas.

JWT: acordar renovación simultánea web/worker; invalidará sesiones y contexto temporal, exigir nuevo login. MySQL: crear cuenta nueva restringida, probar TLS, cambiar servicios coordinadamente y revocar la cuenta expuesta después de comprobarlos.

Facial: NO reemplazar de golpe FACE_ENCRYPTION_KEY. No existe keyring/migrador de producción implementado. Respaldar ciphertext y clave anterior en gestor seguro; preparar y probar migración o lectura multiclave en copia, verificar descifrado antes/después y recuperación de backup; luego coordinar cambio. Es un bloqueo externo de seguridad, no una rotación ya completada.

Rollback: detener worker, conservar tablas y evidencia, volver a versión aprobada SANITIZADA compatible; no restaurar binarios con secretos públicos ni lifespan con DDL. La versión anterior no necesariamente entiende cambios criptográficos: conservar ruta comprobada de recuperación. No usar rollback que pierda nuevas acciones o embeddings. No ejecutar DROP en producción.

## Estado de aprobación

PR de integración en BORRADOR: no aprobado para producción. Pendientes mínimos: manifiesto histórico de integridad, validación Linux/Render y artefactos faciales, esquema real Aiven/clon y rotación coordinada de secretos. No hubo merge a main, despliegue, modificación de variables Render ni migración de producción.
