# Verificación de Parte 3: K-Means de cuatro variables

Fecha: 26 de octubre de 2026. Worktree: `monitor-asistencia-parte3`.
Rama: `parte-3-segmentacion`.

## Pruebas ejecutadas

Desde la raíz, con un intérprete que tenga las dependencias de
`segmentacion/requirements.txt`:

```powershell
python -B -m unittest discover -s segmentacion -t . -v
python -B segmentacion/segmentacion_kmeans.py
```

**10 pruebas aprobadas en 29.764 segundos. Ejecución completa: código de salida 0.**

El alias `python` de Windows no estaba disponible. Para esta verificación se usó
el intérprete existente `../monitor-asistencia-ia/segmentacion/.venv/Scripts/python.exe`
con `-B`, sin instalar ni cambiar paquetes. Todas las ejecuciones, temporales,
caché de Matplotlib y resultados se ubicaron en este worktree.
Python 3.14.7, NumPy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1 y Matplotlib 3.11.2.

Las diez pruebas comprueban:

1. Agregaciones de asistencia, tardanzas y notas calculadas desde el CSV compartido,
   sin modificar la entrada.
2. Conteos sintéticos reproducibles, incluso al reordenar las sesiones.
3. Simulación de expresiones independiente de notas, asistencia y etiquetas.
4. Rechazo de fuentes no sintéticas, expresiones externas, duplicados y valores inválidos.
5. Uso efectivo de las cuatro variables, escalado y selección de k.
6. Codo como heurística separada de la elección por silueta.
7. Rechazo de perfiles insuficientes o variables inválidas durante el ajuste.
8. Siete archivos de salida completos y reproducibles; límites de rutas de entrada y salida.
9. Ejecución como script y como módulo con el CSV predeterminado; error controlado del CLI.
10. Correspondencia numérica de PCA, centroides, silueta y codo con el modelo de cuatro variables.

## Resultados regenerados

| Comprobación | Resultado |
|---|---|
| Entrada | `datos_asistencia_sinteticos.csv` |
| Sesiones sintéticas | 6750 |
| Perfiles sintéticos únicos | 150 |
| Variables | asistencia_ratio, tardanzas_ratio, promedio_notas, expresiones_positivas_ratio |
| k elegido entre k≥3 | 3 |
| Silueta | 0.237369 |
| Perfiles por segmento | 45 / 60 / 45 |
| Mejor k global | 2 |
| Codo orientativo | 4 |
| Varianza conservada en PCA 2D | 73.8 % |

Se regeneraron los siete archivos de `resultados/` con la ruta actual de entrada.
Se inspeccionó visualmente `visualizacion_clusters.png`: contiene la proyección PCA
de las cuatro variables, centroides con cuatro columnas (incluidas expresiones
sintéticas), silueta e inercia. Las pruebas contrastan esos paneles con los valores
calculados; K-Means se ajusta antes de PCA, en cuatro dimensiones.

## Recuperabilidad y alcance

Antes de eliminar las copias antiguas se verificaron los diez hashes originales
contra el commit `5a0f2a54d87aa2c61a6cb338922a29b0aa0f0a47`, considerando LF/CRLF.
La documentación y los resultados experimentales anteriores coinciden con
`b33ed020e7972ad7b1e1808381ecec1969e47bd2`. Ambos commits permanecen en Git.
Los comandos para consultar o exportar la versión anterior están en
[README_Parte3.md](README_Parte3.md#recuperar-la-versión-anterior-desde-git).

El CSV compartido conserva su SHA-256:
`10780c9f18cadbcc005cd9d1827f73cbfd203a5c12ff5ea5339b484ab4bc339b`.
Se eliminaron las copias locales de la implementación anterior y sus manifiestos;
la versión actual contiene solo el modelo actualizado y los archivos necesarios.

Se verificó `git diff --check`. No se modificaron EmoScan ni otros módulos;
el cambio previo del README raíz se conservó. Las referencias de Git, incluida
`main`, permanecen iguales. No se hicieron commits ni pushes.
La verificación ejecutada corresponde a Parte 3; no se ejecutaron suites de otros módulos.
