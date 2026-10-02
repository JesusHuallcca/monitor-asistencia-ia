import cv2
from insightface.app import FaceAnalysis


class FaceDetector:
    def __init__(self):
        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"]
        )

        self.app.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

    def detect(self, frame):
        faces = self.app.get(frame)

        results = []

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)

            results.append(
                (
                    int(x1),
                    int(y1),
                    int(x2 - x1),
                    int(y2 - y1)
                )
            )

        return results


_detector = FaceDetector()


def detect_faces(frame):
    return _detector.detect(frame)