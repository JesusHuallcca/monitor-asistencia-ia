# Parte 6 — Red neuronal personalizada

Versión para revisión e integración por el responsable del backend. **MySQL: Pendiente de integración**. La demostración sintética funciona sin base ni credenciales. No conectarse a la nube desde la computadora de presentación.

Lee primero **[INTEGRACION_MYSQL.md](INTEGRACION_MYSQL.md)**: contrato interno validado, nueve variables, fórmulas, permisos, procedencia, instalación y rutas pendientes. **[RESULTADOS_PUBLICACION.md](RESULTADOS_PUBLICACION.md)** registra las verificaciones finales.

Modelo conservado: 9 → 32 ReLU → 16 ReLU → 1 sigmoide, 865 parámetros. TensorFlow 2.20.0/Keras, Python 3.12. Semilla 62. Las curvas y métricas provienen del entrenamiento real original; no se reentrenó para publicar.

Los tres artefactos necesarios se incluyen en `artifacts/` junto a `model_manifest.json`. Ejecuta `python -m red_neuronal.validate_artifacts` para comprobar integridad y carga; cargar exclusivamente binarios confiables de este repositorio.

```powershell
$pythonP6 = "$env:USERPROFILE/.venvs/p6/Scripts/python.exe"
& $pythonP6 -m pip install -r red_neuronal/requirements-integracion.txt
& ./red_neuronal/start_parte6.ps1
```

Abrir http://127.0.0.1:8007/profesor/red-neuronal.html y activar Demostración sintética. El diagrama representa las 58 neuronas; las conexiones son ilustrativas, no pesos individuales. Incluye selección con ratón, teclado y toque, explicaciones y parámetros por capa.

## Reproducir el experimento original (opcional, no para inferencia)

`python -m red_neuronal.generate --seed 62`, `python -m red_neuronal.train --epochs 80 --seed 62` y `python -m red_neuronal.evaluate`. Una consulta jamás entrena ni modifica el escalador. Para preservar esta versión, usa `--out` en otro directorio al experimentar; un nuevo entrenamiento necesita su propio manifiesto y versión.

La división temporal y por estudiante, las métricas originales y la comparación están detalladas en [RESULTADOS.md](RESULTADOS.md). Registros de pruebas de una iteración anterior están en [RESULTADOS_INTEGRACION.md](RESULTADOS_INTEGRACION.md); no constituyen validación de MySQL real y sus instrucciones locales fueron sustituidas por la guía actual.

## Pruebas

`python -m pytest red_neuronal/tests -q -p no:cacheprovider` y `python -m red_neuronal.run_system_ui_tests`. Este último ejecuta Chrome con SQLAlchemy SQLite RAM y JWT de prueba: no accede a producción ni utiliza alumnos reales. Las capturas locales quedan en `.cache/` y no se publican.
