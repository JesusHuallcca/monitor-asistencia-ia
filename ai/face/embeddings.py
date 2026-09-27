import cv2
import numpy as np


class FaceEmbedder:
    def __init__(self, size=(128, 128)):
        self.size = size

    def generate(self, face):
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, self.size)

        normalized = gray.astype(np.float32) / 255.0
        vector = normalized.flatten()

        norm = np.linalg.norm(vector)

        if norm == 0:
            return vector

        return vector / norm


def generate_embedding(face):
    return FaceEmbedder().generate(face)


def compare_embeddings(embedding_a, embedding_b):
    a = np.asarray(embedding_a, dtype=np.float32)
    b = np.asarray(embedding_b, dtype=np.float32)

    if a.shape != b.shape:
        return 0.0

    similarity = float(np.dot(a, b))
    return max(0.0, min(1.0, similarity))