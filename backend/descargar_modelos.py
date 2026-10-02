from pathlib import Path

from huggingface_hub import hf_hub_download

destino = Path(__file__).resolve().parents[1] / "ai" / "face" / "models"
destino.mkdir(parents=True, exist_ok=True)

modelos = [
    ("opencv/face_detection_yunet", "face_detection_yunet_2023mar.onnx"),
    ("opencv/face_recognition_sface", "face_recognition_sface_2021dec.onnx"),
]

for repo, archivo in modelos:
    ruta = hf_hub_download(repo_id=repo, filename=archivo, local_dir=str(destino))
    print("OK:", ruta)