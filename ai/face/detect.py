import cv2
from pathlib import Path


class FaceDetector:
    def __init__(self):
        model_path = (
            Path(__file__).resolve().parent
            / "models"
            / "haarcascade_frontalface_default.xml"
        )

        self.detector = cv2.CascadeClassifier(str(model_path))

        if self.detector.empty():
            raise RuntimeError(
                f"No se pudo cargar el clasificador facial: {model_path}"
            )

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        return faces


def detect_faces(frame):
    detector = FaceDetector()
    return detector.detect(frame)