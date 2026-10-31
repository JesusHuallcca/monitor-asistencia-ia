# Guía de preparación de despliegue — Parte 7

Estado: **PROPUESTA LOCAL, NO APLICAR A PRODUCCIÓN TODAVÍA**.
Revisión: 2026-10-31. Worktree monitor-asistencia-parte7, rama parte-7-chatbot-inteligente.

No se conectó Aiven, no se consultaron variables privadas de Render, no se aplicaron migraciones, no se hizo merge/commit/push ni se desplegó. La revisión utiliza código local y documentación pública oficial. No prueba que la configuración efectiva del proveedor coincida con la del repositorio.

Archivos de esta preparación:

- MATRIZ_VARIABLES.md: 24 variables efectivamente leídas por el backend; plataforma, frontend, utilidades y propuestas separadas.
- render-parte7.propuesta.yaml: ejemplo de tres servicios con despliegue automático apagado; no sustituye render.yaml.
- PRECHECK_LOCAL.json: resultado reproducible de memoria, exportación y estrategia criptográfica sintética.
- backend/parte7_deployment_check.py: ejecuta ese chequeo aislado, sin app.main ni conexión MySQL.

Consultar también ../AUDITORIA_PUBLICACION.md: registra los bloqueos heredados y las pruebas previas.

## 1. Decisión de arquitectura

Conservar el backend FastAPI y el frontend existentes. Agregar **un Render Background Worker dedicado** para python backend/parte7_worker.py. No ejecutar un planificador dentro de cada proceso Uvicorn. Mantener inicialmente un proceso web y una réplica web por la caché privada de reportes en memoria.

El worker actual usa BlockingScheduler y consulta las acciones cada 30 segundos; está diseñado para permanecer en ejecución. Render describe [Background Workers](https://render.com/docs/background-workers) como servicios continuos. Sus [Cron Jobs](https://render.com/docs/cronjobs) requieren comandos que finalicen: usar el worker actual como cron no es compatible. Para cron habría que desarrollar un comando de una sola pasada, definir retraso admisible y revisar recuperación; no se implementó ni se recomienda como reemplazo directo.

Las fechas de negocio están en MySQL y la agenda usa zonas IANA/UTC, no la zona del navegador. No hay transporte de comunicaciones externas; aprobar una comunicación solo produce un borrador reviewed.

## 2. Bloqueos previos al despliegue

1. Retirar/rotar JWT estático en render.yaml y eliminar credenciales de respaldo del código, incluida la contraseña codificada. No copiar esos valores a nuevos archivos ni confiar en que Base64 los proteja.
2. Corregir /api/health y el manejador de errores: no devolver partes de contraseña, host, usuario, SQL ni excepciones internas. Como liveness propuesto se usa /api/attendance/health, que actualmente solo devuelve estado/módulo. No verifica readiness de Aiven.
3. Corregir el ámbito del listado general de asistencias para profesores; el chatbot tiene ámbitos propios, pero esa ruta heredada usa get_all sin cursos asignados.
4. Retirar el create_all del arranque o introducir un gate real apagado en producción. Hoy una variable DB_AUTO_CREATE_SCHEMA=false no hace nada. El usuario web/worker de ejecución no debe tener DDL.
5. Introducir TLS verificable y retirar defaults de conexión; exigir configuración explícita. El engine actual solo pasa pool_pre_ping, sin configuración ssl explícita.
6. Reconciliar los seis archivos compartidos con origin/main (referencia local 6557e65), que avanzó dos commits e integró Parte 6 y frontend responsive. No se realizó esa integración. Validar dependencias conjuntas con TensorFlow.
7. Recuperar el harness de las pruebas heredadas: su último intento produjo dos errores por fixture client inexistente y se detuvo. No declarar aprobada la suite global.
8. Revisar que el worker exija también JWT_SECRET_KEY explícita; actualmente sus gates iniciales solo exigen DB y las dos confirmaciones de proactividad.

No se ejecutó la aplicación de producción para “comprobar” estos problemas: su lifespan intenta DDL y descargas. La existencia de pruebas Parte 7 aprobadas no elimina estos bloqueos.

## 3. Configuración de Render propuesta

Los comandos siguientes son para el futuro entorno Linux de staging, con raíz del repositorio. No se ejecutaron en Render.

| Servicio | Build | Start |
|---|---|---|
| Backend FastAPI | python -m pip install -r requirements.txt -r requirements-parte7-proactivo.txt | PYTHONPATH=.:backend python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "$PORT" --workers 1 |
| Worker Parte 7 | python -m pip install -r requirements-parte7-proactivo.txt | python backend/parte7_worker.py |
| Frontend Node, rootDir=frontend | npm ci --omit=dev | npm start |

El ejemplo usa nombres diferentes de los servicios existentes, branch explícita y autoDeployTrigger:"off". Es una referencia de configuración, no una instrucción para crear tres servicios adicionales en la cuenta actual. Reutilizar los servicios existentes requiere revisión del propietario; esta preparación no cambió ninguno.

Elegir Python 3.12 con patch disponible y validado en la imagen final; prueba local 3.12.10. Fijar Node si se conserva el frontend como web Node; herramienta local 24.22.2. No fijar credenciales con value ni generar una clave facial al azar durante cada build.

No agregar preDeployCommand, ejecución de SQL, seeding ni descargas de datos de alumnos. No usar --reload en producción. El worker no necesita PORT, clave facial ni Gemini. No asociar una cuenta MySQL de administrador global a los servicios.

La propuesta no cambia la modalidad actual del frontend a static site. Sus URLs de API se resuelven en frontend/js/config.js y localStorage; configurar API_URL en Render no las reescribe. Verificar el dominio backend real autorizado y CORS con Chrome; nunca publicar una credencial en JavaScript.

El YAML usa solo marcadores privados sync:false. Para un servicio ya existente, esos marcadores no actualizan automáticamente secretos anteriores. Ver [Blueprint reference](https://render.com/docs/blueprint-spec#prompting-for-secret-values). No se validó contra una cuenta real ni se sincronizó.

## 4. Dependencias, artefactos y memoria

requirements.txt actual no incluye openpyxl, reportlab, python-docx ni APScheduler; por eso el build web propuesto combina ambos requirements. El worker instala el conjunto Parte 7, sin TensorFlow ni motores faciales. requirements-parte7-lock.txt registra el entorno aislado probado; no es un lock conjunto certificado con main/TensorFlow ni un lock Linux.

Comprobaciones mínimas en un build de staging:

    python -m pip check
    python -m pytest backend/tests/parte7 -q -p no:cacheprovider --tb=short

Instalar requirements-parte7-pruebas.txt solo en el entorno de pruebas. Instalar devDependencies del frontend para Chrome, no para servir archivos estáticos. Fijar luego un lock conjunto, comprobar ruedas Linux, versiones NumPy/Pandas/scikit-learn, TensorFlow/Keras y las versiones con que se guardaron los artefactos ML. No reentrenar ni convertir modelos durante deploy.

Los modelos faciales y los resultados ML guardados deben estar disponibles en rutas verificadas antes de readiness. El main heredado intenta descargar un ONNX al arrancar: revisar ese comportamiento y aprovisionar artefactos con origen/hash aprobados en build, sin incluir nuevos modelos descargados en el commit de Parte 7.

### Medición local realizada

Ejecutar desde el worktree, usando el Python de pruebas:

    python -B backend/parte7_deployment_check.py

Resultado Windows/Python 3.12.10:

- Importación de la demo integrada: working set 129.71 MiB.
- Tras vista previa autorizada de 8 registros y XLSX/PDF/DOCX: working set 157.07 MiB, pico observado 157.43 MiB.
- MySQL bloqueado; sin TensorFlow, ONNX, Chrome, carga máxima ni exportaciones simultáneas.

Estos valores NO dimensionan la aplicación completa en Linux. La caché de 24 MiB limita el contenido almacenado, no el RSS total: JSON deserializado, tablas, librerías y buffers temporales ocupan memoria adicional. Dos renders pueden coexistir; no duplicar procesos web antes de externalizar estado.

Como hipótesis de capacidad para validar, reservar un presupuesto inicial de 2 GiB al web si carga TensorFlow y visión, y 512 MiB al worker aislado. No son mínimos medidos ni garantías de suficiencia; escoger el plan final solo después del ensayo Linux. La propuesta YAML no selecciona ni contrata un plan.

Medir en el contenedor final: RSS base y pico, dos exportaciones de 2000 filas, 32 snapshots hasta el límite global, consultas ML, concurrencia y cola de 50 acciones por ciclo; confirmar margen operacional (objetivo inicial: pico <70% de memoria asignada), ausencia de OOM/exit 137 y latencias aceptadas. Probar límites 413/429/503 sin agotar memoria.

El pool SQLAlchemy no está dimensionado explícitamente. Contabilizar conexiones por proceso, worker, reinicios y otros módulos contra el límite del plan Aiven. Configurar pool/timeouts al implementar el endurecimiento; no aumentar conexiones indiscriminadamente.

## 5. MySQL y migraciones aditivas

Migración pendiente: database/mysql/migrations/parte7/001_proactividad_additive.sql.

| Tabla | Finalidad | Restricciones importantes |
|---|---|---|
| chatbot_proactive_actions | Acción, propietario/destinatario, zona, estado, versión y agenda UTC | Identidad única; índice status/next_run; FK académicas; owner=recipient. |
| chatbot_proactive_preferences | Preferencias de la cuenta | PK/FK owner_id. |
| chatbot_proactive_notifications | Resultado privado y estado | execution_key único, FK de acción/propietario y vencimiento. |
| chatbot_proactive_audit | Evento mínimo | Referencia al propietario, sin contenido privado de consultas. |
| chatbot_proactive_worker | Latido UTC | Una fila del worker lógico main. |

La inspección estática confirma cinco CREATE TABLE, sin ALTER/DROP/TRUNCATE ni escrituras en tablas previas; las columnas coinciden con ProactiveBase. La API solo comprueba existencia de tablas, no equivalencia exhaustiva de esquema.

El ORM utiliza metadatos aislados y Text; la propuesta MySQL usa MEDIUMTEXT para configuraciones/snapshots e incluye FK/CHECK no declaradas en esos metadatos. No usar create_all de ProactiveBase para sustituir la migración en MySQL. Revisar el esquema real: INT signed, InnoDB, collation/charset, claves foráneas, soportes CHECK, tamaños y tipos. No se comprobó la versión real de Aiven.

Comprobar las tablas académicas y chat_historial ya existentes. database/mysql/05_chatbot.sql es una propuesta previa CREATE IF NOT EXISTS: revisarla solo si esas tablas faltan, sin recrear las presentes. No ejecutar 01_schema.sql ni 02_seed.sql sobre la base existente; el primero contiene DROP TABLE.

Procedimiento de staging, con revisión humana:

1. Obtener solo estructura autorizada y un respaldo con procedimiento de restauración comprobado; no copiar datos reales a este worktree.
2. Verificar qué tablas faltan. Registrar aprobación y versión de migración.
3. Aplicar únicamente la propuesta aprobada con cuenta técnica de migración en desarrollo, fuera del arranque web.
4. Si falla parcialmente, inspeccionar y reconciliar la estructura: MySQL DDL no debe suponerse una transacción completamente reversible. El script CREATE sin IF NOT EXISTS no es un mecanismo de reintento automático.
5. Probar los cinco modelos, tamaños, constraints, transacciones, bloqueo de fila, concurrencia y reinicio contra MySQL de desarrollo.
6. Retirar DDL de las cuentas runtime y habilitar los gates del worker solo después de aprobar.

Permisos propuestos: web conserva los permisos académicos ya necesarios y añade los específicos de Parte 7; worker solo SELECT de usuarios, cursos, profesores/asignaciones, estudiantes/matrículas, sesiones, asistencias, evaluaciones y notas, más las operaciones mínimas de sus tablas propias. El worker lee preferencias, actualiza acciones/latido, inserta notificaciones/auditoría y elimina únicamente filas vencidas de su módulo. Revisar grants concretos sin usar avnadmin para runtime.

## 6. Aiven, TLS y credenciales

El código usa DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD; no lee DATABASE_URL del entorno. Construye la URL internamente. Hay que retirar el respaldo de contraseña y el reemplazo de usuario heredados antes de introducir nuevas credenciales.

Propuesta pendiente de código: añadir una ruta DB_SSL_CA y crear el engine con ssl_ca, ssl_verify_cert=True y ssl_verify_identity=True, más timeouts acotados. El certificado CA debe montarse como archivo administrado y verificarse; no es una clave privada. No usar ssl_disabled ni desactivar validación para resolver errores.

Aiven explica la CA y la diferencia entre verificar emisor/identidad en [TLS certificates](https://aiven.io/docs/platform/concepts/tls-ssl-certificates). Los parámetros concretos de PyMySQL se documentan en [Connection](https://pymysql.readthedocs.io/en/latest/modules/connections.html). Este documento no ejecuta el ejemplo de conexión del proveedor, porque incluye creación/escritura de tablas.

En staging: confirmar cifrado negociado sin registrar DSN, comprobar rechazo con CA incorrecta/hostname incorrecto y verificar conexión con CA vigente. Preparar actualización del bundle cuando el proveedor rote su CA. Guardar únicamente resultados de estado, nunca passwords o variables completas.

### Rotación MySQL

Con el propietario autorizado:

1. Preparar un usuario nuevo limitado por servicio en desarrollo; no cambiar la contraseña de una cuenta compartida sin inventariar consumidores.
2. Registrar la versión de la credencial en un gestor seguro, configurar web/worker de staging, reiniciar pools y verificar permisos.
3. Planificar el corte de todos los consumidores, incluidos jobs y servicios anteriores. Confirmar conexiones nuevas.
4. Revocar la credencial anterior tras el corte verificado. Si se considera comprometida, priorizar contención y no mantenerla activa por comodidad.
5. Probar que el usuario anterior ya no autentica. No registrar intentos con la contraseña.
6. Rollback de código conserva la credencial nueva y sus permisos; **no reactivar una contraseña comprometida**. Reparar compatibilidad o preparar otra cuenta autorizada si fuera necesario.

El proveedor permite [usuarios de servicio](https://aiven.io/docs/products/mysql/howto/manage-service-users). No se creó ni modificó ninguno durante esta tarea.

## 7. Rotación JWT

El proyecto firma/verifica con una sola JWT_SECRET_KEY. No hay kid/keyring ni verificación simultánea de claves antiguas. El contexto temporal deriva su firma de esa clave; la rotación invalida tokens de acceso y contexto. El historial en MySQL no se cifra con ella y no desaparece.

Para una clave expuesta: emitir una nueva clave segura mediante el gestor autorizado, desplegar la configuración coordinadamente en todos los procesos que validan tokens y forzar nuevo login; no mantener la clave comprometida como fallback. Probar 401 con JWT anterior y éxito con login nuevo, rechazo del contexto anterior y aislamiento por rol. Revisar los errores de contexto sin filtrar detalles.

Mantener consistencia de la política y la clave entre servicios que la usan; el worker emplea JWT_SECRET_KEY para pseudónimos de auditoría, no necesita emitir tokens. El cambio de pseudónimos de logs es esperado. No usar JWT_ALGORITHM como mecanismo de recuperación ni aceptar algoritmos indicados por el cliente.

Para rotación rutinaria sin logout sería necesario implementar y probar un esquema de versionado/validación acotada, hoy inexistente. No reutilizar la clave de cifrado facial para JWT.

## 8. Rotación facial preservando recuperación

Implementación actual: backend/app/core/face_crypto.py usa Fernet(settings.FACE_ENCRYPTION_KEY) para escribir y leer rostros.embedding, LargeBinary. No guarda key_id ni admite claves anteriores. **Reemplazar directamente FACE_ENCRYPTION_KEY rompe la lectura del contenido previo.** Cambiar JWT o contraseña MySQL no vuelve a cifrar los embeddings.

Procedimiento propuesto, pendiente de implementación y aprobación del responsable facial:

1. Custodiar por separado una copia de seguridad cifrada de la BD y la clave con la que fue cifrada, en un gestor restringido y con registro de versiones. Probar restauración/descifrado en entorno autorizado. No exportar embeddings en claro ni claves a Git/logs.
2. Desarrollar y probar primero un lector de transición con la nueva y la anterior, compatible con la recuperación de respaldos. MultiFernet permite cifrar con la primera y descifrar con varias; ver [documentación oficial](https://cryptography.io/en/latest/fernet/). Hoy no está integrado.
3. Si no hay keyring confiable, realizar una ventana de mantenimiento: suspender enrolamiento, actualización y login facial; mantener login por contraseña. Evitar escritores antiguos durante el cambio.
4. Migrar ciphertext por lotes transaccionales a la clave nueva usando una herramienta autorizada, con checkpoint/versionado y validación en memoria del vector antes/después. Registrar cantidades/estado, no datos biométricos. Nunca tratar como “completado” un blob que no pudo descifrarse.
5. Comprobar que todas las filas válidas, incluido contenido inactivo aún retenido, se leen con la clave nueva. Probar backups y recuperación con su combinación correcta de ciphertext/clave.
6. Habilitar escritura nueva y actualizar el runtime de forma coordinada. Cuando no quede contenido que dependa de la antigua, retirarla del entorno activo; conservarla bajo custodia mientras existan respaldos válidos que la requieran, según retención y política.
7. Rollback: después de recifrar, una app con la clave antigua sola NO leerá las filas nuevas. Reutilizar un lector compatible y la clave nueva; una restauración de backup requiere su clave correspondiente y aprobación por posible pérdida de cambios posteriores.

Una clave perdida no se recupera a partir de la base de datos. Si no existe una copia autorizada, debe deshabilitarse ese login y planificar un nuevo enrolamiento voluntario; no declarar recuperación ficticia. Si hubo exposición de clave/ciphertext, la rotación no elimina copias ya obtenidas.

Se comprobó únicamente la estrategia en memoria con claves efímeras y texto sintético: nueva sola rechaza ciphertext viejo, MultiFernet.rotate produce ciphertext legible con nueva y el respaldo antiguo sigue legible con antigua. No se modificó el módulo facial ni se probaron datos de estudiantes.

## 9. Planificador: duplicados, concurrencia y reinicios

- Identidad única por propietario/configuración evita duplicar borradores; clases/evaluaciones usan identidad por fuente. Editar es una revisión con control de versión.
- execution_key único identifica acción/hora programada. Se usa SELECT ... FOR UPDATE en la ejecución y notificación/avance de agenda se guardan en la misma transacción.
- Antes del commit, un reinicio deja la transacción sin confirmar para su rollback; después del commit, la agenda ya avanzó y no debe repetirse esa ejecución. Dos procesos pueden coincidir durante un reemplazo de deploy; las restricciones y locks deben validarse en MySQL.
- Solo una instancia dedicada como diseño normal. max_instances=1 y coalesce son controles dentro del proceso; **no son locks distribuidos**. La seguridad entre procesos la aportan las transacciones/constraints.
- Al iniciar, se vuelve a consultar next_run vencido en la BD, hasta 50 acciones por ciclo. No hay agenda duradera en el navegador ni un job store compartido de APScheduler.
- Recuperación tiene límites: una clase/evento ya pasado se bloquea para revisión; un reporte recurrente atrasado usa el último período institucional cerrado respecto de la ejecución actual, no reconstruye cada semana perdida. No prometer backfill completo.
- Errores por acción pueden dejar estado blocked: no existe un retry exponencial ni una cola de fallidos automática. La corrección y reactivación son revisadas. Errores globales de almacenamiento se registran saneados y otro ciclo vuelve a consultar.
- El latido se actualiza por ciclo; una antigüedad mayor a 120 s muestra worker sin actividad. Un proceso vivo no garantiza salud de cada acción.
- Notificaciones/snapshots vencen a 30 días; auditoría mínima a 90. La limpieza solo afecta tablas del módulo. Las alertas no repiten un conjunto sin cambios, pero nuevos registros pueden justificar otro aviso.
- Antes de producción, ensayar SIGTERM en staging y cierre ordenado del scheduler/pool. El CLI actual no implementa un handler propio de apagado. No marcarlo como probado por haber aprobado un test SQLite.

El test local de concurrencia/reinicio usa SQLite de archivo; las garantías MySQL requieren ensayo InnoDB real en desarrollo. No hay efectos externos previos al commit.

## 10. Reportes sin disco persistente

La vista previa conserva dataset serializado y su SHA en ReportStore RAM: propietario, huella del ámbito actual y TTL de 600 s. Los archivos se generan en BytesIO, se almacenan temporalmente como bytes y se entregan mediante Response autenticada. XLSX usa openpyxl, PDF ReportLab y Word python-docx. No hay un directorio público de descargas.

Cada generación/lectura/descarga revalida identidad y ámbito; hay límites por cuenta, protección de fórmulas, límites de filas/fechas/tamaño y Cache-Control:no-store, private. El frontend descarga el blob autorizado y puede imprimir el PDF. Nunca autenticar con un token permanente en la URL.

Un reinicio o cambio de réplica pierde previews/archivos y requiere regenerarlos; no pierde datos académicos. El worker guarda un snapshot privado del reporte en MySQL y la API web crea su vista previa al abrirlo. No intenta compartir la RAM del worker con la del web.

Con varias réplicas/procesos web la descarga puede llegar a una caché distinta y las cuotas quedan fragmentadas. Hasta implementar almacenamiento/limitación compartidos, usar una instancia y --workers 1. También hay que considerar el solapamiento de instancias durante un deploy: las previews vigentes pueden necesitar regeneración. No añadir un disco para “arreglar” esta afinidad.

Los seis archivos de docs/parte7/ejemplos son evidencia deliberadamente sintética para revisión; el programa de producción no guarda documentos de alumnos allí.

## 11. Pruebas previas y secuencia de habilitación

### Ejecutadas en esta preparación

- 256 pruebas Parte 7 aprobadas de nuevo, 1 aviso de deprecación TestClient/httpx; pip check sin conflictos.
- Chequeo local reproducible: tres descargas reales autorizadas, hashes correctos, memoria registrada y estrategia de rotación efímera aprobada.
- Matriz contrastada con los 20 campos Settings y las cuatro lecturas extra de producción; variables dinámicas identificadas.
- Revisión estática ORM/SQL, límites, recuperaciones y arranque. No es prueba de MySQL ni de Render.
- Las pruebas Chrome de la auditoría anterior registraron 218 comprobaciones más voz/conversación. No se volvieron a ejecutar aquí porque no se cambió frontend ni runtime; no se presentan como una ejecución nueva.

### Puertas de aprobación pendientes

1. Corregir los bloqueos de seguridad y reconciliar main sin sobrescribir a otros integrantes.
2. Crear build Linux conjunto y pasar pip check, pruebas Parte 7, suite heredada reparada y pruebas de integración del proyecto principal.
3. En MySQL de desarrollo, revisar/aplicar solo el SQL aprobado y probar rol/ámbito, restricciones, dos workers concurrentes y reinicio antes/después del commit.
4. Ensayar JWT, credenciales MySQL y cifrado facial con datos sintéticos y respaldos de prueba. Nunca empezar la rotación facial editando la variable.
5. Cargar secretos mediante el gestor del servicio, fuera de Git; fijar zona, revisar TLS, pool y grants. Esta guía no realiza esas acciones.
6. Arrancar staging web y frontend, verificar login, roles, preview/descarga de tres formatos y CORS. Admin sin concesión debe recibir 403; profesor ajeno y estudiante ajeno no deben obtener datos.
7. Tras migración revisada, iniciar un worker. Crear/confirmar recordatorio verificado y reporte semanal; cerrar Chrome; verificar latido, una sola notificación y comunicaciones solo reviewed/no enviadas.
8. Probar carga/memoria y comprobar que no haya DSN, tokens, secretos ni contenido estudiantil en logs.
9. Aprobar release/artefactos y plan de rollback antes de decidir un despliegue real. No se concede esa aprobación en este documento.

## 12. Rollback seguro

Registrar antes del corte: revisión de código y artefactos, comandos, versión de esquema, versiones de secretos en el gestor (sin valores), zona y estado de acciones. Conservar respaldo y probar su restauración.

1. Suspender primero el worker afectado, sin borrar acciones ni notificaciones. Si está en ejecución, dejar terminar o asegurar rollback de transacción; no lanzar otro a ciegas.
2. Evitar nuevas activaciones desde la interfaz durante el incidente. CHATBOT_PROACTIVE_ENABLED en el web NO es un apagado de API; usar control operacional autorizado o un gate real previamente implementado.
3. Volver al artefacto de aplicación validado compatible con las tablas aditivas. Mantener esas cinco tablas; no usar DROP como rollback.
4. No restaurar toda la BD para revertir únicamente el código: se perderían asistencias posteriores. Una restauración de datos es una operación distinta con aprobación y recuperación verificadas.
5. Revisar expresamente la configuración que aplicará el rollback. Render puede reutilizar las variables específicas del deploy de destino y tratar de forma diferente los grupos de entorno. Podría recuperar una clave JWT antigua, un usuario revocado o una clave facial incompatible. No ejecutar “Rollback” sin revisar esto.
6. Preferir un redeploy controlado del código anterior con secretos vigentes y lector facial compatible cuando el rollback del artefacto reintroduciría secretos obsoletos. No reactivar una clave comprometida para lograr un arranque.
7. Perder previews RAM es esperable: regenerarlas tras nuevo login. Las acciones persistentes quedan para revisión; considerar períodos perdidos y fuentes ya pasadas antes de reactivar.
8. Verificar ámbitos, login, errores genéricos, documentos, lectura de cifrado de prueba y latido; reactivar UN worker y confirmar deduplicación.
9. Mantener despliegue automático apagado hasta resolver la causa y aprobar un nuevo corte. El rollback de código no revierte migraciones, rotaciones de secretos ni datos.

Consultar el comportamiento exacto de variables/artefactos en [Render Rollbacks](https://render.com/docs/rollbacks). No se ejecutó un rollback ni se modificó configuración real.
