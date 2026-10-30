# Resultados finales de Parte 6

## Verificación efectivamente ejecutada

- Instalación nueva en un entorno Python 3.12 independiente (`p6clean`) usando las versiones fijadas: aprobada. `pip check`: sin conflictos.
- Código exportado exclusivamente desde el índice de Git a una carpeta limpia, sin `.env`, cachés ni entornos virtuales previos. Los tres artefactos se cargaron desde esa copia sin reentrenar.
- `python -m red_neuronal.validate_artifacts`: aprobada; manifiesto, modelo, escalador, arquitectura y versión compatibles.
- Suite completa ejecutada desde esa copia y el entorno nuevo: **72 pruebas aprobadas**, una advertencia de deprecación de AnyIO/Starlette, sin errores. Datos, ausencia de futuro, scaler, carga, inferencia, contrato de nueve valores, calendario objetivo, procedencia, JWT, permisos por curso, IDOR y estado pendiente.
- Chrome en **1366×768, 1920×1080 y 390×844** contra API temporal SQLAlchemy SQLite RAM: acceso JWT de prueba, selección, contexto, inferencia Keras real, historial insuficiente y modo sintético aprobados. Esta prueba NO es MySQL real.
- Chrome en las mismas resoluciones contra la aplicación final: arquitectura de **58 neuronas**, hover, selección, toque, nueve variables, tres gráficos Plotly, inferencia sintética y versión real aprobados. Sin errores JavaScript ni desbordamientos. MySQL mostrado como **Pendiente de integración**, sin valores académicos inventados.
- No se abrió una conexión a MySQL en la nube ni a producción. Esa integración y su evaluación real están pendientes del responsable del backend.

## Modelo conservado

Arquitectura 9 → 32 ReLU → 16 ReLU → 1 sigmoide, **865 parámetros**. Versión `parte6-dense-9x32x16x1-v1`. No hubo reentrenamiento ni cambios de pesos, escalador, dataset o métricas. Tres binarios sintéticos incluidos (38.165 bytes en total), con SHA-256 en `artifacts/model_manifest.json`.

4.200 ejemplos supervisados sintéticos: 2.520 entrenamiento, 840 validación, 840 prueba. Semilla 62. EarlyStopping terminó en época 27 y el mejor checkpoint fue época 17. Los indicadores siguientes son exclusivamente sintéticos.

| Métrica | Red neuronal | Regresión logística |
|---|---:|---:|
| accuracy | 0.715476 | 0.710714 |
| precision | 0.731092 | 0.720325 |
| recall | 0.846304 | 0.861868 |
| f1 | 0.784491 | 0.784765 |
| roc_auc | 0.761166 | 0.764741 |
| brier | 0.189450 | 0.188759 |
| log_loss | 0.561892 | 0.559878 |

No se demuestra superioridad general ni rendimiento validado en personas reales. Las métricas históricas de otros modelos del proyecto no se comparan como si fueran la misma evaluación.

## Entrega y alcance

50 archivos revisados: módulo `red_neuronal/` (preparación, entrenamiento original, inferencia interna, artefactos sintéticos, documentación, pruebas y runners), página/CSS/JavaScript de Parte 6, API/servicios de referencia y un enlace en el menú del profesor. No se incluyen `.env`, credenciales reales, bases locales, temporales, entornos virtuales ni modelos ONNX descargados.

La revisión de seguridad se aplicó a los archivos nuevos y modificados del commit; los archivos existentes de configuración de otros módulos no se copiaron a Parte 6 ni se modificaron. Se conservaron las ramas ajenas, Segmentación IA, EmoScan y los tres stash. No se creará PR ni merge automáticamente.

Guía para el compañero: **INTEGRACION_MYSQL.md**. Explica fórmulas y unidades, valores faltantes, escalador, contrato interno/HTTP separado, procedencia y versión, permisos y revisión necesaria del esquema real. El navegador nunca construye entradas académicas libres para el modelo.

Las capturas y reportes de QA están en `.cache/publicacion/` (locales/ignorados). La aplicación final puede abrirse en http://127.0.0.1:8007/profesor/red-neuronal.html. La demo funciona; MySQL no se anuncia como completado.
