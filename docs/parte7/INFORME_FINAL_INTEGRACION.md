# Informe final de integración — Parte 7: Monitor IA Assistant

Fecha: 31/10/2026. Worktree: monitor-asistencia-parte7. Rama: parte-7-chatbot-inteligente.

**Dictamen: funcional en desarrollo aislado; integración con main y despliegue bloqueados.** Las cinco fases y el rediseño se probaron juntos con FastAPI, JWT y SQLite sintético. Esto no certifica Aiven, Gemini real, TensorFlow combinado ni una aplicación resultante de merge.

No se hicieron commits, pushes, merges, despliegues ni migraciones. No se conectó a MySQL. Los tres stash y las ramas de los compañeros se conservan; el índice sigue vacío.

## Evidencia e inventario

- HEAD: 90e7ce75c34497350728b9aa02afd74c9e8ca188.
- origin/main actualizado con git fetch origin main: 6557e65fdb3cf66b2f7e4f563c6b1fce891fe9c8.
- Divergencia: 0 commits locales / 2 remotos. Los cambios sin commit no entran en ese conteo.
- Remotos: 4952ac4 (Parte 6/MySQL) y 6557e65 (responsive).
- Inventario completo por archivo y estado Git: [ARCHIVOS_PENDIENTES.tsv](revision/ARCHIVOS_PENDIENTES.tsv).
- Comparación de versiones e integridad: [AUDITORIA_ESTATICA.json](revision/AUDITORIA_ESTATICA.json).
- Resultados: [RESULTADOS_PRUEBAS.json](revision/RESULTADOS_PRUEBAS.json).
- Seguridad sin valores secretos: [SEGURIDAD_Y_CONFIGURACION.json](revision/SEGURIDAD_Y_CONFIGURACION.json).

El inventario inicial tenía 109 archivos pendientes, incluidos código, documentos y evidencias de las fases anteriores. El inventario final contiene 117 archivos pendientes (11 modificados y 106 nuevos), incluyendo esta auditoría. No hay eliminaciones versionadas ni rutas pendientes .env, ONNX, bases locales o entornos virtuales. Esto no elimina los secretos heredados ya versionados.

Archivos principales:

| Área | Archivos pendientes |
|---|---|
| Integración compartida | backend/app/api/chatbot.py; backend/app/schemas/chatbot.py; backend/app/services/chatbot_service.py |
| Seguridad/contexto | servicios chatbot_security.py y chatbot_conversation.py |
| Reportes | API chatbot_reports.py; schema chatbot_reports.py; servicios chatbot_reports.py, chatbot_report_documents.py y chatbot_report_store.py |
| ML | API chatbot_ml.py; servicio chatbot_ml.py |
| Proactividad | API y schema chatbot_proactive.py; db/proactive_models.py; servicios chatbot_proactive.py y chatbot_proactive_scheduler.py; backend/parte7_worker.py |
| Interfaz | componentes chatbot.js/proactive.js; CSS chatbot/proactive/panel-navigation; JS chatbot-init, panel-comun, panel-navigation y chatbot-legacy-page; chatbot-waves.svg |
| Páginas | estudiante/asistencia.html e ia.html; profesor/ia.html |
| Pruebas/dependencias | backend/tests/parte7; frontend/tests/parte7* y chatbot.voice.test.mjs; frontend/package.json/package-lock.json; requirements-parte7-*.txt |
| Migración propuesta | database/mysql/migrations/parte7/001_proactividad_additive.sql |
| Demo/evidencias | backend/parte7_demo.py, parte7_report_examples.py, parte7_proactive_examples.py y parte7_deployment_check.py; docs/parte7 |

Esta revisión amplió una aserción de frontend/tests/parte7.workspace.chrome.test.mjs, regeneró evidencias/ejemplos y añadió documentación/herramientas de diagnóstico. No cambió implementaciones de ML, EmoScan, MySQL ni configuración de producción. Los cambios previos del backend siguen pendientes.

## Cinco fases y rediseño juntos

| Parte | Verificado localmente | Pendiente |
|---|---|---|
| 1. Seguridad | Estudiante propio; profesor por cursos asignados/matrículas; admin/superadmin con concesión explícita. Ámbito vacío cerrado. Contexto, historial, descargas y acciones revalidan permisos. | Endpoints y secretos heredados fuera del chatbot. |
| 2. Conversación/voz | Intenciones, saludos, seguimiento y contexto firmado por 20 minutos. Texto, teclado, STT/TTS configurables, consentimiento y exclusión micrófono/reproducción. | Micrófono físico, proveedor de voz del navegador y Gemini real. |
| 3. Reportes | Dataset autorizado común; preview y XLSX/PDF/DOCX reales. Propiedad, revocación, vencimiento, límites y protección de fórmulas. Sin datos no hay gráfico ficticio. | Caché/cuotas compartidas para escalar; pruebas cloud. |
| 4. ML | K-Means guardado: 150/K=3/0.2373692496101911; origen y variables; reportes sin entrenamiento ni ganador no comparable; sin EmoScan. | Inferencia Parte 6 del main integrado y artefacto de regresión ausente. |
| 5. Proactividad | Fuentes verificadas, revisión/activación/pausa, estados, preferencias, bandeja, deduplicación y ejecución sin Chrome. Comunicaciones solo borrador/revisado. | Migración y worker dedicado; concurrencia/reinicio en MySQL de desarrollo. |
| Rediseño | Componente compartido SENATI, historial, filtros, voz, reportes y notificaciones conectados; cierre restaura página/borrador. | Reconciliar menús y drawer con main. |

El router /api/chatbot/message valida contexto/ámbito antes de derivar a reportes, ML y proactividad. Los reportes ML y programados reutilizan los exportadores. Las notificaciones abren la vista previa del chatbot. No existe transporte de mensajes externos.

## Robot flotante

Se comprobó visibilidad real y posición dentro del viewport al cerrar el asistente, además de montaje único, apertura y retorno:

- Estudiante: asistencia, calificaciones, curso, cursos, emoscan, ia y perfil.
- Profesor: curso, cursos, ia, perfil y segmentacion.
- 12 páginas funcionales; 262 comprobaciones workspace; cuatro resoluciones y administración sin cambios.
- En ia.html la vista amplia abre automáticamente; el robot se oculta mientras está abierta y reaparece al cerrar.
- Cinco páginas antiguas del profesor son archivos de 0 bytes: asistencia.html, dashboard.html, estadisticas.html, estudiantes.html y modelos.html. No se cuentan como implementadas.
- Las páginas nuevas de main, incluido inicio.html y módulos ML, no existen aquí y requieren otra verificación tras integrar. Los módulos ausentes siguen pendientes sin enlaces rotos, por elección del usuario.

Evidencias: [workspace-verificacion.json](evidencias/workspace-verificacion.json) y [rediseño/capturas](REDISENO_INTERFAZ.md).

## DEFAULT_DATA: causa y propuesta mínima

El módulo principal segmentacion/segmentacion_kmeans.py es de **tres variables**, no exporta DEFAULT_DATA y prepare_students(raw) retorna una tupla. La integración espera **cuatro variables**, argumentos expression_seed/samples y un DataFrame. El módulo que cumple ese contrato existe en segmentacion/experimental_expresiones/segmentacion_expresiones.py.

Cuatro consumidores importan el módulo equivocado: backend/app/services/segmentacion_service.py, backend/tests/integracion_final/test_segmentacion.py, test_segmentacion_expresiones.py y frontend/tests/preparar_segmentacion.py.

Añadir solo DEFAULT_DATA no resuelve el problema: process_csv falla después con TypeError al pasar expression_seed a la función de tres variables. Es un fallo de rutas/contratos, no matemático ni de EmoScan.

origin/main **ya corrigió el import del servicio** hacia el módulo experimental; conservar ese avance y sus formatos nuevos. Los helpers/pruebas siguen apuntando al módulo antiguo.

Se entrega [PROPUESTA_DEFAULT_DATA_NO_APLICADA.patch](revision/PROPUESTA_DEFAULT_DATA_NO_APLICADA.patch), preparada sobre el estado local y **sin aplicar**. Añade un adaptador explícito modelo_cuatro_variables.py que reexporta DEFAULT_DATA/FEATURES/fit_segments y delega prepare_students al modelo existente. Solo normaliza modalidad="principal_4_variables". Los cuatro consumidores importan ese contrato.

Esa normalización es necesaria: los CSV guardados usan principal_4_variables, mientras el módulo reutilizado devuelve experimental_4_variables. Solo corregir imports dejó 49 pruebas aprobadas y una diferencia de metadatos. Con el adaptador, pasan las 50 pruebas de integracion_final.

La comprobación usó sustitución temporal del módulo solo dentro del proceso de prueba. **El producto actual no se modificó.** Se reprodujeron 150 perfiles, K=3 y silueta 0.2373692496101911; las cuatro variables y asignaciones coinciden con los CSV guardados. No cambian StandardScaler, K-Means, PCA, semillas ni datos. [Diagnóstico](revision/DEFAULT_DATA_DIAGNOSTICO.json).

También pasaron 280 aserciones antiguas del navegador con fixtures calculadas por ese modelo real y cámara/respuestas personales simuladas. Esto valida la interfaz con la propuesta; no demuestra que el endpoint actual ya esté corregido.

El parche local no debe aplicarse a ciegas sobre main: adaptar sus imports conservando el servicio actualizado del compañero.

### Integridad de Parte 3

La suite de algoritmos informó 17 aprobadas, cuatro subpruebas fallidas y 25 subpruebas aprobadas. Los cuatro fallos de hashes afectan README_Parte3.md, requirements.txt, segmentacion_kmeans.py y test_segmentacion.py.

No cambiaron respecto de HEAD. Al convertir CRLF a LF, sus hashes coinciden exactamente con integridad_original.json: diferencia de checkout Windows. Otros CSV/artefactos sí coinciden con hashes CRLF, así que no normalizar todo ni regenerar el manifiesto indiscriminadamente. Proponer atributos eol=lf específicos para esos cuatro archivos o un contrato de hash canónico revisado; no cambiar algoritmos ni desactivar la prueba.

## Pruebas ejecutadas

Python 3.12.10; Chrome real con Playwright. SQLite exclusivamente sintético y MySQL bloqueado. Demo de auditoría separada en 127.0.0.1:8018 para no interrumpir la vista de 8017.

| Prueba | Resultado |
|---|---|
| backend/tests/parte7 | 256 aprobadas, un aviso Starlette/TestClient-httpx. También incluidas en la ejecución global; no sumarlas dos veces. |
| backend/tests completo, imports originales | **291 aprobadas, 3 fallidas y 25 errores**, un aviso. Suite global no aprobada. |
| integracion_final con propuesta solo en memoria | 50 aprobadas. No cambia el resultado original del producto. |
| K-Means principal + experimental | 17 aprobadas; cuatro subpruebas fallidas por CRLF/LF; 25 subpruebas aprobadas. |
| Voz | Aprobada con STT/TTS simulados; sin audio físico. |
| Chrome chatbot / workspace / workspace real | 72 / 262 / 29 comprobaciones aprobadas. |
| Chrome proactividad / reportes / ML | 42 / 44 / 60 aprobadas. |
| Conversación real contextual | Saludo → cursos → ranking → octubre: aprobada. |
| Navegador antiguo con fixtures de propuesta | 280 aserciones aprobadas; K-Means calculado, cámara/inferencia personal simuladas. |
| JavaScript legado de expresiones | 14 comprobaciones aprobadas. |
| Ejemplos de reportes | Excel/PDF/Word generados, descargados y abiertos con lectores independientes. 8 filas autorizadas sintéticas; 87,5% calculado. |
| Demo semanal | APScheduler sin navegador, reloj de prueba acelerado: recordatorio y reporte semanal, 2 filas, 50% calculado, tres documentos y cero envíos externos. |
| pip check del venv Parte 7 | Sin dependencias rotas; no certifica paquetes externos en TEMP ni la imagen combinada Linux/TensorFlow. |
| git diff --check | Aprobado al cierre. |

Las seis suites Chrome propias suman 509 aserciones (72+262+29+42+44+60), además de voz y conversación. La prueba antigua de 280 es separada y usa la propuesta solo para sus fixtures.

Bloqueos globales:

- Dos errores de colección DEFAULT_DATA.
- Un error de colección facial: face_repository.py importa get_connection, inexistente en database.py. No se ejecutó la rutina manual de escritura ni se reintrodujo una conexión global.
- Veintidós errores de preparación en test_chatbot.py/test_chatbot_auth.py por fixtures client/headers ausentes. Sus expectativas antiguas de acceso administrativo implícito deben actualizarse; no debilitar permisos.
- Dos pruebas EmoScan requieren integraciones/emoscan/imagenes_prueba/astronauta.png, no versionado en esta rama; no validan inferencia ONNX real sin ese recurso.
- test_bounded_queue_timeout_and_recovery falla también solo, esperando READY. Requiere investigación con el responsable de EmoScan; no se aumentaron tiempos para ocultarlo.

Al inicio faltaban OpenCV/Flask. Se completaron solo en TEMP y se alineó OpenCV a <5. La repetición eliminó el fallo de Flask; la tabla refleja el resultado posterior. Se corrigió el guard __main__ del runner temporal para multiprocessing spawn; el timeout de cola persistió en ejecución directa aislada.

No se descargaron fotos, ONNX ni datos reales, ni se ejecutaron los scripts manuales que enrolan rostros o escriben asistencias.

[revision/auditar_backend.py](revision/auditar_backend.py) permite repetir el diagnóstico: impone credenciales ficticias, clave facial efímera en memoria, bloqueo de conexiones no SQLite, descargas y red externa. Desde un entorno local con dependencias de prueba completas:

    python -B docs/parte7/revision/auditar_backend.py

P7_AUDIT_IMPORT_OVERLAY=1 permite probar solo la propuesta con backend/tests/integracion_final -q -p no:cacheprovider --tb=short. Es una variable diagnóstica, **no de Render**. Una ejecución con overlay no valida el producto sin corregir.

No arrancar app.main directamente para QA: su lifespan intenta DDL/descargas. La demo parte7_demo evita ese arranque y el runner bloquea esos efectos.

Documentos comprobados: [Excel](ejemplos/ejemplo-asistencia-autorizada.xlsx), [PDF](ejemplos/ejemplo-asistencia-autorizada.pdf), [Word](ejemplos/ejemplo-asistencia-autorizada.docx).

## Conflictos antes del merge

Comparación HEAD/base, archivo local y origin/main usando git merge-file sobre copias temporales LF. No se creó merge ni MERGE_HEAD; es diagnóstico textual, no una aplicación combinada probada.

| Ruta solapada | Resultado | Revisión necesaria |
|---|---|---|
| backend/app/services/chatbot_service.py | Conflicto, 2 bloques | Conservar seguridad/contexto/reportes/ML e incorporar mejoras de main para faltas/asistencia. |
| frontend/components/chatbot.js | Conflicto, 2 bloques | Mantener rediseño y herramientas sin perder mejoras de main. |
| frontend/estudiante/asistencia.html | Conflicto, 1 bloque | main renovó la página: adaptar su montaje, no reinstalar la página antigua. |
| frontend/estudiante/ia.html | Conflicto, 2 bloques | Conservar ruta y vista amplia con layout responsive integrado. |
| frontend/js/panel-comun.js | Conflicto, 2 bloques | Reconciliar menús reales, páginas nuevas y drawer. |
| backend/app/api/chatbot.py | Texto combina limpio | Revisar semántica de roles, subrouters y seguridad. |
| frontend/js/chatbot-init.js | Texto combina limpio | Revisar orden de carga, auth e idempotencia. |

Cinco conflictos textuales y siete rutas solapadas. No hay colisiones add/add en esta instantánea.

Otros riesgos:

- main introduce otro responsive/drawer y más páginas; pueden duplicarse controles o perderse enlaces aunque Git no marque un conflicto.
- main incorpora tratamiento de ausencias que aquí aún interpreta “faltas” sin período como consulta de hoy. No perder esa mejora al reconciliar.
- main ya corrige el import del servicio Segmentación y amplía formatos; actualizar helpers sin volver a versiones antiguas.
- El adaptador neuronal detectará automáticamente la Parte 6 presente en main y podrá dejar de responder “pendiente”. Hay que probar su servicio autorizado, fechas, artefactos y TensorFlow.
- Los cinco módulos pendientes del menú local sí tienen páginas en main; activar enlaces solo tras comprobar la integración.
- Los locks divergen: Parte 7 probó NumPy 2.5.4/Pandas 3.1.0/sklearn 1.9.1/FastAPI 0.162.0; Parte 6 fija TensorFlow 2.20.0/NumPy 2.2.6/Pandas 2.3.3/sklearn 1.7.2/FastAPI 0.119.1. Ambos locks juntos imponen versiones incompatibles. main añade tensorflow-cpu/keras sin fijarlos. Resolver y probar una imagen Linux conjunta; no sustituir el lock del compañero.

## MySQL: propuesta pendiente, no aplicada

[001_proactividad_additive.sql](../../database/mysql/migrations/parte7/001_proactividad_additive.sql): cinco CREATE TABLE; ninguna sentencia destructiva, escritura académica ni creación de base.

| Tabla | Finalidad |
|---|---|
| chatbot_proactive_actions | Propietario/destinatario, configuración, fuente, zona, frecuencia, estado y ejecución. |
| chatbot_proactive_preferences | Habilitación y zona. |
| chatbot_proactive_notifications | Resultado privado y execution_key único. |
| chatbot_proactive_audit | Eventos mínimos. |
| chatbot_proactive_worker | Latido; no lease de liderazgo. |

ProactiveBase es independiente de Base. No sustituir SQL por create_all: el DDL agrega FK/CHECK/índices y MEDIUMTEXT donde el ORM usa Text. El worker, cuando se habilite, escribirá sus tablas y purgará notificaciones/auditorías vencidas; no se ejecutó en MySQL.

El compañero debe verificar en una copia de desarrollo: versión MySQL/InnoDB, charset/collation, tipos/signedness de usuarios.id/cursos.id/estudiantes.id, columnas, FK/CHECK/índices, límites de snapshots y cuentas. Verificar chat_historial según 05_chatbot.sql, sin ejecutar todo el script sobre objetos existentes. Comprobar fechas/matrículas/notas requeridas por Parte 6 y evaluaciones.fecha_vencimiento, sin inventarlas.

Probar locks, transacciones, concurrencia, revocación y reinicios en MySQL de desarrollo. Separar cuenta migradora de usuarios runtime web/worker sin DDL. El gate de migración revisada solo comprueba existencia de tablas, no equivalencia del esquema. No se inspeccionó la base de la nube ni se pidieron credenciales.

## Render: variables y ejecución

La [matriz completa](despliegue/MATRIZ_VARIABLES.md) coincide con los 20 campos Settings locales/remotos; junto a lecturas adicionales identifica 24 variables de aplicación. No se consultaron valores efectivos de Render.

| Variables | Servicio / finalidad |
|---|---|
| DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD | Web/worker con cuentas separadas; configuración explícita, contraseña secreta y TLS pendiente. |
| JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES | Firma/política web. Worker también necesita el secreto para pseudónimos de auditoría. |
| APP_TIMEZONE | Web/worker; zona institucional coherente. |
| CHATBOT_INSTITUTIONAL_READ_USER_IDS | Web/worker; vacío deniega a admin/superadmin. |
| GEMINI_API_KEY, GEMINI_MODEL | Solo web, opcionales. Sin ambos funciona el flujo local. |
| CHATBOT_PROACTIVE_ENABLED y CHATBOT_PROACTIVE_MIGRATION_REVIEWED | Solo worker, tras migración aprobada; no migran ni validan todo el DDL. |
| CHATBOT_DEMO_MODE | false/ausente en producción; no es un sandbox ni sustituye autorización. |

FACE_ENCRYPTION_KEY pertenece al backend facial, no al worker/frontend. Preservar la política EMOSCAN_* existente.

Reportes no añade variables: TTL=600 s, 32 entradas y 24 MiB de caché son constantes. No hay SMTP/Twilio/WhatsApp. DB_SSL_CA, CORS_ALLOWED_ORIGINS, DB_AUTO_CREATE_SCHEMA y FACE_ENCRYPTION_PREVIOUS_KEYS son propuestas **no leídas actualmente**: configurarlas no implementa esos controles. API_URL del navegador tampoco se configura añadiendo una variable Render de ese nombre.

Comandos propuestos, pendientes de resolver seguridad/dependencias:

- Web build: python -m pip install -r requirements.txt -r requirements-parte7-proactivo.txt.
- Web start: PYTHONPATH=.:backend python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "$PORT" --workers 1.
- Worker build: python -m pip install -r requirements-parte7-proactivo.txt.
- Worker start: python backend/parte7_worker.py.

El render.yaml actual no instala exportadores/planificador de Parte 7. La [propuesta de Blueprint](despliegue/render-parte7.propuesta.yaml) no lo reemplaza ni debe sincronizarse todavía. Medir memoria/carga en Linux con todos los modelos: la demo Windows sin TensorFlow/ONNX no demuestra que 512 MiB alcancen.

## Recordatorios: Background Worker

Recomendado: **un Background Worker dedicado**. El entrypoint actual usa BlockingScheduler continuo, consulta cada 30 s y no termina; encaja con un servicio continuo sin entrada HTTP de Render. [Fuente oficial](https://render.com/docs/background-workers).

Cron requeriría otro entrypoint finito de una pasada. Render exige que el comando termine y usa horarios UTC. No poner el worker actual en Cron ni ejecutar ambos a la vez. [Cron Jobs](https://render.com/docs/cronjobs).

Controles:

- Identidad única de configuración y execution_key único por acción/horario.
- Revalidación de propietario, ámbito, preferencias y fuente en cada ejecución.
- SELECT FOR UPDATE; notificación y avance de next_run en la misma transacción; IntegrityError con rollback.
- Acciones durables en SQL; no dependen de Chrome ni de pickles.
- Reinicio consulta vencidos. Fuente pasada/cambiada bloquea la acción. Recurrentes generan el período cerrado al momento de ejecutar y avanzan: no reproducen todas las semanas perdidas.
- Máximo 50 acciones/pasada; notificaciones 30 días, auditoría 90 días; latido de 120 s.
- Prueba de dos workers/reinicio sin duplicados en SQLite de archivo; prueba de Chrome cerrado aprobada.

max_instances=1 solo evita concurrencia dentro del proceso. El latido no es liderazgo distribuido. Mantener una instancia y probar contención/deadlocks/reinicio en MySQL antes de escalar. Los errores pueden bloquear acciones y requerir revisión; no hay cola de reintentos con backoff configurable.

CHATBOT_PROACTIVE_ENABLED controla solo el arranque del worker, no los endpoints web. No presentarlo como interruptor global.

Los reportes interactivos viven en RAM, con propiedad/TTL, sin disco persistente. Los programados conservan el dataset en SQL y generan el documento al descargar. Caché y cuotas son por proceso: con varias réplicas pueden fallar descargas o multiplicarse cuotas. Render usa disco efímero por defecto; un disco tampoco comparte RAM entre procesos. [Discos de Render](https://render.com/docs/disks). Mantener una instancia web/un proceso o implementar almacenamiento y cuotas compartidos.

## Privacidad y secretos: bloqueos

Se confirmaron literales JWT y FACE_ENCRYPTION_KEY en render.yaml, defaults JWT/facial en backend/app/core/config.py y respaldo de contraseña MySQL usado por database.py. La clave facial tiene formato Fernet válido, no es solo un marcador. También están en origin/main.

**No se imprimieron valores ni se probó su vigencia en producción.** No se encontraron copias de esos literales en pendientes, incluidos XML de XLSX/DOCX, ni coincidencias en una búsqueda dirigida de tokens/llaves privadas. No es un pentest ni garantiza ausencia de todo secreto.

Acciones previas a publicación/despliegue:

- Rotar/revocar JWT y credenciales MySQL con el responsable; retirar literales/fallbacks y usar secretos del despliegue. Rotar JWT invalida sesiones/contextos.
- **No cambiar/borrar directamente la clave facial.** El lector soporta una sola. Preparar keyring/migrador, respaldo y restauración probada; recifrar datos y conservar la clave antigua en bóveda restringida mientras existan respaldos que la requieran. Retirarla del runtime solo después de verificar recuperación.
- Quitar un literal no lo revoca ni elimina del historial. Coordinar cualquier limpieza histórica; no force push unilateral.

Otras vulnerabilidades heredadas:

- /api/health público expone pass_prefix, pass_len, has_fallback, host, user y db_error, también en main. Reemplazarlo por health mínimo; diagnóstico protegido.
- Handler global devuelve str(exc); responder de forma genérica con logs saneados.
- GET /api/attendance/ permite profesor y deriva a get_all sin ámbito de cursos. Corregir y probar con dos profesores.
- get_current_user convierte sub a int sin validar: claims malformados pueden producir 500; responder 401.
- Lifespan intenta create_all/descargas; separar DDL y provisión de modelos del arranque.
- Engine sin CA/verificación TLS Aiven explícita; validar antes de cloud.
- Revisar CORS por sus patrones amplios.

Controles propios de Parte 7: backend decide ámbitos, Gemini no genera SQL ni permisos; contexto firmado pero legible; descargas/acciones revalidan ámbito; logs con códigos/pseudónimos; EmoScan queda fuera de reportes docentes y riesgo académico.

Si se configura Gemini, recibe pregunta y resultado autorizado, potencialmente datos académicos personales. Autorización académica no sustituye decisión institucional sobre transferencia/retención con terceros. Mantenerlo desactivado hasta revisar minimización y política. Su prompt tampoco garantiza exactitud numérica de la redacción: falta verificación con el proveedor real.

Chrome puede transcribir con un servicio externo. La app pide consentimiento y no guarda grabaciones; no afirmar que todo reconocimiento es local.

## Orden de integración y reversión

1. Resolver secretos expuestos, health/errores, ámbito de asistencia y arranque DDL/descargas; preservar recuperación facial.
2. Revisar/aplicar la propuesta de imports/metadatos conservando el servicio nuevo de main. Resolver hashes Windows, fixtures heredadas y fallos de cola/artefactos EmoScan.
3. Cuando se autorice, reconciliar cinco conflictos y dos solapamientos limpios en entorno de integración independiente. No aceptar ours/theirs para archivos completos.
4. Conservar páginas/menús reales del compañero, elegir un drawer y comprobar robot/roles en todas las rutas nuevas.
5. Resolver dependencias Linux/TensorFlow; probar artefactos e inferencia prospectiva autorizada, sin reentrenar.
6. Revisar/aplicar solo la migración aprobada en desarrollo; probar locks/reinicio/deduplicación/revocación.
7. Staging autorizado con secretos por servicio, web de un proceso y worker único; comprobar documentos/TTL, no envío externo y carga/memoria.
8. Repetir suite global **sin overlays** y pruebas de main/Parte 6 en el árbol realmente integrado. Audio/cámara físicos requieren prueba manual.
9. Revisar contenido exacto y autorizar publicación, integración y despliegue por separado.

Rollback: suspender primero el worker, volver al artefacto compatible con secretos vigentes, conservar tablas/datos, regenerar previews RAM y revisar acciones vencidas antes de reactivar un worker. No DROP, restauración global de BD ni reactivación de claves comprometidas para revertir solo código. [Guía detallada](despliegue/GUIA_DESPLIEGUE_Y_ROLLBACK.md).

**Estado final: lista para revisión local; no aprobada para merge ni despliegue. No se publicó ningún commit.**
