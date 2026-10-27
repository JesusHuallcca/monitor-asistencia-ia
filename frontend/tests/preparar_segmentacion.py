"""Calcula las fixtures de navegador desde el modelo definitivo, sin MySQL."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
import pandas as pd
from app.services.segmentacion_service import process_csv
from segmentacion.segmentacion_kmeans import DEFAULT_DATA

if __name__ == "__main__":
    output = ROOT / "segmentacion" / ".cache"
    output.mkdir(exist_ok=True)
    full = process_csv(DEFAULT_DATA.read_bytes(), generar_detalle=True)
    legacy = process_csv(DEFAULT_DATA.read_bytes())
    raw = pd.read_csv(DEFAULT_DATA)
    small = process_csv(raw[raw.usuario_id <= 20].to_csv(index=False).encode("utf-8"))
    for name, data in [("demo_api.json", full), ("demo_api_small.json", small), ("demo_api_legacy.json", legacy)]:
        (output / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("Fixtures reales preparadas: 150 y 20 perfiles sintéticos. Sin conexión a MySQL.")
