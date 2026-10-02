import time

import cv2

from backend.app.services.face_service import face_service
from backend.app.services.liveness_service import liveness_service


class CameraService:
    def __init__(
        self,
        camera_index=0,
        processing_interval=0.5
    ):
        self.camera_index = camera_index
        self.processing_interval = processing_interval
        self.capture = None
        self.last_processing_time = 0.0
        self.last_result = {
            "faces_detected": 0,
            "faces": []
        }

    def start(self):
        if self.capture is not None:
            return

        self.capture = cv2.VideoCapture(
            self.camera_index
        )

        if not self.capture.isOpened():
            self.capture = None

            raise RuntimeError(
                f"No se pudo abrir la cámara "
                f"con índice {self.camera_index}"
            )

        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )

        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )

    def read(self):
        if self.capture is None:
            raise RuntimeError(
                "La cámara no está iniciada"
            )

        success, frame = self.capture.read()

        if not success:
            raise RuntimeError(
                "No se pudo capturar el frame"
            )

        return frame

    def process_current_frame(self):
        frame = self.read()

        current_time = time.time()

        elapsed = (
            current_time -
            self.last_processing_time
        )

        if elapsed < self.processing_interval:
            return self.last_result

        self.last_processing_time = current_time

        faces = face_service.detect(frame)

        results = []

        for detected_face in faces:

            face_image = face_service.extract_face(
                frame,
                detected_face
            )

            if face_image.size == 0:
                continue

            recognition = face_service.recognize(
                face_image
            )

            liveness = liveness_service.check(
                frame
            )

            x, y, width, height = detected_face

            results.append({
                "box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(width),
                    "height": int(height)
                },
                "recognition": recognition,
                "liveness": liveness
            })

        self.last_result = {
            "faces_detected": len(results),
            "faces": results
        }

        return self.last_result

    def stop(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.last_processing_time = 0.0

        self.last_result = {
            "faces_detected": 0,
            "faces": []
        }


camera_service = CameraService(
    camera_index=0,
    processing_interval=0.5
)