# redeploy trigger
#!/usr/bin/env bash
set -e

# Directory where the ONNX model lives (relative to project root)
MODEL_DIR="integraciones/emoscan"
MODEL_FILE="emotion-ferplus-8.onnx"
# Public URL for the model (GitHub raw file)
MODEL_URL="https://github.com/onnx/models/raw/main/vision/classification/emotion_ferplus/model/emotion-ferplus-8.onnx"

# Ensure the directory exists
mkdir -p "$MODEL_DIR"

# Download the model if it is not already present
if [ ! -f "$MODEL_DIR/$MODEL_FILE" ]; then
  echo "Downloading ONNX model..."
  curl -L -o "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL"
else
  echo "ONNX model already present."
fi

# Start the FastAPI server with proper PYTHONPATH (project root + backend)
cd backend
PYTHONPATH=/app:/app/backend uvicorn app.main:app --host 0.0.0.0 --port $PORT
