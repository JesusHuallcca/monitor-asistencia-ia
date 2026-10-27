# Modelos necesarios y distribución

Estos modelos públicos no contienen fotografías ni embeddings de estudiantes.
El reconocimiento de identidad existente no se modifica.

| Modelo | Ruta desde la raíz | Bytes | SHA-256 |
|---|---|---:|---|
| FERPlus opset 8 | `integraciones/emoscan/emotion-ferplus-8.onnx` | 35040571 | `a2a2ba6a335a3b29c21acb6272f962bd3d47f84952aaffa03b60986e04efa61c` |
| YuNet | `models/face_detection_yunet_2023mar.onnx` | 232589 | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| SFace | `models/face_recognition_sface_2021dec.onnx` | 38696353 | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` |

FERPlus se incorpora a esta rama (33.4 MiB), sin necesitar Git LFS. YuNet y SFace
ya forman parte del repositorio. No se añaden modelos personalizados de estudiantes.

## Recuperación alternativa

Si una distribución omite FERPlus, desde la raíz:

```powershell
.\.venv312\Scripts\python.exe integraciones/emoscan/descargar_modelo.py
Get-FileHash integraciones/emoscan/emotion-ferplus-8.onnx -Algorithm SHA256
```

Comparar el hash con la tabla antes de usarlo. URL del descargador:
https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/model/emotion-ferplus-8.onnx?download=true

Documentación y licencia MIT declarada por ONNX Model Zoo:
https://github.com/onnx/models/tree/main/validated/vision/body_analysis/emotion_ferplus

Aviso original FERPlus: `LICENCIA_FERPLUS.txt`.
Fuente: https://github.com/ebarsoum/FERPlus/blob/master/LICENSE.md

Para YuNet y SFace, el script existente `backend/descargar_modelos.py` requiere
`huggingface_hub` y descarga de `opencv/face_detection_yunet` y
`opencv/face_recognition_sface` a `ai/face/models`. También están en `models/`
en este repositorio. Consultar las licencias de sus repositorios de origen.

## Rutas

El valor predeterminado de `FACE_MODELS_DIR` es `ai/face/models`. Para utilizar
los dos binarios incluidos en `models/`, ejecutar desde la raíz y definir en
el `.env` local `FACE_MODELS_DIR=models`.

`EMOSCAN_MODEL_PATH` es opcional: por defecto apunta al FERPlus incluido.
La fotografía pública se prepara con `descargar_imagen_prueba.py` y queda
excluida de Git; no es necesaria para ejecutar el Monitor con su cámara.
