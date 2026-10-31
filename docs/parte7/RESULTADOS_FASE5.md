# Resultados — Parte 7, fase 5

Fecha: 2026-10-31. Rama parte-7-chatbot-inteligente.
Worktree exclusivo: monitor-asistencia-parte7.

## Comprobaciones ejecutadas

| Prueba | Resultado |
|---|---|
| pytest backend/tests/parte7 -q -p no:cacheprovider | **256 aprobadas**, incluidas 58 nuevas de proactividad y las 198 anteriores. |
| Sintaxis de chatbot.js y proactive.js | Correcta. |
| chatbot.voice.test.mjs | Aprobada; transcripción y síntesis simuladas, sin micrófono físico. |
| parte7.chrome.test.mjs | **72 comprobaciones aprobadas**, Chrome real con API/audio simulados. |
| parte7.proactive.chrome.test.mjs | **42 comprobaciones aprobadas**, Chrome/FastAPI/JWT/SQLite reales. |
| parte7.reports.chrome.test.mjs | **44 comprobaciones aprobadas**, backend real de demostración. |
| parte7.live-demo.test.mjs | Aprobada, conversación completa y ámbito académico. |
| parte7.ml.chrome.test.mjs | **60 comprobaciones aprobadas**, integración ML preservada. |
| parte7_proactive_examples.py | Aprobada: recordatorio y reporte semanal por APScheduler real, sin navegador, reloj lógico acelerado explícito. |
| git diff --check | Correcto. |

Resoluciones: 1366×768, 1920×1080 y 390×844. Sin errores JavaScript ni desbordamiento horizontal. Capturas de escritorio y móvil inspeccionadas; encabezado y sugerencias visibles, tarjetas en dos columnas o una en móvil.

Una advertencia de deprecación existente de Starlette/TestClient sobre httpx; ningún fallo.

## Evidencia funcional

- Fuentes verificadas de clase y evaluación; una evaluación no inventa hora de vencimiento.
- Propuestas visibles al abrir el dashboard; preparar una propuesta no crea ni activa una tarea.
- Borrador → revisión/confirmación → activa; edición, pausa, reactivación y estados registrados.
- Una configuración repetida conserva el mismo recordatorio y muestra su estado real.
- Recordatorio activado, proceso de Chrome cerrado completamente y notificación creada por el servidor antes de reabrirlo.
- Reporte semanal calculado desde observaciones autorizadas, con apertura protegida y descarga real.
- Reporte diario del día institucional anterior y límites correctos cuando el usuario tiene otra zona horaria.
- Resumen de estudiante exclusivamente propio; profesor solo sus cursos. Manipular IDs/roles/destinatarios no amplía permisos.
- Revocar asignación, desactivar cuenta, cancelar clase o cambiar fecha bloquea la ejecución.
- Umbrales de ausencias/tardanzas y deduplicación de condición sin cambios; sin imputar ausencias.
- Borradores de comunicaciones aprobados permanecen sin envío externo.
- Concurrencia de dos workers y reinicio con SQLite de archivo sintético: una sola notificación.
- Preferencias desactivadas, vencimiento y limpieza de notificaciones, auditoría minimizada y señal de worker activo/inactivo.
- Metadatos nuevos separados de Base; migración MySQL no aplicada automáticamente.

## Demostración y documentos

[FASE5_DEMOSTRACION.json](ejemplos/FASE5_DEMOSTRACION.json) contiene fuentes y hashes.
La demostración es independiente de la base en memoria del servidor vivo; usa un reloj lógico acelerado y no simula resultados de producción.

Reporte semanal: **26/10/2026–01/11/2026**, dos registros sintéticos autorizados: un presente y una ausencia. Asistencia calculada: **50 %**.

- [Excel](ejemplos/fase5-reporte-semanal.xlsx)
- [PDF](ejemplos/fase5-reporte-semanal.pdf)
- [Word](ejemplos/fase5-reporte-semanal.docx)

Archivos abiertos y comprobados con openpyxl, pypdf y python-docx. Cero comunicaciones externas. MySQL bloqueado en las demostraciones y pruebas.

Capturas: evidencias/proactivo-1366.png, proactivo-1920.png y proactivo-390.png.

## Estado de la entrega

Demo local en http://127.0.0.1:8017/, SQLite en memoria. Los datos de esta demo se reinician al reiniciar el proceso; cerrar el navegador no detiene sus trabajos.

Pendientes de despliegue: revisión/aplicación de migración aditiva en desarrollo, validación MySQL y servicio worker dedicado supervisado con secretos gestionados por el responsable. No se modificaron render.yaml, Procfile ni servidores de otros módulos.

No se cambiaron main, Parte 3, Segmentación IA, Parte 6 ni EmoScan. Se conservaron los tres stash. Sin commits, pushes o merges.

[Contratos, arquitectura y operación](FASE5_ASISTENTE_PROACTIVO.md).
