> La distribución por pestañas descrita aquí fue sustituida. Consulta [DASHBOARD_SEGMENTACION.md](DASHBOARD_SEGMENTACION.md) para la página única actual.

# Rediseño de Segmentación IA

Trabajo local en monitor-asistencia-integracion-segmentacion, rama integracion-segmentacion-ia.
No cambia el algoritmo, los endpoints, MySQL, EmoScan personal, reconocimiento facial ni login.

## Cómo visualizarlo

Con el frontend en 8001 y el backend autenticado en 8000, iniciar sesión como profesor en
http://127.0.0.1:8001/login.html y abrir
http://127.0.0.1:8001/profesor/segmentacion.html.
Recargar con Ctrl+F5 si el navegador conserva el controlador anterior.

1. Ver demostración calcula la entrega de Parte 3 a través de la API protegida.
2. Cargar CSV sintético despliega un área separada, con selección/arrastre, formato,
   límites y errores. Las expresiones se generan en el backend; no se suben datos faciales.
3. Resumen presenta cuatro tarjetas, distribución y medias descriptivas por cluster.
4. Explorar clusters muestra PCA con tooltip de las cuatro variables. La barra del gráfico
   permite zoom, desplazamiento, recuadro y lazo; pulsar un punto lo selecciona.
5. Comparar variables permite cambiar X e Y. Ratios se visualizan de 0 a 100 %,
   notas de 0 a 20. Las cuatro barras mantienen sus escalas separadas.
6. Evaluación K-Means muestra inercia y silueta para cada K. La elección y los textos
   se calculan desde metricas y evaluacion_k: máxima silueta entre K >= 3.
   Para la demostración el mejor global es K=2, el elegido es K=3 y la silueta 0.2374
   no representa 23.74 % de precisión.

El selector global y la leyenda controlan los grupos visibles entre pestañas.
El contador indica perfiles en esos grupos, no el número de puntos dentro del zoom.
La selección de puntos se muestra aparte, con hasta 12 filas en la tabla de detalle.
Restablecer vista recupera grupos, selección y encuadre; conserva los ejes elegidos.
Descargar resultados entrega todos los perfiles del resultado procesado, aunque haya filtros.

Las tarjetas y la evaluación corresponden al dataset completo. Filtrar no vuelve a entrenar
el modelo. No se atribuyen emociones internas, atención, riesgo ni causas a los clusters.
Las medias, tamaños, varianza PCA y explicaciones numéricas proceden de la respuesta JSON.

Al elegir otro CSV se purgan figuras, métricas, selección y textos del resultado anterior.
Al procesarlo correctamente se reconstruyen los filtros, ejes y gráficos y se abre Resumen.
Los errores de CSV, red o respuesta inválida nunca dejan visible un resultado anterior.
Las actualizaciones de Plotly se serializan y los eventos programáticos de selección
no borran la selección del usuario.

## Archivos

Modificados:
- frontend/profesor/segmentacion.html: estructura, pestañas, controles y accesibilidad.
- frontend/js/segmentacion.js: carga existente, Plotly, filtros y explicaciones dinámicas.
- frontend/tests/integracion-final.test.cjs: conecta las comprobaciones del dashboard nuevo;
  conserva el bloque de pruebas del estudiante.
- INTEGRACION_FINAL.md: instrucciones y fixtures de las pruebas actualizadas.
- RESULTADOS_INTEGRACION.md: referencia al informe de este rediseño.

Nuevos:
- frontend/css/segmentacion-dashboard.css: estilos exclusivos del dashboard; la hoja
  segmentacion.css compartida con EmoScan se conserva intacta.
- frontend/vendor/plotly-basic-2.35.2.min.js y plotly-locale-es-2.35.2.js:
  biblioteca y traducción servidas localmente, sin peticiones a CDN al usar la interfaz.
- frontend/vendor/PLOTLY-LICENSE.txt y PLOTLY.md: licencia MIT y procedencia.
- frontend/tests/segmentacion-dashboard.checks.cjs: pruebas de interacción con ratón y teclado.
- frontend/tests/preparar_segmentacion.py: fixtures calculadas por el modelo real.
- REDISENO_SEGMENTACION.md: esta guía y registro de verificación.

## Repetir las pruebas

Desde la raíz, con requirements-integracion.txt instalado:

~~~powershell
.\.venv\Scripts\python.exe -m pip install pytest playwright
.\.venv\Scripts\python.exe -B -m pytest backend/tests/integracion_final backend/tests/emoscan -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m unittest discover -s segmentacion -t . -v
.\.venv\Scripts\python.exe -B frontend/tests/preparar_segmentacion.py
~~~

La regresión real de FERPlus requiere el modelo incluido y la fotografía pública de NASA
de las pruebas originales, ignorada por Git. Si falta, prepararla explícitamente con
python integraciones/emoscan/descargar_imagen_prueba.py. No se utilizan fotos de estudiantes.

Para JavaScript se puede usar Node y Playwright instalados en frontend:

~~~powershell
cd frontend
npm install
npx playwright install chromium
npm run test:integration
node tests/emoscan.test.js
~~~

El test busca por defecto segmentacion/.cache/demo_api.json y demo_api_small.json.
Se pueden proporcionar rutas alternativas con SEGMENTATION_FIXTURE y SEGMENTATION_SMALL_FIXTURE.
CHROME_EXECUTABLE permite usar Chrome instalado; PLAYWRIGHT_MODULE permite señalar
el paquete playwright-core del runtime local de Playwright.
QA_ARTIFACTS habilita capturas en un directorio local ignorado.

El navegador utiliza figuras Plotly reales y gestos de ratón/teclado. Solo el transporte
de autenticación/API se sustituye por respuestas de prueba calculadas desde el algoritmo
para 150 y 20 perfiles. Los endpoints y roles se comprueban además en FastAPI con SQLite
en memoria y conexiones MySQL bloqueadas. El vídeo e inferencia personal son dobles de
prueba de la regresión existente. No equivalen a una prueba de cámara física.

Los resultados finales y límites de la ejecución se agregan debajo.


## Resultado de la verificación final (26 de octubre de 2026)

| Verificación | Resultado |
|---|---|
| Integración y regresiones Python | 63 pruebas aprobadas, 38.11 s |
| K-Means definitivo | 10 pruebas aprobadas, 25.281 s |
| Chrome real, escritorio y móvil | 60 comprobaciones aprobadas |
| Regresión JavaScript de asistencia opcional | 14 comprobaciones aprobadas |
| Total | 73 pruebas Python y 74 comprobaciones JavaScript |
| Demostración calculada | 150 perfiles, K=3, silueta 0.2373692496101911 |
| Integridad de módulos protegidos | Hashes sin cambios |
| Referencias de Git y tres stashes | Sin cambios |

Se comprobaron con ratón real de Playwright: tooltip, clic en un perfil, recuadro de
selección múltiple, zoom, desplazamiento, restablecimiento y ocultación desde la leyenda.
También se comprobaron filtros entre pestañas, ejes/unidades, medias, curvas, teclado,
carga por arrastre, rechazo de archivos, descarga íntegra, cambio de 150 a 20 perfiles,
purga de datos previos y recuperación tras una respuesta inválida.
Las cuatro pestañas se verificaron a 390 px; las capturas de escritorio usan 1440 px.

El transporte del navegador usa fixtures calculadas con el backend real. No se probó
un login de usuario real ni la carga autenticada contra MySQL en esa prueba de Chrome.
Los endpoints y roles se probaron por separado en SQLite en memoria; MySQL fue bloqueado
en esas suites. No se cambió la base de datos ni se conectaron expresiones reales.
No se necesitó una cámara física para este rediseño.

Disponibilidad comprobada al finalizar: la página del profesor en 8001 y /api/health
en 8000 respondieron HTTP 200. El acceso al análisis sigue requiriendo sesión de profesor.

Registros y capturas locales, excluidos de Git:
- segmentacion/.cache/redisenio/python-tests.log
- segmentacion/.cache/redisenio/kmeans-tests.log
- segmentacion/.cache/redisenio/browser-tests.log
- segmentacion/.cache/redisenio/emoscan-js-tests.log
- segmentacion/.cache/redisenio/qa/segmentacion-profesor.png
- segmentacion/.cache/redisenio/qa/segmentacion-movil.png

Se conservaron los hashes de backend, segmentacion, integraciones, database, login,
EmoScan y las hojas compartidas. Solo la prueba general de navegador se adaptó para
conectar el nuevo bloque de pruebas del dashboard; la pantalla del estudiante no cambió.
git diff --check finalizó correctamente. Sin commits ni pushes.
