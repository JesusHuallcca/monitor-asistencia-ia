# Verificación de fase 4 — integración ML

Fecha: 2026-10-31. Worktree monitor-asistencia-parte7, rama parte-7-chatbot-inteligente.

## Resultados ejecutados

| Verificación | Resultado |
|---|---|
| Python: pytest backend/tests/parte7 -q -p no:cacheprovider | **198 aprobadas**; incluye 58 casos ML nuevos y las pruebas de fases anteriores. |
| JavaScript: node --check frontend/components/chatbot.js | Correcto. |
| chatbot.voice.test.mjs | Aprobado: transcripción, cancelación, denegación y alternativa de texto. Audio simulado, sin micrófono físico. |
| parte7.chrome.test.mjs | **72 comprobaciones aprobadas**. Chrome real; API y voz simuladas. |
| parte7.reports.chrome.test.mjs | **44 comprobaciones aprobadas**. Chrome → FastAPI → JWT → SQLite reales; tres descargas, PDF imprimible, roles, períodos y datos vacíos. |
| parte7.live-demo.test.mjs | Aprobado: saludo → cursos → ranking de tardanzas → registros de octubre, con backend y permisos reales de la demo. |
| parte7.ml.chrome.test.mjs | **60 comprobaciones aprobadas**. Chrome → FastAPI → JWT → SQLite reales; consultas ML, contexto del modelo, permisos, estados pendientes, tres descargas y responsive. |
| git diff --check | Correcto. |

Resoluciones Chrome: 1366×768, 1920×1080 y 390×844. Sin errores JavaScript ni desbordamiento horizontal de la página. Las tablas amplias mantienen desplazamiento dentro de su contenedor. Se inspeccionaron visualmente las capturas de escritorio y móvil.

Un aviso de deprecación de Starlette/TestClient sobre httpx; no provoca fallos. No se cambiaron dependencias ajenas para eliminar ese aviso.

## Casos relevantes

- Lectura de artefactos K-Means: 150 perfiles, K=3, silueta 0.2373692496101911, cuatro variables y grupos 45/60/45.
- Validación de origen, variables, fuente SHA256, perfiles únicos, conteos y medias. Ante archivos ausentes, NaN, origen facial, hash o resumen inconsistentes, se responde no disponible.
- Pruebas prohíben fit en KMeans, StandardScaler y PCA al consultar resultados.
- Rechazo de IDs de cursos/estudiantes ajenos, administradores sin concesión, rol falsificado e inferencia neuronal por estudiante.
- Revocación de asignación antes de invocar el proveedor neuronal; no hay invocación tras perder acceso.
- Parte 6 ausente o con historial bloqueado: sin probabilidad. Respuestas de proveedor incompatibles, probabilidad NaN, corte inválido, versión vacía o excepción: no disponible.
- Regresión consulta únicamente historial del curso autorizado y notas calificadas anteriores al corte. Excluye una nota futura del mismo curso y notas de otros cursos. Sin notas, no imputa 14.
- Los proveedores de inferencia disponibles son **dobles explícitos en pruebas**, no modelos ejecutados en producción ni métricas neuronales nuevas.
- Gemini no interviene en las respuestas ML.
- Los tres formatos se generaron realmente y se abrieron con openpyxl, pypdf y python-docx; propiedad y autenticación de descargas comprobadas.
- Los seguimientos preservan el modelo seleccionado y el snapshot de reporte. Un reporte académico posterior conserva su funcionamiento.

## Disponibilidad y preservación

La demo queda en http://127.0.0.1:8017/, loopback, SQLite en memoria, MySQL bloqueado y Gemini desactivado. No contiene estudiantes reales.

Regresión: métricas archivadas disponibles; artefacto de inferencia ausente. Origen de entrenamiento no acreditado por manifiesto.
Parte 6: pendiente de integración en Parte 7; revisión de la rama remota documentada, sin copiarla ni hacer merge.
No se ejecutaron entrenamiento, conexiones MySQL, commits o pushes. Los tres stash y las referencias protegidas permanecieron intactos.

Contratos, variables y dependencias: [FASE4_INTEGRACION_ML.md](FASE4_INTEGRACION_ML.md).
