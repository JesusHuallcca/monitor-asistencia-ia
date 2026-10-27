#!/usr/bin/env bash
# railway_startup.sh
# Se ejecuta antes de arrancar uvicorn en Railway.
# Descarga el modelo FERPlus ONNX si no existe (no se sube a Git por su tamaño).

set -e

MODEL_DIR="/app/integraciones/emoscan"
MODEL_PATH="${MODEL_DIR}/emotion-ferplus-8.onnx"
MODEL_URL="https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/model/emotion-ferplus-8.onnx?download=true"

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_PATH" ] || [ "$(wc -c < "$MODEL_PATH")" -lt 1000000 ]; then
    echo "Descargando modelo FERPlus ONNX..."
    curl -L --retry 3 --retry-delay 5 -o "${MODEL_PATH}.part" "$MODEL_URL"
    mv "${MODEL_PATH}.part" "$MODEL_PATH"
    echo "Modelo descargado correctamente: $(du -sh "$MODEL_PATH" | cut -f1)"
else
    echo "Modelo FERPlus ONNX ya presente: $(du -sh "$MODEL_PATH" | cut -f1)"
fi

echo "Startup completado. Arrancando uvicorn..."
