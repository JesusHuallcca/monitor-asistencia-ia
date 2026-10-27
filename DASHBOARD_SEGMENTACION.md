# Segmentación IA — Aprendizaje No Supervisado con K-Means

Trabajo local en monitor-asistencia-integracion-segmentacion, rama integracion-segmentacion-ia.
El dashboard conserva una sola página, menú SENATI, autenticación de profesor y CSV sintéticos.
No modifica el algoritmo definitivo, sus semillas, escalado, asignaciones ni criterio de K.

## Abrir y exponer

1. Con FastAPI en http://127.0.0.1:8000 y frontend en http://127.0.0.1:8001,
   iniciar sesión como profesor en http://127.0.0.1:8001/login.html.
2. Abrir http://127.0.0.1:8001/profesor/segmentacion.html y recargar con Ctrl+F5.
3. Pulsar **Ver demostración**: 150 perfiles, K=3, silueta aproximada 0.237369 y cuatro variables.
   Todos los indicadores se leen de la API, sin resultados fijos en JavaScript.
4. **Cargar CSV** despliega formato, selección/arrastre y ejemplo. Elegir un CSV de sesiones
   sintéticas y pulsar **Procesar segmentación**. El servidor valida cada fila; se muestran
   sesiones y perfiles procesados. Un archivo nuevo borra inmediatamente el análisis anterior.
5. Explorar grupos mediante filtro, leyenda o botones descriptivos. Restablecer filtros
   recupera todos los grupos, selección y zoom. Descargar resultados entrega el CSV completo.

Las columnas de entrada, límites y validaciones de seguridad se conservan:
usuario_id, sesion (o sesion_id), estado, promedio_notas y origen_datos=sintetico.
UTF-8, máximo 2 MiB, 10000 sesiones y entre 4 y 500 perfiles. No incluir expresiones de
entrada, fotos ni datos faciales; el servidor genera las expresiones sintéticas.

## Distribución en una página

Encabezado y aviso académico, controles, cuatro indicadores, leyenda descriptiva de grupos
y ocho tarjetas en cuatro filas de dos columnas (una columna en móvil). No hay pestañas.
El PCA ocupa siete de doce columnas y la silueta cinco; las demás filas se reparten
en mitades. El borde azul, el rótulo Vista principal y el mayor tamaño destacan el PCA.

| Fila | Izquierda | Derecha |
| --- | --- | --- |
| 1 | PCA principal con perfiles y centroides | Silueta por perfil |
| 2 | Asistencia vs. promedio de notas | Asistencia vs. expresiones positivas sintéticas |
| 3 | Método del codo | Mapa de calor de centroides |
| 4 | Distribución de perfiles por cluster | Comparación de cuatro variables en cuatro barras separadas |

Al final aparecen la explicación de elección de K y la tabla de perfiles seleccionados.
Se mantienen exactamente tres dispersiones de perfiles: PCA y las dos comparaciones
complementarias. No se reincorpora Tardanzas vs. notas.
La variable tardanzas permanece en todos los cálculos del modelo.

## Qué representa cada gráfico

1. **PCA**: cada punto es un perfil; cada rombo es el centroide real de un cluster, proyectado
   al mismo espacio PCA. PC1/PC2 muestran la varianza explicada. La vista 2D resume un
   modelo calculado en cuatro dimensiones; no se vuelve a entrenar al filtrar.
2. **Asistencia vs. promedio de notas**: cada punto es un perfil; X es asistencia (0–100 %)
   e Y la nota media (0–20). Permite comparar grupos conservando sus etiquetas y colores,
   sin afirmar causalidad ni predecir rendimiento.
3. **Asistencia vs. expresiones positivas sintéticas**: X e Y son porcentajes (0–100 %).
   Permite explorar la variable experimental simulada; no representa emociones reales
   ni utiliza datos faciales de EmoScan.
4. **Silueta por perfil**: una barra por persona ficticia, ordenada dentro de su grupo.
   La línea marca la media del dataset completo. Valores cercanos a 1 indican mayor
   separación, cercanos a 0 solapamiento y negativos mayor cercanía a otro grupo.
   No es una medida de precisión ni valida predicciones.
5. **Codo**: inercia para los K evaluados y línea en el K elegido. El cambio de pendiente
   sirve como orientación; no reemplaza el criterio documentado.
6. **Mapa de calor**: filas de centroides y columnas de los cuatro atributos estandarizados.
   Azul es menor que la media de la muestra; naranja mayor; blanco cercano a ella.
   La escala z es simétrica y se mantiene al filtrar. Estos colores expresan valores,
   no identidades de grupo; los grupos conservan sus colores en los demás gráficos.
7. **Distribución**: cantidad de perfiles por cluster, con etiquetas sobre las barras.
   En la demostración son 45, 60 y 45.
8. **Comparación**: cuatro pequeños gráficos de barras de medias con escalas independientes:
   asistencia, tardanzas y expresiones 0–100 %; notas 0–20. No se mezclan unidades.

Las descripciones de E1/E2/E3 se calculan comparando las medias de asistencia observadas:
baja, intermedia o relativamente alta dentro de esta muestra. Si los identificadores
cambian, los nombres siguen los valores, no el número del grupo. Si son iguales, se
describe asistencia similar. No son etiquetas de riesgo, diagnósticos ni pronósticos.

## Interactividad y tooltips

Los tres gráficos de puntos comparten colores E1 azul, E2 naranja y E3 verde, nombres
descriptivos, filtro y selección de perfiles. La barra aparece al pasar el puntero y contiene zoom, desplazamiento, selección y restaurar.
Se conserva el zoom con rueda. El tooltip de perfiles y centroides aparece debajo del dibujo,
en una zona reservada que impide tapar puntos o salirse de la tarjeta. Tiene fondo blanco,
borde redondeado, letra compacta y valores dinámicos. La silueta añade el coeficiente individual.
Pulsar un perfil muestra su tarjeta y lo selecciona; la tabla inferior detalla hasta doce.
Pulsar un centroide filtra su grupo, sin contarlo como un perfil adicional.
Los tres centroides no aumentan el indicador de 150 perfiles.

Ocultar grupos afecta a las vistas y al mapa de calor. Las métricas y la evaluación siguen
usando el dataset completo. El filtro no vuelve a calcular K-Means ni siluetas.
Las expresiones son exclusivamente sintéticas y no proceden de EmoScan.

## Ampliación de la API de segmentación

Solo cambia backend/app/services/segmentacion_service.py. Los endpoints, dependencias de
autorización y límites permanecen iguales. Nuevos campos de respuesta:

- centroides: segmento, pca_1, pca_2, valores_estandarizados (orden de variables) y cuatro
  atributos en unidades originales.
- siluetas: usuario_id, segmento y silueta individual para todos los perfiles.

Se reutilizan centros, etiquetas, media y escala del modelo. silhouette_samples se evalúa
con las mismas cuatro variables estandarizadas y distancia euclídea. Se reproduce la base
PCA full-SVD sobre esos mismos datos para proyectar los centros reales, comprobando que
las coordenadas de perfiles coincidan con las originales. No se ajusta otro K-Means.
El promedio de las siluetas individuales coincide con la métrica existente.

Para la demostración se conserva el mejor K entre K >= 3: K=3. El mejor global es K=2
y el codo orientativo K=4. No se cambian cálculos para elevar artificialmente la métrica.
El CSV descargable conserva los resultados originales del modelo.

Plotly Cartesian 2.35.2 se sirve localmente para incluir heatmap; licencia y hash en
frontend/vendor/PLOTLY.md. No se emplean gráficos PNG precalculados.

## Pruebas y límites

Pruebas numéricas independientes comprueban centros estandarizados y originales, proyección
PCA y siluetas individuales para 150, 20 y 4 perfiles (incluidos clusters de un solo perfil).
Las pruebas de Chrome comprueban datos reales del modelo, leyendas dinámicas con identificadores
permutados, centroides, mapa de calor, hover de silueta, bordes, selección, zoom, restauración,
descarga, CSV inválidos y sustitución por 20 perfiles. Se prueban 1366×768, 1920×1080 y 390×844.

Las pruebas Python usan SQLite en RAM y bloquean MySQL. Las de navegador usan una sesión
y cámara de prueba, y JSON generado con el modelo real mediante
frontend/tests/preparar_segmentacion.py. No sustituyen la prueba manual de login con una
cuenta real ni de la cámara física. No se ha modificado EmoScan ni se accede a datos de
producción. Los diagnósticos requieren recargar el backend para que la API devuelva los
campos nuevos; el frontend rechaza una respuesta antigua o incompleta.

Capturas locales de verificación: segmentacion/.cache/ocho-graficos/ (excluidas de Git).
Comandos generales y configuración en INTEGRACION_FINAL.md.

Referencias de las APIs utilizadas:
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_samples.html
- https://plotly.com/javascript/heatmaps/
- https://github.com/plotly/plotly.js/blob/v2.35.2/dist/README.md


La última ampliación solo modifica la pantalla, su controlador, estilos exclusivos, pruebas de navegador y esta guía. No cambia el backend ni el modelo.

## Verificación de las ocho tarjetas

- 66 pruebas de backend y permisos: aprobadas.
- 10 pruebas del modelo: aprobadas.
- 246 comprobaciones de Chrome: aprobadas.
- 14 pruebas JavaScript de EmoScan: aprobadas.
- Resoluciones 1366×768, 1920×1080 y 390×844: sin desbordamientos ni excepciones JavaScript.
- Los tres gráficos conservan 150 perfiles en la demostración, K=3 y silueta aproximada 0.237369.
- Nuevo CSV de 20 perfiles: coordenadas de las tres dispersiones, centroides, siluetas, codo, distribución y medias sustituidos por los nuevos datos.
- Se verifican hover en los cuatro extremos de las tres dispersiones, zoom y restauración en las comparaciones, selección sincronizada, filtro global y descarga CSV.
- Capturas en segmentacion/.cache/ocho-graficos/. Las pruebas de navegador usan autenticación y cámara simuladas y resultados del modelo real; queda la revisión manual con la cuenta local.
- Backend, modelo, MySQL, EmoScan y otras ramas intactos; sin commits ni pushes.

## Detalle categórico opcional

Las ocho tarjetas anteriores se conservan. Debajo se añade Distribución de expresiones
sintéticas con selector General / Por cluster. La demostración incluye el desglose adicional;
el CSV clásico sigue siendo compatible y no muestra ese detalle cuando no lo aporta.
Los nuevos conteos no entran en el modelo ni cambian las cuatro variables o asignaciones.
Ver [CATEGORIAS_SINTETICAS.md](CATEGORIAS_SINTETICAS.md) para la reconstrucción binaria,
la convención académica, el esquema CSV, ejemplos y límites.