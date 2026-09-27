import cv2
import numpy as np
from keras_facenet import FaceNet


class FaceEmbedder:
    def __init__(self):
        self.model = FaceNet()

    def generate(self, face):
        if face is None or face.size == 0:
            return np.array([], dtype=np.float32)

        rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        face_input = cv2.resize(rgb, (160, 160))

        face_input = face_input.astype(np.float32)

        face_input = np.expand_dims(face_input, axis=0)

        embedding = self.model.embeddings(face_input)[0]

        embedding = np.asarray(embedding, dtype=np.float32)

        norm = np.linalg.norm(embedding)

        if norm == 0:
            return embedding

        return embedding / norm


_embedder = FaceEmbedder()


def generate_embedding(face):
    return _embedder.generate(face)


def compare_embeddings(embedding_a, embedding_b):
    a = np.asarray(embedding_a, dtype=np.float32)
    b = np.asarray(embedding_b, dtype=np.float32)

    if a.shape != b.shape:
        return 0.0

    if a.size == 0 or b.size == 0:
        return 0.0

    similarity = float(np.dot(a, b))

    return max(0.0, min(1.0, similarity))