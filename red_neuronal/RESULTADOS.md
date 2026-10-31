# Resultados reales de Parte 6

Verificación local: 29 de octubre de 2026. Sin commits, pushes ni merges.

Python 3.12.10; TensorFlow 2.20.0; Keras 3.15.1. CPU Windows, entorno independiente en `C:/Users/Jakelin.Cullampe/.venvs/p6`.

Arquitectura 9 → 32 (ReLU) → 16 (ReLU) → 1 (sigmoide), 865 parámetros. Semilla 62. Máximo 80 épocas: EarlyStopping terminó en 27; checkpoint seleccionado en época 17.

Dataset: 120 perfiles, 4.800 sesiones sintéticas, 4.200 ejemplos supervisados. Entrenamiento 2.520 / validación 840 / prueba 840. Sin estudiantes compartidos y con orden cronológico entre particiones.

| Métrica de test | Red neuronal | Regresión logística |
|---|---:|---:|
| accuracy | 0.715476 | 0.710714 |
| precision | 0.731092 | 0.720325 |
| recall | 0.846304 | 0.861868 |
| f1 | 0.784491 | 0.784765 |
| roc_auc | 0.761166 | 0.764741 |
| brier | 0.189450 | 0.188759 |
| log_loss | 0.561892 | 0.559878 |

La red obtiene algo más de accuracy y precision; la logística obtiene mayor recall, F1 y ROC-AUC, y menores Brier/log loss. No hay superioridad general demostrada. No se compara con el modelo histórico preexistente, que usa otra evaluación.

Matriz neuronal (filas reales, columnas predichas; orden no asiste/asiste): `[[166,160],[79,435]]`. Matriz logística: `[[154,172],[71,443]]`.

Pruebas ejecutadas:

- `pytest red_neuronal/tests -q -p no:cacheprovider`: **30 aprobadas**. Una advertencia de deprecación de AnyIO/Starlette, sin fallos. Preparación, exclusión del futuro, datos duplicados/reales, cohortes, escalador, métricas recalculadas, inferencia repetible, formato, 401/403/200 en ambos endpoints, modelo ausente y recursos frontend.
- `python -m red_neuronal.evaluate`: métricas recalculadas desde los artefactos locales (tolerancia numérica 1e-6 comprobada en las pruebas).
- Dos entrenamientos independientes con semilla 62: curvas, métricas y pesos **idénticos** en este entorno. Segunda ejecución en `.cache/repro/`.
- Chrome real headless: 1366×768, 1920×1080, 390×844. Gráficos, inferencia, cambio de datos, zoom, recarga, estado de error, sesión explícita y ausencia de desbordamiento. Sin errores JavaScript. Capturas en `.cache/browser/`.

Revisión de alcance: todos los archivos del módulo son nuevos; ningún archivo ya versionado fue modificado. `main`, modelos existentes, Segmentación IA, EmoScan y los tres stash se conservan. No se ejecutó el lifespan de la aplicación original, no se consultó MySQL y no se descargaron modelos faciales.

Servidor aislado: http://127.0.0.1:8006/profesor/red-neuronal.html. Pulsar **Iniciar demostración sintética**. La sesión local no autentica cuentas reales.

Pendiente: probar la entrada optativa `app.parte6:app` con cuentas reales en un entorno de integración autorizado. No se ha validado rendimiento con estudiantes reales ni se afirma calibración poblacional.
