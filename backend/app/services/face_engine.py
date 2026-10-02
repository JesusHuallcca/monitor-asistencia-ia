import threading
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


class FaceError(Exception):
    """Error que el usuario puede corregir (no se ve la cara, hay varias, etc.)."""


class FaceUnavailable(Exception):
    """El motor no está listo (faltan modelos, etc.)."""


class OpenCVFaceEngine:
    """Motor de reconocimiento: YuNet (detección) + SFace (embedding)."""

    def __init__(self, models_dir: str):
        base = Path(models_dir)
        det = base / "face_detection_yunet_2023mar.onnx"
        rec = base / "face_recognition_sface_2021dec.onnx"
        if not det.exists() or not rec.exists():
            raise FaceUnavailable(f"Faltan los modelos .onnx en {base}")

        self._lock = threading.Lock()
        self._detector = cv2.FaceDetectorYN.create(str(det), "", (320, 320), 0.8, 0.3, 5000)
        self._recognizer = cv2.FaceRecognizerSF.create(str(rec), "")

    def embedding(self, image_bytes: bytes) -> np.ndarray:
        img = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise FaceError("Imagen inválida")

        alto, ancho = img.shape[:2]
        mayor = max(alto, ancho)
        if mayor > 1280:  # reducir fotos enormes
            escala = 1280 / mayor
            img = cv2.resize(img, (int(ancho * escala), int(alto * escala)))
            alto, ancho = img.shape[:2]

        with self._lock:  # el detector guarda estado interno
            self._detector.setInputSize((ancho, alto))
            _, caras = self._detector.detect(img)

            if caras is None or len(caras) == 0:
                raise FaceError("No se detectó ningún rostro. Mira a la cámara con buena luz.")
            if len(caras) > 1:
                raise FaceError("Se detectaron varios rostros. Debe aparecer solo una persona.")
            cara = caras[0]
            if float(cara[14]) < 0.9:
                raise FaceError("El rostro no se ve con claridad. Acércate y mejora la luz.")

            alineado = self._recognizer.alignCrop(img, cara)
            vector = self._recognizer.feature(alineado)

        return np.asarray(vector, dtype=np.float32).flatten()

    @staticmethod
    def similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Similitud coseno: más alta = más parecidos."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@lru_cache(maxsize=1)
def get_engine() -> OpenCVFaceEngine:
    return OpenCVFaceEngine(settings.FACE_MODELS_DIR)