"""Descarga manual explícita del modelo público FERPlus (33 MB aprox.)."""
from pathlib import Path
from urllib.request import urlopen
from config import MODEL_PATHS

URL = "https://huggingface.co/onnxmodelzoo/emotion-ferplus-8/resolve/main/model/emotion-ferplus-8.onnx?download=true"
DEST = MODEL_PATHS['emotion_onnx']

def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.is_file() and DEST.stat().st_size > 1_000_000:
        print("Modelo ya presente:", DEST)
        return
    temp = DEST.with_suffix(".part")
    try:
        with urlopen(URL, timeout=90) as response, temp.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        if temp.stat().st_size < 1_000_000:
            raise RuntimeError("Descarga incompleta o no es un modelo ONNX")
        temp.replace(DEST)
        print("Modelo descargado:", DEST)
    finally:
        if temp.exists():
            temp.unlink()

if __name__ == "__main__":
    main()
