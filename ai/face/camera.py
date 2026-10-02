import cv2


class Camera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.capture = None

    def start(self):
        self.capture = cv2.VideoCapture(self.camera_index)

        if not self.capture.isOpened():
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

    def stop(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None


def open_camera(camera_index=0):
    camera = Camera(camera_index)
    camera.start()
    return camera