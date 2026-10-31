# Parte 7 · Fase 2: conversación contextual y voz

## Resultado

Se amplió el mismo router y componente SENATI de la fase 1. No hay un segundo chatbot.
Se mantienen el aislamiento de cuentas, la concesión institucional explícita y las consultas SQLAlchemy acotadas.
No se modificaron la red neuronal, K-Means, EmoScan, MySQL ni otras ramas. Sin commits, pushes o merges.

## Probar ahora, sin credenciales ni datos reales

La demostración local está disponible en:

**http://127.0.0.1:8017/**

1. Abrir Chrome y pulsar **Probar como profesor** o **Probar como estudiante**.
2. Pulsar **Abrir asistente** o el botón del robot.
3. Escribir o dictar esta secuencia, esperando cada respuesta:
   - Hola.
   - ¿Cuáles son mis cursos?
   - ¿Y cuál tiene más tardanzas?
   - Muéstrame los registros de octubre.
4. Revisar que Programación gana el ranking de los registros sintéticos, queda seleccionado y que el seguimiento muestra únicamente sus registros de octubre.
5. Probar «¿Y en noviembre?», «Gracias», «Hasta luego» y **Restablecer contexto**.
6. Cambiar un curso en el selector: se borra la selección de estudiante para evitar una combinación incompatible.

La demo reutiliza FastAPI, el router, los JWT, la política y las consultas reales contra SQLite en memoria. No simula respuestas del backend. Sus observaciones académicas son ficticias. Los datos se generan para octubre del año del proceso; indicar un año diferente puede devolver cero registros, correctamente.

MySQL está bloqueado por un listener y Gemini está desactivado en el proceso de la demo. No se importa `app.main`, no se ejecuta su lifespan ni se activan módulos de cámara, modelos o automatizaciones al iniciar.
Las sesiones demo son públicas solo para cuentas ficticias del proceso local y no sirven para acceder a otros servidores. No usar esta aplicación de demostración en producción ni exponerla fuera de loopback.
La configuración del frontend se responde desde la demo usando su propio origen; `frontend/js/config.js` y la configuración de los servidores existentes no se modifican.

Direcciones internas, después de elegir la cuenta en la portada:

- Profesor: http://127.0.0.1:8017/frontend/profesor/ia.html
- Estudiante: http://127.0.0.1:8017/frontend/estudiante/ia.html
- Salud: http://127.0.0.1:8017/api/health

### Volver a iniciar la demo

Desde el worktree `monitor-asistencia-parte7`, con Python 3.12 y las dependencias del chatbot:

```powershell
python -B -m uvicorn parte7_demo:app --app-dir backend --host 127.0.0.1 --port 8017
```

No iniciar `app.main` para esta demostración. Si el puerto está ocupado, identificar su proceso antes de tomar cualquier acción; no cerrar servidores ajenos. La demo pierde su BD y sus tokens al terminar el proceso.
En esta sesión se ejecutó con el Python ya instalado en `C:UsersJakelin.Cullampe.venvsp6Scriptspython.exe`, sin modificar ese entorno.

## Probar conversación por voz

1. Desplegar **Voz del asistente** y marcar **Leer respuestas**. Está desactivado inicialmente.
2. Elegir una voz en español, si el navegador ofrece varias. La lista se actualiza con `voiceschanged`; si no hay voces enumeradas, se solicita español al motor del navegador, sin garantizar que el equipo lo tenga instalado.
3. Pulsar el micrófono y aceptar la explicación **Permitir micrófono**. A continuación, permitir el acceso en el aviso de Chrome. Si no se desea usarlo, elegir **Seguir con texto**.
4. Hablar. La transcripción parcial aparece en el cuadro de entrada y la final aparece en la conversación, marcada como transcrita desde la voz. Al terminar se envía solamente el texto.
5. Verificar que la respuesta completa sigue visible y que se escucha si la voz está habilitada y disponible.
6. Probar **Silenciar**, **Detener reproducción** y **Repetir respuesta**. Silenciar cancela la lectura y no acumula respuestas para reproducir después. Repetir lee la última respuesta completa.
7. Durante la reproducción el micrófono está bloqueado. Tras detener o finalizar hay un breve margen de 250 ms; volver a pulsarlo manualmente. Nunca se reactiva solo.
8. Cerrar con Escape o el botón de cierre: debe detenerse el audio y cancelarse la captura. Salir de la página también cancela ambos.

Se conserva `SpeechRecognition`/`webkitSpeechRecognition` con es-PE y se añade `speechSynthesis`/`SpeechSynthesisUtterance`. No se usa MediaRecorder ni se guardan grabaciones. El proveedor de reconocimiento del navegador puede procesar audio externamente: la confirmación lo advierte. La aplicación conserva preguntas y respuestas en texto según la política de historial existente; en la demo esa tabla vive solo en RAM.
La voz necesita localhost o HTTPS y depende de las capacidades/permisos del navegador. Todo el asistente sigue disponible por texto, Enter, Tab y Escape, sin habilitar audio.

## Conversación y memoria temporal

- Intenciones locales cerradas para saludos, agradecimientos, despedidas, cursos, ranking de tardanzas, registros, estadísticas, próxima clase y las consultas existentes.
- Las preguntas de seguimiento conservan curso, estudiante, período e intención académica previa. «Gracias» no sustituye la intención previa para un seguimiento posterior por mes.
- Contexto firmado con propósito propio y clave derivada del secreto del backend. Incluye cuenta, huella del ámbito, IDs de selección, fechas y caducidad; no incluye grabaciones ni una copia del diálogo.
- Dura **20 minutos desde el último turno correcto**. Se mantiene solo en una variable de la pestaña, sin guardarlo en localStorage/sessionStorage ni en MySQL. Una recarga/salida o Restablecer contexto lo elimina del cliente.
- La firma protege su integridad, no cifra sus campos. No debe colocarse en URLs ni logs. No sirve como token de autenticación.
- En cada mensaje se vuelven a consultar rol, usuario activo, cursos y matrículas. Un contexto de otra cuenta se deniega; uno caducado, alterado o con permisos cambiados requiere restablecerse (409). La interfaz lo descarta y permite reenviar con filtros revisados.
- Restablecer el contexto no borra el historial. **Nueva conversación** conserva el comportamiento existente de borrar el historial propio y además limpia la memoria de la pestaña.

La interpretación reconoce meses en español, un año explícito, hoy, ayer, este mes y mes pasado. El mes sin año usa el año actual y se muestran siempre las fechas inclusivas consultadas. Los rangos explícitos se validan y no pueden superar 367 días inclusivos.
Los filtros vacíos enviados explícitamente eliminan selecciones; un campo omitido conserva su valor temporal. Un nombre natural puede cambiar una selección recordada, pero no contradecir un ID seleccionado explícitamente ni ampliar permisos.
Los empates del ranking se explican, sin escoger arbitrariamente un ganador. Cuando existe un ganador único con tardanzas, se selecciona para el siguiente turno y se anuncia ese cambio.

### Límites actuales

Es un intérprete determinista mejorado, no comprensión universal de español. Fechas compuestas, intervalos escritos libremente, múltiples entidades y frases ambiguas pueden necesitar selección o reformulación. Los filtros de período se aplican a registros, estadísticas y ranking; las consultas predictivas mantienen el contrato previo de próxima sesión y no constituyen una nueva integración de Parte 6.
El contexto firmado es stateless: descartar su copia en el navegador no revoca retroactivamente otras copias válidas dentro de su TTL. Solo funcionan en la misma cuenta y siguen sujetos al ámbito vigente.

## Sistema híbrido y Gemini

Se conserva Gemini opcional para **redactar** el resultado académico ya autorizado. No se necesita una clave para conversar, resolver el contexto o consultar datos.
El intérprete estructurado y la política local deciden la operación y el ámbito; Gemini no genera SQL, no recibe herramientas de base de datos, no modifica permisos ni ejecuta acciones.
El contexto firmado se añade después de la redacción y no se envía al proveedor. La demostración local lo mantiene desactivado; las pruebas de ese proveedor usan un transporte simulado. No se afirma haber comprobado su disponibilidad real ni su exactitud semántica.

## Archivos de esta fase

Backend:

- `app/schemas/chatbot.py`: campos opcionales de contexto y fechas, validación de rango.
- `app/services/chatbot_conversation.py`: intenciones estructuradas, períodos y contexto firmado.
- `app/services/chatbot_service.py`: integración con las consultas existentes y ranking autorizado.
- `app/api/chatbot.py`: preparación y devolución del contexto; Gemini sigue después de la autorización.
- `parte7_demo.py`: demostración local aislada con datos sintéticos en RAM.
- `tests/parte7/test_conversation.py` y `test_demo.py`.

Frontend:

- `components/chatbot.js`, `css/chatbot.css`: controles, consentimiento, contexto visible y lectura fragmentada completa.
- `js/chatbot-init.js`: conserva el status HTTP para recuperarse de contexto vencido.
- `js/panel-comun.js`, `profesor/ia.html`, `estudiante/ia.html`: entrada al mismo asistente desde ambos roles y ajuste de menú móvil limitado a esas páginas.
- `package.json`, `package-lock.json`: dependencias reproducibles de pruebas.
- `tests/chatbot.voice.test.mjs`, `parte7-tools.mjs`, `parte7.chrome.test.mjs`, `parte7.live-demo.test.mjs`.

Se mantienen también los archivos y pruebas de seguridad añadidos en la fase 1, todavía sin commit.

## Pruebas realizadas

| Comprobación | Resultado |
| --- | --- |
| `python -B -m pytest backend/tests/parte7 -q -p no:cacheprovider` | **88 aprobadas**. Una advertencia de obsolescencia Starlette/AnyIO. |
| `node --check frontend/components/chatbot.js` | Sin errores de sintaxis. |
| `node frontend/tests/chatbot.voice.test.mjs` | Pasa: panel, transcripción parcial/final, envío, consentimiento, cancelación, permiso denegado, cierre y alternativa de texto. |
| `node frontend/tests/parte7.chrome.test.mjs` | **72 comprobaciones aprobadas** en Chrome real: 1366×768, 1920×1080 y 390×844, sin errores JavaScript ni desbordamiento horizontal. API y audio simulados para probar estados de reproducción y micrófono sin hardware. |
| `node frontend/tests/parte7.live-demo.test.mjs` | Pasa: Chrome → FastAPI → JWT → SQLAlchemy → SQLite reales, conversación completa. No se simulan respuestas académicas; los registros son sintéticos. No se activa audio ni micrófono físico. |
| `git diff --check` | Sin errores de espacios. |

La suite backend incluye las 58 regresiones de seguridad anteriores y nuevos casos de español, continuidad, cambios naturales y manuales de selección, períodos, firma/caducidad, aislamiento por cuenta, revocación y protección ante propiedades falsas. La demo además verifica que no se pueda consultar el curso/estudiante externo.

### Repetir frontend

Con Node 24 LTS y Chrome instalados, desde `frontend/`:

```powershell
npm ci
npm run test:chatbot
# Con la demo local ya iniciada:
node tests/parte7.live-demo.test.mjs
```

No se descarga otro navegador: Playwright usa Chrome instalado (`channel: chrome`). En esta sesión Node 24.22.2 se descargó de nodejs.org y se comprobó su SHA256; Node y los paquetes de herramientas se alojaron en la carpeta temporal `monitor-parte7-tools`, sin cambiar la instalación del sistema ni servidores existentes.
Las pruebas admiten `MONITOR_TEST_NODE_MODULES` apuntando a esa carpeta temporal; si se omite, usan las dependencias locales de `npm ci`. La prueba live admite `MONITOR_LIVE_DEMO_URL` y rechaza backends que no identifiquen SQLite en memoria y MySQL bloqueado.

### Evidencias y pruebas pendientes

- [Conversación con backend real y datos sintéticos](evidencias/demo-conversacion.png).
- [1366×768](evidencias/chatbot-1366.png), [1920×1080](evidencias/chatbot-1920.png), [390×844](evidencias/chatbot-390.png). Estas tres capturas corresponden a las pruebas con API/audio simulados y están identificadas aquí como tales.
- Pendiente manual: comprobar sonido audible, la voz española instalada y el micrófono físico de este equipo, así como el aviso de permiso real de Chrome. No se afirma que el hardware haya funcionado.
- No se ejecutó la suite completa de todos los módulos ni se realizaron consultas contra MySQL o Gemini reales.

## Referencias

- [MDN: SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis) y [voiceschanged](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/voiceschanged_event).
- [Google: salidas estructuradas](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en). Referencia para una ampliación futura del intérprete; esta fase mantiene la interpretación local y la redacción opcional existente.
