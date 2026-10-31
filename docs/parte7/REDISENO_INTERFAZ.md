# Rediseño del asistente — vista integrada SENATI

Implementado localmente en monitor-asistencia-parte7, rama parte-7-chatbot-inteligente. Sin commit, push, merge, despliegue, conexiones a MySQL ni cambios en backend/modelos.

## Resultado

Un solo componente compartido ocupa la superficie principal a la derecha del menú. No hay backdrop, modal pequeño ni bloqueo del sidebar. Al abrirlo se conservan los nodos/estado de la página; al cerrar se restauran, junto con el borrador, el scroll y la conversación en memoria. La ruta no cambia por abrir/cerrar el asistente.

Se conservan el robot del proyecto y SENATI. La interfaz incluye saludo con nombre autenticado, identificación de demo cuando corresponde, preguntas por rol, filtros autorizados, contexto, mensajes alineados, entrada inferior, voz y reportes. Los datos académicos continúan llegando del backend; no se añadieron porcentajes ni métricas en JavaScript.

“Nueva conversación” limpia la vista y el contexto temporal sin borrar el historial del servidor. Historial permite recuperar preguntas autorizadas; la eliminación anterior sigue disponible como acción independiente con confirmación explícita.

La campana y el botón flotante muestran un contador únicamente a partir de notificaciones sin leer devueltas por el servicio; no se usa una cifra decorativa. El acceso al centro abre el centro existente o la ruta ia.html#notificaciones.

En escritorio se mantiene el menú a la izquierda. Tablet/móvil utilizan un drawer acotado a profesor/estudiante, sin modificar el panel administrativo. El contenido de conversación se desplaza independientemente de la entrada inferior.

## Menús y compatibilidad con main

- Estudiante: se retiró Asistente IA del menú, manteniendo ia.html funcional y con apertura automática de la vista amplia.
- Inicio utiliza la portada de cursos ya disponible (cursos.html?inicio=1); no se creó una copia antigua de inicio.html, que aparece en el main remoto.
- Profesor: conserva Cursos, Segmentación IA y Perfil. Por elección del usuario, Estadística Básica, Predicción ML, Clasificación ML, Dashboard ML y Red Neuronal IA aparecen como pendientes de integración, sin href ni enlaces rotos. No se copiaron sus módulos de otra rama.
- Admin y superadmin: no se inyecta el nuevo componente ni el drawer académico en sus páginas.
- La página antigua de asistencia recibe únicamente un adaptador de presentación y transporte del asistente. No se modificó camera.js ni la lógica de consentimiento/captura.
- No se modificaron EmoScan, modelos ML, auth.js, config.js ni configuración de servidores.

La rama aún debe reconciliar sus archivos compartidos con main mediante una integración revisada posterior. Este trabajo no hizo merge ni sustituyó archivos del main remoto.

## Archivos de implementación modificados o creados en este rediseño

| Archivo | Cambio |
|---|---|
| frontend/components/chatbot.js | Vista integrada, herramientas, historial persistente y notificaciones del servicio. |
| frontend/css/chatbot.css | Diseño completo responsive, tipografía, tarjetas, conversación y entrada inferior; conserva estilos de reportes/ML. |
| frontend/js/chatbot-init.js | Inicialización idempotente. |
| frontend/js/panel-comun.js | Menús por rol y montaje compartido en páginas funcionales. |
| frontend/js/panel-navigation.js (nuevo) | Drawer académico accesible y cierre con Escape. |
| frontend/css/panel-navigation.css (nuevo) | Sidebar SENATI y comportamiento móvil, sin afectar administración. |
| frontend/js/chatbot-legacy-page.js (nuevo) | Integra la página heredada de asistencia sin modificar su componente de cámara. |
| frontend/estudiante/asistencia.html | Cuatro scripts de montaje; cámara y consentimiento conservados. |
| frontend/components/proactive.js | Apertura directa del centro con #notificaciones. |
| frontend/package.json | Comando test:workspace. |

Pruebas actualizadas para la apertura automática y el diseño sin modal:

- frontend/tests/chatbot.voice.test.mjs
- frontend/tests/parte7.chrome.test.mjs
- frontend/tests/parte7.live-demo.test.mjs
- frontend/tests/parte7.ml.chrome.test.mjs
- frontend/tests/parte7.proactive.chrome.test.mjs
- frontend/tests/parte7.reports.chrome.test.mjs

Pruebas nuevas:

- frontend/tests/parte7.workspace.chrome.test.mjs
- frontend/tests/parte7.workspace.live.test.mjs

También se generaron este documento, capturas y workspace-verificacion.json. Los archivos de las fases anteriores y los documentos de DevOps ya estaban pendientes; no deben atribuirse todos los cambios del worktree a este rediseño.

## Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| backend/tests/parte7 | 256 aprobadas; un aviso de deprecación TestClient/httpx. SQLite aislado, MySQL bloqueado. |
| chatbot.voice.test.mjs | Aprobada: consentimiento, transcripción, cancelación, permiso denegado, cierre y texto alternativo. Audio simulado. |
| parte7.chrome.test.mjs | 72 comprobaciones aprobadas en Chrome real. API/audio simulados explícitos. |
| parte7.workspace.chrome.test.mjs | 250 comprobaciones aprobadas: 12 páginas funcionales, cuatro roles, geometría, retorno, borrador, historial, menú y notificaciones. Fixtures de interfaz identificadas. |
| parte7.workspace.live.test.mjs | 29 comprobaciones aprobadas contra FastAPI/JWT/SQLite reales de la demo: cursos, historial, vista amplia y reporte académico calculado. |
| parte7.proactive.chrome.test.mjs | Revisión anterior: 42 comprobaciones aprobadas (no repetidas en el ajuste visual de la captura): centro, confirmación, duplicados, reportes, borradores y recordatorio ejecutado con Chrome cerrado. |
| parte7.reports.chrome.test.mjs | 44 comprobaciones aprobadas: vista previa, Excel/PDF/Word reales, impresión, datos vacíos, períodos y permisos. |
| parte7.ml.chrome.test.mjs | 60 comprobaciones aprobadas: resultados guardados, explicaciones, estados pendientes, permisos y reportes. |
| parte7.live-demo.test.mjs | Conversación saludo → cursos → ranking → octubre aprobada con backend real de demostración. |
| Sintaxis JavaScript y git diff --check | Aprobadas. |
| Integración antigua Segmentación/EmoScan | **Bloqueada antes del navegador**: preparar_segmentacion.py importa DEFAULT_DATA de segmentacion.segmentacion_kmeans, donde no existe. No se modificó ese algoritmo para forzar la prueba. |

En la revisión con la captura se repitieron 455 comprobaciones Chrome con conteo (72 + 250 + 29 + 44 + 60), además de la prueba de voz y la conversación contextual. Las 42 comprobaciones del centro proactivo corresponden a la revisión anterior. No se afirma que todas las pruebas del repositorio estén aprobadas. Los dos errores de fixtures heredados documentados en AUDITORIA_PUBLICACION.md tampoco se corrigieron en este rediseño.

La regresión antigua inicialmente también carecía de Matplotlib en el entorno aislado. Se instalaron sus dependencias en TEMP/monitor-parte7-tools/plot-deps para intentar ejecutarla, sin modificar requirements ni el entorno base. Superado eso, apareció la incompatibilidad DEFAULT_DATA. No se publican dependencias temporales.

Durante la verificación se ajustaron esperas de DOM y de finalización de la animación móvil; no se sustituyeron verificaciones por capturas estáticas. El historial muestra un estado de carga mientras se consulta, para no presentar la lista anterior como actualización terminada.

### Páginas funcionales verificadas

Estudiante: asistencia.html, calificaciones.html, curso.html, cursos.html, emoscan.html, ia.html y perfil.html.

Profesor: curso.html, cursos.html, ia.html, perfil.html y segmentacion.html.

Hay cinco archivos heredados de profesor de cero bytes: asistencia.html, dashboard.html, estadisticas.html, estudiantes.html y modelos.html. No contienen una página autenticada implementada, no se modificaron y no se contabilizan como vistas funcionales. Se registran en workspace-verificacion.json.

## Capturas de pantalla

Directorio: docs/parte7/evidencias/.

- workspace-estudiante-{1920,1366,820,390}.png
- workspace-profesor-{1920,1366,820,390}.png

Son capturas reales de Chrome de la interfaz con fixtures identificadas; no son imágenes generadas ni demuestran acceso a datos reales.

Capturas adicionales con el backend real de demo (SQLite RAM):

- workspace-real-profesor-1920.png
- workspace-real-profesor-1366.png
- workspace-real-estudiante-820.png
- workspace-real-estudiante-390.png
- workspace-real-reporte-1366.png

La demostración usa exclusivamente datos sintéticos declarados. El reporte capturado contiene cuatro registros de Programación de octubre y 100% de asistencia calculado, incluyendo tardanzas; no es una cifra de producción.

Resoluciones probadas: 1920×1080, 1366×768, 820×1180 y 390×844. Se comprobaron sidebar, drawer, entrada visible y ausencia de overflow horizontal. En la primera iteración solo se recibió el adjunto de texto. La revisión actual sí utiliza la captura enviada después: se adaptaron su saludo horizontal, preguntas, fondo y mensajes a SENATI, conservando los datos del servicio.


## Ajuste con la captura recibida — 31/10/2026

Implementación adicional limitada a frontend/components/chatbot.js, frontend/css/chatbot.css y el nuevo frontend/assets/img/chatbot-waves.svg; también se ampliaron las dos pruebas workspace y se actualizaron este documento y las evidencias. El SVG es un fondo decorativo escrito en código; no sustituye gráficos de datos ni incorpora imágenes de otras marcas. Se conserva el robot original del proyecto.

| Referencia | Resultado implementado |
|---|---|
| Robot junto al saludo, nombre azul | Saludo horizontal con nombre de la sesión autenticada; se adapta al ancho móvil. |
| Cinco preguntas horizontales | Cinco botones con iconos SVG y preguntas por rol; una fila a 1366/1920, tres columnas en tablet y dos en móvil. |
| Fondo azul suave con ondas | Fondo vectorial ligero, sin fotografías ni marcas añadidas. |
| Preguntas a la derecha y respuestas a la izquierda | Burbuja azul e inicial del usuario; tarjeta blanca con borde tenue y robot del asistente. |
| Entrada inferior redondeada | Compositor compacto con micrófono, envío y botón + que abre herramientas reales de voz. Crece hasta 110 px al escribir varias líneas. |
| Sidebar oscuro | Menú SENATI existente, rutas conservadas y módulos del profesor pendientes sin enlaces rotos. |
| Datos ilustrativos de la imagen | No se copiaron. Las capturas integradas muestran los cálculos de la base sintética local y su procedencia. |

El saludo permanece en el flujo de conversación y se desplaza con el historial. Las respuestas extensas pueden desplazarlo fuera de la vista, especialmente a 1366×768; no se ocultan etiquetas por CSS. El compositor permanece fuera de ese scroll.

Capturas de comparación, tomadas en Chrome real con el backend de prueba y sin interceptar la respuesta académica:

- [Conversación a 1920×1080](evidencias/workspace-referencia-conversacion-1920.png).
- [Conversación a 1366×768](evidencias/workspace-referencia-conversacion-1366.png).
- [Inicio del estudiante a 1366×768](evidencias/workspace-estudiante-1366.png).
- [Inicio del profesor a 1366×768](evidencias/workspace-profesor-1366.png).
- [Adaptación móvil a 390×844](evidencias/workspace-estudiante-390.png).

En estas conversaciones se seleccionó Matemática y se pidió el porcentaje histórico: 8 registros sintéticos, 5 presentes, 2 tardanzas y 1 ausencia; el servicio calcula 87,5% contando presentes más tardanzas. Los valores no están escritos en el JavaScript del producto. Las capturas welcome usan fixtures explícitas para comprobar geometría, no datos de estudiantes reales.

La prueba ampliada comprueba las cinco preguntas, su fila de escritorio, la disposición robot/saludo, el botón de voz, la inicial autenticada y la conservación del saludo al conversar. No hubo errores JavaScript ni desbordamiento horizontal en las cuatro resoluciones verificadas.

Durante la prueba integrada se corrigió una expectativa del test: “¿Cuántas faltas tengo?” sin período se clasifica actualmente como ATTENDANCE_TODAY, no COURSE_STATS. No se modificó esa lógica del backend en este trabajo visual. Para consultar ausencias históricas, especificar el período, por ejemplo “Genera el reporte de faltas de septiembre”. La captura final verifica la consulta de porcentaje histórico; no se añadieron cifras para imitar la imagen.

La prueba de voz usa dobles de reconocimiento y síntesis. Permiso, transcripción, cancelación y alternativa de texto pasaron; un micrófono físico y la disponibilidad del reconocimiento de Chrome en el equipo siguen pendientes de prueba manual.

## Cómo revisar en Chrome

1. Abrir http://127.0.0.1:8017/ y elegir Profesor o Estudiante para iniciar una identidad SINTÉTICA.
2. La ruta de ese rol abre la vista amplia automáticamente:
   - http://127.0.0.1:8017/frontend/profesor/ia.html
   - http://127.0.0.1:8017/frontend/estudiante/ia.html
3. Cerrar con × o Escape. El menú sigue disponible. Desde cualquier página funcional del rol, pulsar el robot para abrirlo sin cambiar de URL.
4. Probar “Muéstrame mis cursos”, cerrar/reabrir y consultar Historial. Pulsar Nueva conversación y comprobar que la pregunta anterior permanece en Historial.
5. Profesor: seleccionar Programación y pedir “Genera el reporte de asistencia de mi curso de octubre”; revisar y descargar Excel/PDF/Word. El origen sintético debe quedar visible.
6. Abrir Voz del asistente. La lectura está apagada por defecto. Para dictar, pulsar micrófono, confirmar el uso y conceder el permiso del navegador; comprobar transcripción, cancelar, detener y repetir. Las pruebas automatizadas no validaron un micrófono físico ni el servicio de transcripción de cada equipo.
7. Usar DevTools para las cuatro resoluciones; en móvil abrir/cerrar el menú con ☰ y Escape, y comprobar que el campo de texto permanece visible.

La demo no incorpora todos los servicios académicos del proyecto principal; algunas páginas subyacentes pueden indicar servicio no disponible. Esas respuestas no se reemplazaron con datos falsos. Para validar contra el sistema completo se necesita la integración segura pendiente; no utilizar credenciales de producción para esta revisión visual.

Para repetir la prueba nueva de interfaz con herramientas instaladas en el frontend: npm run test:workspace. La prueba integrada requiere además la demo local activa: node frontend/tests/parte7.workspace.live.test.mjs.

No se probó una cámara o micrófono físico y no se afirma que funcionen. Los tres stash se conservan y no se hicieron commits ni pushes.
