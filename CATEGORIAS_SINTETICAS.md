# Categorías de expresiones exclusivamente sintéticas

Esta ampliación vive únicamente en el worktree monitor-asistencia-integracion-segmentacion,
rama integracion-segmentacion-ia. No modifica el generador ni el modelo de Parte 3,
EmoScan, MySQL u otras ramas. No utiliza imágenes ni inferencias faciales reales.

## Qué existía y qué puede recuperarse

El código original segmentacion/segmentacion_kmeans.py agrega las sesiones por usuario_id
ordenado y utiliza:

```python
rng = np.random.default_rng(2026)
probabilities = rng.uniform(.05, .95, len(students))
counts = rng.binomial(40, probabilities)
expresiones_positivas_ratio = counts / 40
```

Por ejemplo, el perfil 1 tiene 12 positivos sobre 40 muestras: 12/40 = 0.30.
Los CSV originales de resultados ya incluyen expresiones_positivas_conteo_simulado y
muestras_expresiones_simuladas, además de la proporción. Se preservan sin sobrescribirlos.
También es posible reproducir el conteo binario con la semilla, los parámetros, la misma
población ordenada y el entorno NumPy original.

Nunca se generaron categorías FERPlus individuales ni una secuencia de 40 expresiones.
Por tanto, las ocho categorías no pueden recuperarse como registros originales.
Una proporción positiva tampoco determina un reparto único entre ocho categorías.

## Qué se añadió y qué significa

backend/app/services/segmentacion_expresiones.py añade un desglose académico nuevo.
Por convención explícita de esta ampliación, alegría conserva exactamente el conteo binario
positivo. Esto no afirma que el antiguo generador hubiera identificado alegría ni ninguna
emoción. Las otras siete categorías se reparten con un multinomial independiente, con
pesos ilustrativos (no empíricos):

| Categoría restante | Peso dentro de las observaciones no positivas |
| --- | --- |
| Neutral | 0.55 |
| Sorpresa | 0.15 |
| Tristeza | 0.10 |
| Enojo | 0.08 |
| Disgusto | 0.04 |
| Miedo | 0.05 |
| Desprecio | 0.03 |

La semilla por perfil procede de los primeros ocho bytes SHA-256 de
desglose_sintetico_v1_semilla_2026:usuario_id:total:positivos.
El RNG adicional no consume el RNG del modelo y no usa asistencia, notas, tardanzas,
cluster ni información de EmoScan. Con el mismo entorno y datos, el resultado se reproduce
y no depende del orden de las filas. Las sumas son exactamente 40 por perfil.

El detalle se calcula después de ajustar el modelo. No entra en StandardScaler, K-Means,
PCA ni en la selección de K. No cambia las cuatro variables, etiquetas, centroides,
siluetas ni curvas de evaluación originales.

Para CSV con categorías aportadas, se respetan sus conteos tras validarlos. La respuesta
distingue csv_sintetico_validado de generado_determinista_adicional: no atribuye a un CSV
externo los pesos ni la semilla del generador adicional.

## CSV y compatibilidad

El CSV clásico de sesiones sigue funcionando igual. Sin las columnas opcionales, el
backend devuelve expresiones_categoricas=null y no se muestra el gráfico detallado.
La demostración, en cambio, solicita expresamente el desglose adicional sintético.

Para cargar categorías se incluyen estas diez columnas opcionales como conjunto completo:

```text
exp_sint_neutral,exp_sint_alegria,exp_sint_sorpresa,exp_sint_tristeza,
exp_sint_enojo,exp_sint_disgusto,exp_sint_miedo,exp_sint_desprecio,
exp_sint_total,exp_sint_origen
```

- Son conteos POR PERFIL, no por sesión. Repetirlos idénticos en todas las sesiones del
  mismo usuario_id. El backend toma una sola copia por perfil y nunca suma sus repeticiones.
- Los ocho conteos son enteros no negativos, suman exp_sint_total y el total actual es 40.
- exp_sint_alegria coincide con el conteo positivo original calculado por el modelo para
  ese dataset. No se admite usar las categorías para reemplazar la cuarta variable.
- exp_sint_origen=sintetico en todas las filas; se mantiene origen_datos=sintetico.
- Un conjunto parcial, valores decimales, negativos, sumas incorrectas, datos inconsistentes
  por usuario o datos que no respeten el conteo positivo se rechazan con un error claro.
- Los límites de 2 MiB, 10000 sesiones y 4–500 perfiles permanecen vigentes.
- No se admiten fotografías, ratios faciales externos ni datos privados de EmoScan.

Ejemplos nuevos, sin sobrescribir los originales:

- frontend/ejemplos/segmentacion_sintetica_categorias.csv: 6750 sesiones de carga con conteos
  por perfil repetidos. Tiene 709252 bytes, aproximadamente 693 KiB (menos de 2 MiB).
- segmentacion/ejemplos/expresiones_categorias_por_perfil.csv: 150 filas, una por perfil,
  con las cuatro variables originales y las ocho categorías adicionales.

Para regenerar ambos ejemplos académicos desde la raíz del worktree:

```powershell
.\.venv\Scripts\python.exe -B integraciones/segmentacion/generar_categorias_sinteticas.py
```

El script aislado importa el generador original sin editarlo. Para otro CSV, hay que
preparar sus perfiles con prepare_students y generar sus conteos con generate_counts:
no copiar ciegamente los conteos de la demostración, porque el generador binario original
depende de la población completa y de su orden por identificador.

El botón Descargar resultados añade las columnas categóricas cuando existen datos válidos.
En CSV clásicos conserva el formato de resultados anterior. El CSV de resultados por
perfil no sustituye el formato de sesiones requerido para una nueva carga.

## Gráfico y unidades

Se conservan las ocho tarjetas previas y se añade una sección independiente debajo.
Su selector cambia entre General y Por cluster:

- General: ocho barras de cantidades y porcentajes, sobre las observaciones de los
  grupos visibles. El tooltip muestra cantidad, porcentaje y denominador.
- Por cluster: barras apiladas de ocho categorías. Cada porcentaje usa las observaciones
  de ese cluster, no el total de estudiantes.
- El filtro global y la ocultación de clusters en las dispersiones también afectan al detalle.
- Los colores de este gráfico identifican categorías, no E1/E2/E3.
- Si no hay datos suficientes, el gráfico se oculta y se purgan los datos anteriores.
- Se indica de forma visible que son observaciones simuladas, no porcentajes de estudiantes
  que realmente sienten emociones. No son resultados ni probabilidades del clasificador FERPlus.

La demostración tiene 150 × 40 = 6000 observaciones, repartidas en 1800, 2400 y 1800 por cluster.
Son distintas de las 6750 sesiones de asistencia; no deben confundirse ambas cantidades.

| Categoría sintética | Cantidad de observaciones | Porcentaje de 6000 |
| --- | ---: | ---: |
| Neutral | 1631 | 27.1833 % |
| Alegría | 3071 | 51.1833 % |
| Sorpresa | 436 | 7.2667 % |
| Tristeza | 281 | 4.6833 % |
| Enojo | 237 | 3.9500 % |
| Disgusto | 104 | 1.7333 % |
| Miedo | 141 | 2.3500 % |
| Desprecio | 99 | 1.6500 % |
| Total | 6000 | 100 % |

## Cómo verlo

Abrir http://127.0.0.1:8001/profesor/segmentacion.html, iniciar sesión como profesor y
recargar con Ctrl+F5. Pulsar Ver demostración y bajar a Distribución de expresiones sintéticas.
Elegir General o Por cluster; consultar las cantidades y los porcentajes en las barras
y los tooltips. Aplicar un filtro de cluster para verificar el cambio de denominador.

Para comprobar CSV, desplegar Cargar CSV y descargar el ejemplo con categorías sintéticas.
Procesarlo y observar el gráfico. Cargar después el ejemplo clásico: los ocho análisis
originales permanecen disponibles y el detalle categórico desaparece.

FastAPI necesita recarga para incorporar el nuevo adaptador. La ruta de demostración
y la carga siguen protegidas por autenticación y rol profesor.

## Límites

La distribución adicional es ilustrativa. No reconstruye expresiones que nunca se
generaron; la relación alegría/positivo es una convención académica. No sirve para
estimar emociones, atención, capacidad o riesgo de personas. Los conteos opcionales
actuales se limitan a 40 observaciones para conservar el total y la proporción originales.
La reproducción exacta debe utilizar el mismo entorno de dependencias.
Las pruebas de navegador usan autenticación y cámara simuladas, con JSON del modelo real.
La sesión con la base local y la cámara física requieren revisión manual.

## Resultados de verificación

- 79 pruebas Python de backend e integración: aprobadas.
- 10 pruebas del modelo original: aprobadas.
- 280 comprobaciones en Chrome: aprobadas; vistas general y por cluster, hover real y resoluciones 1366×768, 1920×1080 y 390×844.
- 14 pruebas JavaScript de EmoScan: aprobadas.
- Se mantienen exactamente las entradas, puntos, grupos, PCA, centroides, siluetas y evaluación K del análisis clásico.
- Demostración: 150 perfiles, K=3, silueta aproximada 0.237369 y 6000 observaciones simuladas adicionales.
- Se valida que los conteos repetidos por sesión no se sumen, y que CSV clásicos oculten y purguen el detalle anterior.
- Se corrigió el reinicio de escalas al alternar orientación general/por cluster.
- Capturas locales en segmentacion/.cache/categorias/; archivos originales y referencias Git verificados sin cambios.
- FastAPI recargado; demostración sin token rechazada con 401. La cuenta real y la cámara física no se verifican mediante las pruebas simuladas de navegador.
