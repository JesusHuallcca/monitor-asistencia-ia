# Parte 7 · Fase 3: reportes académicos inteligentes

## Qué se implementó

El mismo chatbot SENATI genera una vista previa verificada de cinco reportes: asistencia, tardanzas, ausencias, resumen académico y comparación entre períodos.
Se pueden pedir por texto o mediante la entrada de voz existente. La transcripción utiliza el mismo endpoint, los mismos permisos y los mismos cálculos.
La red neuronal, K-Means y EmoScan permanecen independientes. No se conectó ni modificó MySQL de producción. Sin commits, pushes ni merges.

## Probar desde Chrome

Abrir **http://127.0.0.1:8017/** y elegir **Probar como profesor** o **Probar como estudiante**.
La demostración usa SQLite en memoria, JWT y el router reales, tiene MySQL bloqueado y Gemini desactivado.
Al reiniciar la demo hay que volver a elegir la cuenta en la portada, porque cambia su clave temporal y se reinician datos, historial y reportes.

Profesor:

1. Abrir el asistente y seleccionar **Programación** en el filtro de curso.
2. «Genera el reporte de asistencia de mi curso de octubre».
3. Revisar título, origen, fechas, indicadores, gráfico, tabla y metodología. La tabla inicial muestra hasta 25 filas; los archivos contienen todas las filas autorizadas del reporte.
4. «Genera el reporte en Excel» → pulsar **Descargar Excel**.
5. «Ahora quiero el mismo reporte en PDF» → pulsar **Descargar PDF**.
6. «Descárgalo en Word» → pulsar **Descargar Word**.
7. **Imprimir PDF** abre el documento obtenido mediante autenticación en una pestaña con el visor del navegador; usar su icono de impresión o Ctrl+P. No se envía automáticamente nada a una impresora. Si Chrome bloquea la pestaña, permitirla o descargar primero el PDF.
8. Probar «Muéstrame una vista previa», «Muéstrame las tardanzas de esta semana», «Prepara el reporte de faltas de mis estudiantes», «Compara la asistencia de septiembre y octubre» y «Genera el resumen académico del curso».
9. Un seguimiento como «¿Y en noviembre?» conserva el tipo del reporte y cambia el período. «Genera un nuevo reporte» vuelve a consultar los datos; cambiar solo de formato reutiliza la instantánea anterior.

Estudiante:

- «Descarga mi historial de asistencia».
- «Genera mi resumen mensual».
- «Muéstrame mis tardanzas».

Solo se incluyen sus observaciones, incluso cuando comparte cursos con otros estudiantes.
Para usar voz, pulsar el micrófono y aceptar el consentimiento y el permiso de Chrome; la pregunta final transcrita genera la misma vista previa. La lectura de respuestas sigue siendo opcional. Las pruebas automatizadas no comprobaron micrófono, sonido ni impresora físicos.

## Datos de prueba y ejemplos entregables

La demo contiene observaciones sintéticas de septiembre y octubre del año del proceso. Programación tiene cuatro registros por mes.
Los tres ejemplos permanentes entregados corresponden al **mismo dataset autorizado** del curso Programación:

- [Excel real (.xlsx)](ejemplos/ejemplo-asistencia-autorizada.xlsx).
- [PDF real](ejemplos/ejemplo-asistencia-autorizada.pdf).
- [Word real (.docx)](ejemplos/ejemplo-asistencia-autorizada.docx).
- [Manifiesto y verificación](ejemplos/VERIFICACION.json).

La generación se hizo mediante POST autenticado para el profesor sintético, exportación protegida y descarga autenticada. Se abrieron con openpyxl, pypdf y python-docx.
Son ocho observaciones de Ana Sintético: dos PRESENTE, cinco TARDANZA y una AUSENTE. Asistencia: (2 + 5) / 8 = **87,5 %**. Los tres formatos llevan la misma huella SHA-256 del dataset, origen, período y fecha de generación; cada archivo tiene además su hash propio en el manifiesto.
Estas cifras describen exclusivamente el fixture de demostración. No son métricas de estudiantes reales.

Los ejemplos están guardados expresamente para esta entrega y contienen únicamente datos sintéticos. Las exportaciones normales del sistema no se guardan en esa carpeta ni en otros directorios públicos.

Regenerar y volver a verificar los ejemplos desde la raíz:

```powershell
python -B backend/parte7_report_examples.py
```

El script usa una instancia aislada de la demo en memoria. No necesita que el servidor esté ejecutándose ni usa credenciales reales.

## Dataset y metodología

`chatbot_reports.build_dataset` construye un snapshot JSON a partir de consultas SQLAlchemy parametrizadas y la política de `chatbot_security`.
Todos los exportadores reciben exclusivamente ese snapshot. No vuelven a consultar datos ni toman cifras de Gemini o JavaScript.
La huella SHA-256 se calcula sobre el JSON canónico con metadatos y fecha de generación. Cambiar de formato mantiene su contenido, filtros, cálculos y huella. Las modificaciones posteriores de datos no alteran el snapshot anterior; para reflejarlas se debe generar uno nuevo.

- La fecha de la sesión determina el período de asistencia.
- Se normaliza `TARDE` a `TARDANZA`.
- Asistencia = `(PRESENTE + TARDANZA) / (PRESENTE + TARDANZA + AUSENTE) × 100` sobre registros disponibles.
- No se crean ausencias por sesiones que no tienen observación. No se equipara cantidad de registros con cantidad de estudiantes.
- Estados desconocidos se muestran y cuentan por separado; se excluyen del denominador conocido.
- Tardanzas y ausencias filtran las filas del documento; los indicadores distinguen los registros base del ámbito de las filas de ese tipo. La metodología se incluye en los documentos.
- Sin denominador válido, el porcentaje es nulo y se muestra **Sin datos disponibles**. No se sustituye por 0 %.
- Sin filas del reporte no se crea un gráfico. En una comparación, un período sin registros queda identificado como sin datos, sin atribuirle una asistencia del 0 %.
- La comparación muestra cantidades y porcentajes por período y la diferencia en puntos porcentuales cuando ambos tienen denominador.
- El resumen académico incluye promedios por estudiante y curso, ponderados por pesos positivos de evaluaciones calificadas y disponibles al cierre. No mezcla notas de cursos ajenos. Aclara que no reconstruye versiones históricas de notas modificadas.
- El modelo actual trabaja con registros disponibles en la BD; no reconstruye una lista histórica de matrículas revocadas ni atribuye estados a estudiantes sin registros.

Los gráficos de la vista previa son barras/indicadores dinámicos accesibles y se calculan con el dataset recibido. XLSX incluye un gráfico nativo; PDF incluye barras vectoriales cuando la cantidad de grupos permite una leyenda legible. Word presenta tablas e indicadores con el mismo contenido verificado.

## Filtros e interpretación

- Curso y estudiante: selectores existentes y referencias naturales resueltas solo en el ámbito autorizado.
- Tipo de reporte: intenciones cerradas o `report_type` validado del endpoint directo.
- Período: meses/año, hoy, ayer, este mes, mes pasado, esta semana y semana pasada. La semana va de lunes a domingo.
- El mes sin año usa el año actual y las fechas resultantes quedan visibles. En «septiembre y octubre de 2025» se aplica el año compartido a ambos meses.
- Por defecto, un reporte nuevo usa el mes actual hasta hoy. El historial sin período explícito queda limitado a los últimos 366 días inclusivos. El usuario ve el rango aplicado.
- La comparación requiere dos meses o dos rangos explícitos no superpuestos. Dos meses sin intención de comparación requieren aclaración o fechas explícitas; no se elige silenciosamente uno.
- Si «mi curso» resulta ambiguo, se solicita seleccionarlo.

El intérprete sigue siendo determinista. Las frases no contempladas pueden requerir reformulación; no se afirma comprender cualquier formulación en español.

## API protegida

Todas las rutas reutilizan `get_current_user`, cuenta activa y el ámbito académico actual. Las URLs no contienen JWT ni contraseñas.

| Método y ruta | Función |
| --- | --- |
| POST `/api/chatbot/message` | Pide el reporte por texto/transcripción y devuelve la vista previa y el contexto temporal. |
| POST `/api/chatbot/reports` | Crea una vista previa con `ReportSpec`. |
| GET `/api/chatbot/reports/{id}` | Vuelve a consultar la vista previa propia, si sigue vigente. |
| POST `/api/chatbot/reports/{id}/exports/{xlsx\|pdf\|docx}` | Genera un formato desde el snapshot propio. |
| GET `/api/chatbot/reports/{id}/files/{xlsx\|pdf\|docx}` | Descarga un formato previamente generado, tras verificar nuevamente usuario y permisos. |

Ejemplo de cuerpo del endpoint directo:

```json
{
  "report_type": "asistencia",
  "course_id": 2,
  "period_start": "2026-09-01",
  "period_end": "2026-10-31"
}
```

Tipos admitidos: `asistencia`, `tardanzas`, `ausencias`, `academico`, `comparacion`.
Se permite `student_id` solo cuando está autorizado. Comparación agrega `compare_start` y `compare_end`. Los campos adicionales se rechazan.
La descarga del frontend usa `Auth.fetchAutenticado`, recibe un Blob y crea una URL local; no ofrece enlaces públicos a estudiantes. El PDF para imprimir sigue el mismo camino autenticado.
Las respuestas de archivo incluyen `Cache-Control: no-store, private`, `nosniff`, nombre fijo sin datos personales y `X-Report-Dataset-SHA256`.

## Seguridad y vencimiento

- ESTUDIANTE: únicamente su perfil y sus cursos matriculados.
- PROFESOR: cursos asignados y estudiantes matriculados en el curso correspondiente. Las consultas de asistencia y notas unen matrícula por par estudiante/curso.
- ADMIN/SUPERADMIN: lectura institucional solo con la concesión explícita de la fase 1.
- Identificadores aleatorios de 192 bits; conocer un ID no concede acceso. Otra cuenta recibe un rechazo genérico.
- Una huella del ámbito invalida snapshots cuando cambian rol, cursos o matrículas. Se revisa al consultar, generar archivo y descargar, y nuevamente después del renderizado.
- Snapshots y archivos viven solo en RAM y vencen a los **10 minutos**, incluso aunque el contexto conversacional dure 20. Un temporizador los elimina; las operaciones comprueban además el tiempo de forma síncrona.
- Un reinicio los elimina. El vencimiento impide nuevas consultas/descargas: no borra copias que el usuario ya haya descargado.
- Excel escribe todas las cadenas como texto literal y marca los prefijos peligrosos, incluso tras espacios/control. No hay CSV, macros, vínculos externos ni fórmulas construidas a partir de nombres. Los cálculos son valores de Python; las referencias internas del gráfico son controladas por el exportador.
- PDF escapa el texto antes de pasarlo a Paragraph; Word usa texto XML serializado por python-docx. No se aceptan plantillas o rutas de archivo del usuario.
- Los fallos del renderizador tienen un mensaje genérico, sin volcar nombres ni contenidos en el error HTTP.
- Auditoría: `monitor.chatbot.exports`, evento, formato y seudónimo HMAC de la cuenta. Sin preguntas, nombres de estudiantes, tokens, datos del reporte ni IDs de sus filas.
- Gemini no interviene en la generación, los cálculos, los archivos ni la autorización de estos reportes; el dataset no se envía al proveedor.

EmoScan no se consulta en esta fase. Los tipos emocionales no existen en el esquema y las solicitudes de informes emocionales, faciales o diagnósticos se rechazan. Cualquier futura integración requeriría consentimiento y permisos propios, sin diagnósticos emocionales ni uso automático para el profesor.

### Límites actuales

| Control | Límite |
| --- | --- |
| Rango total, incluyendo comparaciones | 366 días inclusivos; comparación sin superposición. |
| Cursos | 50; si se excede, seleccionar un curso. |
| Asistencias / calificaciones leídas | 2000 por conjunto; exceso rechazado, sin truncar cálculos. |
| Vista previa | Hasta 25 filas; documentos con todas las filas admitidas. |
| Dataset canónico | 2 MiB. |
| Archivo individual | 8 MiB. |
| Snapshots simultáneos | 32 por proceso. |
| Memoria agregada del almacén | 24 MiB. |
| Renderizados simultáneos | 2. |
| Creaciones de snapshot | 10 por cuenta/minuto. |
| Generaciones de formato | 6 por cuenta/minuto, incluso solicitudes repetidas al caché. |
| Descargas | 15 por cuenta/minuto. |
| Consultas de vista previa por GET | 30 por cuenta/minuto. |

Límites de memoria y caché son por proceso. Esta entrega debe ejecutarse con **un worker**; con varios workers hace falta un almacén privado compartido con TTL y límites distribuidos. No se añadió infraestructura de producción ni una migración MySQL.
Si el snapshot vence, generar un reporte indicando tipo y período o restablecer el contexto. No se reconstruyen ni entregan archivos vencidos de forma automática.

## Dependencias y ejecución

Se creó el entorno **independiente** `C:\Users\Jakelin.Cullampe\.venvs\p7`, Python 3.12. El entorno de Parte 6 quedó intacto.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-parte7-pruebas.txt
# Para reproducir exactamente el conjunto de versiones verificado:
# .\.venv\Scripts\python.exe -m pip install -r requirements-parte7-lock.txt
.\.venv\Scripts\python.exe -B -m uvicorn parte7_demo:app --app-dir backend --host 127.0.0.1 --port 8017
```

`requirements-parte7-reportes.txt`: dependencias del backend acotado y openpyxl, ReportLab, python-docx. `requirements-parte7-pruebas.txt` añade pypdf para validar PDFs. El lock registra las versiones del entorno probado.
No es necesario instalar TensorFlow, descargar modelos faciales, proporcionar credenciales cloud ni arrancar `app.main` para revisar la demo.

## Archivos principales de esta fase

- `backend/app/schemas/chatbot_reports.py`: contrato validado de filtros y rangos.
- `backend/app/services/chatbot_reports.py`: dataset, indicadores, comparación y vista previa.
- `backend/app/services/chatbot_report_store.py`: RAM, propiedad, TTL, límites y auditoría.
- `backend/app/services/chatbot_report_documents.py`: XLSX, PDF y DOCX desde el mismo dataset.
- `backend/app/api/chatbot_reports.py`: creación y descargas protegidas, integración conversacional.
- `backend/app/api/chatbot.py`, `chatbot_conversation.py`, `chatbot_service.py`: reutilización del router, contexto de reporte, períodos y validación de nombres/selecciones.
- `frontend/components/chatbot.js`, `frontend/css/chatbot.css`: vista previa, barras, tablas, botones y PDF imprimible; conserva voz y estilo SENATI.
- `backend/parte7_demo.py`, `parte7_report_examples.py`: fixtures y ejemplos aislados.
- `backend/tests/parte7/test_reports.py`, `frontend/tests/parte7.reports.chrome.test.mjs` y script npm `test:reports`.

## Pruebas y resultados

```powershell
python -B -m pytest backend/tests/parte7 -q -p no:cacheprovider
python -B backend/parte7_report_examples.py
# Node 24 LTS + Chrome; desde frontend y con la demo iniciada:
npm run test:reports
```

- **140 pruebas backend aprobadas**, incluidas las regresiones de las fases 1 y 2. Una advertencia de obsolescencia de Starlette TestClient/httpx, sin fallos.
- **44 comprobaciones de reportes en Chrome real**: tres descargas, apertura de PDF para imprimir, vista previa, comparación, datos vacíos, acceso por rol y tamaños 1366×768, 1920×1080 y 390×844. Se simula únicamente la entrada de reconocimiento de voz, sin micrófono físico; las respuestas académicas, la autenticación y los archivos provienen del backend real.
- Cálculos, filtros, año compartido, contexto, snapshot inmutable y renovación; archivos abiertos con lectores independientes; fórmulas peligrosas, marcado PDF/Word, datos ausentes, errores de render, volumen, concurrencia, frecuencia, vencimiento, revocación y descargas ajenas cubiertos por pruebas.
- Los tres ejemplos se generaron y verificaron mediante los endpoints protegidos; los SHA-256 y los cálculos constan en `ejemplos/VERIFICACION.json`.
- `git diff --check` sin errores de espacios. No se ejecutó la suite de todos los demás módulos ni se usaron servicios externos de IA o MySQL reales.

Las capturas `evidencias/reportes-1366.png`, `reportes-1920.png` y `reportes-390.png` corresponden al backend real con datos sintéticos. No prueban una impresora física ni voces audibles.

## Referencias técnicas

- [openpyxl: tratamiento de tipos de celda](https://openpyxl.readthedocs.io/en/3.1.2/_modules/openpyxl/cell/cell.html).
- [ReportLab: tablas y LongTable](https://docs.reportlab.com/reportlab/userguide/ch7_tables/).
- [python-docx: Document](https://python-docx.readthedocs.io/en/stable/).
