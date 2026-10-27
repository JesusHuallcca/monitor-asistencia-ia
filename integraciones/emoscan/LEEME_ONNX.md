# EmoScan con OpenCV + ONNX Runtime

La variante actual utiliza FERPlus ONNX en CPU, sin TensorFlow ni PyTorch.
Convierte el recorte BGR a gris 64×64, tensor NCHW float32, y aplica softmax a ocho
clases: neutral, happy, surprise, sad, angry, disgust, fear y contempt.
Si falta el modelo falla explícitamente, sin expresiones aleatorias.

La integración de asistencia se ejecuta en FastAPI, reutiliza su fotograma y
aplica consentimiento, cola y caducidad. Ver [INTEGRACION_ASISTENCIA.md](INTEGRACION_ASISTENCIA.md).

## Modelo y fotografía de prueba

`emotion-ferplus-8.onnx` se incluye junto a `emotion_onnx.py`. Si falta en
una distribución alternativa, ejecutar desde la raíz:

```powershell
.\.venv312\Scripts\python.exe integraciones/emoscan/descargar_modelo.py
```

No guardarlo en `models/`: `config.MODEL_PATHS` apunta junto al clasificador.
Origen, tamaño y SHA-256: [MODELOS.md](MODELOS.md).

Las fotografías y los resultados locales de pruebas están excluidos de Git:

```powershell
.\.venv312\Scripts\python.exe integraciones/emoscan/descargar_imagen_prueba.py
.\.venv312\Scripts\python.exe -B -m pytest backend/tests/emoscan -q -p no:cacheprovider
```

El preparador obtiene la fotografía pública de NASA documentada en
`imagenes_prueba/ORIGEN.md`, valida SHA-256 y no sobrescribe archivos diferentes.

## Interfaz original independiente

Se conserva la interfaz Flask. Solo para ejecutarla por separado, con sus
dependencias de `integraciones/emoscan/requirements.txt`, desde la raíz:

```powershell
.\.venv312\Scripts\python.exe integraciones/emoscan/app.py
```

Su `/health` en el puerto 5000 informa `onnx_loaded`. No iniciar este servidor
junto a la cámara del Monitor para la integración de asistencia.
La inferencia con fotografía y la interfaz se verifican sin cámara; la cámara
física sigue siendo una comprobación manual pendiente.
