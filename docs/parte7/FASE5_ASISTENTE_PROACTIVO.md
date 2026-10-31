# Fase 5 — asistente académico proactivo

Implementación local en monitor-asistencia-parte7, rama parte-7-chatbot-inteligente.
No se hicieron commits, pushes ni merges. No se conectó MySQL, no se aplicaron migraciones de producción y no se enviaron mensajes externos.

## Revisión del esquema existente

Se revisaron backend/app/db/models.py, database/mysql/01_schema.sql, los servicios de notas/asistencia y las consultas autorizadas del chatbot.

| Fuente | Información comprobable | Uso |
|---|---|---|
| sesiones_clase | curso_id, fecha, hora_inicio, hora_fin y estado | Recordatorios de clases futuras ACTIVAS del curso autorizado. Una cancelación o cambio posterior bloquea el recordatorio para revisión. |
| evaluaciones | curso_id, nombre y fecha_vencimiento DATE, opcional | Aviso de evaluación solamente si existe fecha. No existe una hora verificable de vencimiento: la hora configurable es la del AVISO. |
| asistencias | usuario, sesión, fecha y estado explícito | Resúmenes y umbrales; TARDE se normaliza con TARDANZA. No se deduce AUSENTE de una fila faltante. |
| matriculas, asignaciones_profesor | Relación actual estudiante/curso/profesor | Autorización al preparar, confirmar, ejecutar, consultar y descargar. |
| Tutorías/reuniones | No hay tablas o agenda institucional en el esquema | Eventos personales declarados por el usuario con título y fecha ISO que incluya zona; revisión y confirmación explícitas. No se atribuyen a MySQL. |
| Tareas | No existe un modelo independiente de tareas | No se generan tareas o vencimientos ficticios. Se utilizan las evaluaciones reales con fecha. |

No se utilizan EmoScan, fotografías, estados emocionales ni modelos de riesgo para estas acciones.

## Funcionalidades

- Recordatorio de clase con antelación configurable de 0 a 1440 minutos.
- Aviso de evaluación con fecha verificada; hora de aviso elegida por el usuario.
- Resumen semanal de asistencia para estudiante (solo propio) o profesor dentro de su curso.
- Alertas diarias/semanales por ausencias o tardanzas explícitas; umbral 1–100, ventana 1–90 días.
- Reportes diarios/semanales del profesor y notificación interna de disponibilidad.
- Recordatorios personales de tutoría/reunión, distinguidos de la agenda institucional.
- Borradores de comunicación basados en registros autorizados. Aprobar el borrador registra revisión, pero NO lo envía.
- Estados de acciones: draft, active, paused, blocked, completed, cancelled, reviewed.
- Estado de notificación: unread, read, completed.
- Configuración global para desactivar recordatorios; edición con revisión de versión y nueva confirmación.
- Propuestas automáticas de avisos desde próximas clases y evaluaciones verificadas al abrir el dashboard. Pulsar Preparar solo rellena el formulario; no crea ni activa acciones.
- Centro SENATI en las páginas de Asistente IA de profesor y estudiante. Incluye bandeja, contador, fuentes, frecuencia, zona horaria, edición, pausa y apertura de reportes.
- Conversación: «Recuérdame mi próxima clase», «Programa un reporte semanal» o «Alerta de ausencias» ofrecen ir al centro. Interpretar una frase NO crea ni activa una tarea.

Los reportes usan días o semanas institucionales ya cerrados, con la zona APP_TIMEZONE. La zona elegida en la acción determina CUÁNDO ejecutarla; no permite incluir días institucionales todavía abiertos por estar en otro huso horario. Semanas: lunes a domingo de la última semana cerrada. Reporte diario: día institucional anterior.

Si el intervalo de aviso ya empezó pero la clase/evento aún no comienza, la notificación se programa de inmediato tras confirmar. Si la fuente ya pasó o cambió, la acción se bloquea y requiere revisión.

## Arquitectura y planificador

- app/db/proactive_models.py: metadatos ProactiveBase independientes de Base. Importar el router NO incorpora tablas a Base.metadata.create_all de app.main.
- app/schemas/chatbot_proactive.py: tipos cerrados, límites, zonas IANA y fechas con desplazamiento; campos adicionales prohibidos.
- app/services/chatbot_proactive.py: fuentes, revisión, permisos, recurrencia, generación, deduplicación, vencimiento y auditoría.
- app/services/chatbot_proactive_scheduler.py: APScheduler 3.11.3. Un trabajo fijo consulta las acciones persistentes en la BD.
- app/api/chatbot_proactive.py: rutas autenticadas integradas bajo /api/chatbot/proactive.
- backend/parte7_worker.py: proceso dedicado opt-in para despliegue; no migra y exige conexión configurada explícitamente.
- frontend/components/proactive.js y frontend/css/proactive.css: centro responsive; el navegador consulta la bandeja, NO ejecuta el reloj de trabajos.
- backend/parte7_demo.py: habilita BackgroundScheduler solo en su SQLite sintético, con bloqueo para serializar acceso al único SQLite RAM.
- backend/parte7_proactive_examples.py: demostración reproducible con planificador real y reloj lógico acelerado.
- backend/tests/parte7/test_proactive.py y frontend/tests/parte7.proactive.chrome.test.mjs: permisos, datos, estado, concurrencia y navegador.

En despliegue se utiliza un proceso BlockingScheduler dedicado, no un scheduler por cada worker de Uvicorn. Las acciones/fechas están en tablas propias; no se serializan callables ni pickles de usuarios. Se configuran coalesce y max_instances=1, coherentes con la [guía oficial de APScheduler 3](https://apscheduler.readthedocs.io/en/3.x/userguide.html).

Se revisaron render.yaml y Procfile: actualmente declaran servicios web, sin comando de worker proactivo. No se modificaron. Para Render, el worker debe ser un servicio independiente continuo; esa separación corresponde al modelo documentado de [Background Workers de Render](https://render.com/docs/background-workers). Se adjunta un ejemplo NO habilitado automáticamente.

El centro muestra el latido del worker: sin actividad reciente, las acciones aparecen en espera. Un navegador abierto no sustituye un worker.

## Nuevas tablas y migración para revisión

Propuesta: database/mysql/migrations/parte7/001_proactividad_additive.sql.

1. chatbot_proactive_actions: propietario/destinatario, curso/estudiante/fuente, configuración, zona horaria, frecuencia, estado, próxima ejecución UTC, versión y huella del ámbito.
2. chatbot_proactive_preferences: habilitación por usuario y zona predeterminada.
3. chatbot_proactive_notifications: ejecución única, estado de lectura, snapshot privado y vencimiento.
4. chatbot_proactive_audit: actor, acción y código de evento; sin preguntas, texto de comunicaciones, nombres ni métricas privadas.
5. chatbot_proactive_worker: último latido UTC, sin nombres de máquina ni credenciales.

El SQL contiene exclusivamente CREATE TABLE e índices/constraints de tablas nuevas. NO incluye creación de base, alteración o eliminación de tablas previas. NO se ejecutó en MySQL.

Antes de aplicarlo: revisar SQL y compatibilidad de claves/charset/constraints con el servidor, revisar permisos del usuario técnico y ejecutar en una base de DESARROLLO autorizada. La aplicación no lo aplica al arrancar. La demostración crea estas tablas únicamente en SQLite RAM sintético.

Si faltan las tablas, las operaciones de escritura responden 503 y el centro indica migración pendiente. Las fuentes académicas pueden consultarse sin habilitar automatizaciones.

## API

Todos los endpoints requieren JWT y usuario activo. Ningún endpoint admite destinatarios externos, URLs/callbacks, SQL, código o funciones arbitrarias.

- GET /status: disponibilidad de tablas, worker_running, worker_last_seen, external_delivery=false.
- GET /sources: clases próximas y evaluaciones con fecha del ámbito, horizonte máximo de 90 días.
- GET /students?course_id=...: estudiantes autorizados del curso; alumno solo propio.
- GET /preferences y PUT /preferences: enabled y timezone.
- GET /actions y POST /actions: lista propia; POST siempre prepara un borrador, no lo activa.
- PUT /actions/{id}: edición con version y spec. Vuelve a draft para nueva revisión.
- POST /actions/{id}/transition: version, operation y confirmed. activate/review requieren confirmed=true.
- GET /notifications: bandeja propia vigente, sin resultados de ámbitos revocados.
- GET /notifications/{id}: detalle protegido.
- PATCH /notifications/{id}: state=read|completed.
- POST /notifications/{id}/report: crea una vista previa privada temporal del snapshot autorizado; reutiliza las descargas XLSX/PDF/DOCX de fase 3.

Ejemplo de borrador de clase:

    {"kind":"next_class","course_id":1,"source_id":500,"timezone":"America/Lima","frequency":"once","reminder_minutes":30}

Los IDs son ejemplos sintéticos: siempre deben seleccionarse de /sources. No se acepta una fecha de clase inventada desde el cliente.

Ejemplo de programación docente:

    {"kind":"scheduled_report","course_id":1,"timezone":"America/Lima","frequency":"weekly","weekday":0,"local_time":"08:00"}

Confirmación separada, tras revisar el borrador:

    {"version":1,"operation":"activate","confirmed":true}

Comunicación: operation=review, estado final reviewed y external_delivery=false. No hay ruta de envío. No se ha configurado correo, WhatsApp, SMS ni notificaciones push.

## Seguridad y operación

- ESTUDIANTE: solo datos propios de cursos matriculados. No programa reportes docentes ni comunicaciones docentes.
- PROFESOR: únicamente cursos asignados y estudiantes actualmente matriculados.
- ADMIN: mantiene la concesión institucional explícita de lectura. No suplanta al profesor para programar reportes docentes.
- Destinatario siempre igual al propietario. El cuerpo rechaza recipient_id o channel; el worker también comprueba la igualdad.
- Se revalidan rol/estado/ámbito al ejecutar y al consultar/descargar. Una huella de ámbito cambiada bloquea/redacta; no continúa con datos del ámbito anterior.
- Fechas/fuentes se cotejan de nuevo. Cancelaciones, fuentes modificadas e historiales fuera de volumen bloquean la acción.
- Una identidad única evita duplicar el mismo borrador; en clases/evaluaciones, cambiar la anticipación requiere editar el recordatorio existente.
- Una clave única por acción/ejecución y el avance de agenda se guardan con la notificación en la MISMA transacción. No hay efectos externos previos al commit.
- Bloqueo de fila en MySQL; restricción única para contención y SQLite. Se probó concurrencia de dos workers y reinicio con SQLite de archivo sintético. La integración real con MySQL queda pendiente de revisión, no se afirma probada.
- Las alertas no repiten el mismo conjunto de registros mientras la condición no cambie. Volver a cruzar un umbral o nuevos registros permite otro aviso.
- Máximo 40 acciones pendientes por cuenta, 50 ejecuciones por ciclo, 2000 registros por reporte y 2 MB por resultado programado. Reportes grandes requieren filtros menores.
- Bandeja/configuración: máximo 100 entradas por consulta. Reportes descargables siguen con cuotas/TTL de fase 3.
- Notificaciones y snapshots se vencen a 30 días; el worker elimina solo esas filas del módulo. Auditoría minimizada: 90 días. Las configuraciones y estados de acciones se conservan como historial del usuario.
- Errores de worker/planificador se registran con códigos genéricos. Los logs usan pseudónimo HMAC del actor; no incluyen consultas, mensajes, contraseñas ni datos de estudiantes.
- Las fechas de ejecución se guardan en UTC; la zona IANA, hora local y frecuencia se conservan explícitamente.

## Instalación y despliegue pendiente

Python 3.12 del entorno independiente de Parte 7, compatible en las pruebas con APScheduler 3.11.3. Instalado en .venvs/p7, sin tocar entornos de otros módulos.

    python -m pip install -r requirements-parte7-proactivo.txt

Pruebas:

    python -m pip install -r requirements-parte7-pruebas.txt
    python -B -m pytest backend/tests/parte7 -q -p no:cacheprovider

No se cambia requirements.txt del despliegue existente ni se inicia un proceso contra la nube. El operador deberá revisar el build para instalar las dependencias nuevas tanto en API como en worker.

Solo después de aplicar/revisar la migración en desarrollo y configurar una conexión autorizada:

    # Variables de habilitación; no son credenciales:
    CHATBOT_PROACTIVE_ENABLED=true
    CHATBOT_PROACTIVE_MIGRATION_REVIEWED=true
    python backend/parte7_worker.py

DB_HOST, DB_NAME, DB_USER y DB_PASSWORD deben inyectarse mediante el gestor de secretos del entorno, sin imprimirlas ni incluirlas en argumentos, logs o Git. El runner exige esos valores explícitos para evitar los valores heredados del proyecto. La zona institucional debe coincidir con la API. No se solicitaron credenciales de producción.

Dependencias pendientes para producción: revisión/aplicación del SQL, configuración explícita de conexión y secretos por el responsable, servicio worker dedicado y supervisado, y validación de concurrencia/constraints contra MySQL de desarrollo. Las tutorías institucionales necesitarían una fuente institucional futura; la función actual es personal/declarada. Los envíos a terceros no están habilitados.

## Demostración comprobable

Inicio local seguro:

    python -B -m uvicorn parte7_demo:app --app-dir backend --host 127.0.0.1 --port 8017

Abrir http://127.0.0.1:8017/ y elegir profesor o estudiante. En Asistente IA aparece el Centro de notificaciones. No usar app.main para esta demostración.

1. Elegir una clase/evaluación real del catálogo SINTÉTICO.
2. Preparar borrador, revisar fecha/origen/zona/frecuencia/destinatario y activar.
3. Pausar o editar; una edición vuelve a requerir confirmación.
4. Programar un reporte semanal y consultar su próxima fecha.
5. Preparar comunicación y aprobarla: debe quedar sin envío.
6. Para una prueba inmediata, declarar una reunión de prueba a dos minutos vista con desplazamiento horario y antelación de 30 minutos: el intervalo ya empezó y el aviso se ejecuta en segundos, mientras el evento permanece futuro. Cerrar Chrome; al reabrir aparece la notificación del servidor.

Demostración reproducible, independiente del servidor vivo:

    python -B backend/parte7_proactive_examples.py

Usa APScheduler real y SQLite RAM, con reloj lógico acelerado explícito. Ejecuta un recordatorio cuya clase existe en sesiones_clase y un reporte semanal; NO hace esperar una semana real ni simula una notificación de producción.

Archivos en ejemplos/:

- FASE5_DEMOSTRACION.json: evidencia y hashes.
- fase5-reporte-semanal.xlsx
- fase5-reporte-semanal.pdf
- fase5-reporte-semanal.docx

Datos comprobados: período 26/10/2026–01/11/2026, dos registros sintéticos autorizados (un presente, una ausencia), asistencia 50 %. El porcentaje procede del servicio de reportes, no de JavaScript o constantes de presentación. Los archivos se abrieron con openpyxl, pypdf y python-docx.

Chrome:

    cd frontend
    npm run test:proactive

Comprueba revisión, activación, pausa, programación, borrador sin envío, roles, tres resoluciones y un recordatorio con el proceso de Chrome cerrado. El test solo admite la demo loopback y exige MySQL bloqueado. El centro no depende del temporizador del navegador para ejecutar tareas.

Evidencias: evidencias/proactivo-1366.png, proactivo-1920.png y proactivo-390.png.

Resultados finales: [RESULTADOS_FASE5.md](RESULTADOS_FASE5.md). Backend: 256 pruebas aprobadas. Chrome: 42 de proactividad, 72 de interfaz, 44 de reportes y 60 de ML.
