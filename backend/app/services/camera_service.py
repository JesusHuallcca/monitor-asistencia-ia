import cv2

from backend.app.services.face_service import face_service
from backend.app.services.liveness_service import liveness_service


class CameraService:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.capture = None

    def start(self):
        if self.capture is not None:
            return

        self.capture = cv2.VideoCapture(self.camera_index)

        if not self.capture.isOpened():
            self.capture = None
            raise RuntimeError(
                f"No se pudo abrir la cámara con índice {self.camera_index}"
            )

    def read(self):
        if self.capture is None:
            raise RuntimeError("La cámara no está iniciada")

        success, frame = self.capture.read()

        if not success:
            raise RuntimeError("No se pudo capturar el frame")

        return frame

    def process_current_frame(self):
        frame = self.read()

        faces = face_service.detect(frame)
        results = []

        for detected_face in faces:
            face_image = face_service.extract_face(
                frame,
                detected_face
            )

            if face_image.size == 0:
                continue

            recognition = face_service.recognize(face_image)
            liveness = liveness_service.check(frame)

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

        return {
            "faces_detected": len(results),
            "faces": results
        }

    def stop(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None


camera_service = CameraService()