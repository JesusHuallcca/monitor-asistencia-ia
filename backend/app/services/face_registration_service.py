import numpy as np

from ai.face.embeddings import generate_embedding


class FaceRegistrationService:

    def __init__(self, minimum_samples=3):
        self.minimum_samples = minimum_samples

    def generate_samples(self, faces):
        embeddings = []

        for face in faces:
            if face is None or face.size == 0:
                continue

            embedding = generate_embedding(face)

            if embedding is not None:
                embeddings.append(
                    np.asarray(
                        embedding,
                        dtype=np.float32
                    )
                )

        return embeddings

    def build_embedding(self, embeddings):
        if len(embeddings) < self.minimum_samples:
            raise ValueError(
                f"Se requieren al menos "
                f"{self.minimum_samples} muestras"
            )

        matrix = np.vstack(embeddings)

        mean_embedding = np.mean(
            matrix,
            axis=0
        )

        norm = np.linalg.norm(
            mean_embedding
        )

        if norm == 0:
            raise ValueError(
                "No se pudo generar un embedding válido"
            )

        return mean_embedding / norm


face_registration_service = FaceRegistrationService()