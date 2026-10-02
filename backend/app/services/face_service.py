import json

import numpy as np

from ai.face.detect import detect_faces
from ai.face.embeddings import generate_embedding
from ai.face.recognize import FaceRecognizer
from backend.app.db.face_repository import face_repository


class FaceService:

    def __init__(self):
        self.recognizer = FaceRecognizer()
        self.load_faces_from_database()

    def load_faces_from_database(self):
        records = face_repository.find_all()

        for record in records:
            try:
                embedding = np.asarray(
                    json.loads(record["embedding"]),
                    dtype=np.float32
                )

                self.recognizer.known_faces[
                    str(record["person_id"])
                ] = embedding

            except Exception as error:
                print(
                    f"No se pudo cargar el rostro "
                    f"{record.get('person_id')}: {error}"
                )

    def detect(self, frame):
        return detect_faces(frame)

    def extract_face(self, frame, face):
        x, y, width, height = face

        height_frame, width_frame = frame.shape[:2]

        x1 = max(0, x)
        y1 = max(0, y)

        x2 = min(width_frame, x + width)
        y2 = min(height_frame, y + height)

        return frame[y1:y2, x1:x2]

    def create_embedding(self, face):
        return generate_embedding(face)

    def register_face(self, person_id, face):
        embedding = generate_embedding(face)

        face_repository.save(
            person_id,
            embedding
        )

        self.recognizer.register(
            person_id,
            face
        )

        return {
            "person_id": str(person_id),
            "registered": True
        }

    def recognize(self, face):
        return self.recognizer.recognize(face)

    def process_frame(self, frame):
        faces = self.detect(frame)

        results = []

        for detected_face in faces:
            face_image = self.extract_face(
                frame,
                detected_face
            )

            if face_image.size == 0:
                continue

            recognition = self.recognize(
                face_image
            )

            x, y, width, height = detected_face

            results.append({
                "box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(width),
                    "height": int(height)
                },
                "recognition": recognition
            })

        return results


face_service = FaceService()