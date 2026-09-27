from backend.app.db.face_repository import face_repository


def main():
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    class FakeEmbedding:
        def __init__(self, values):
            self.values = values

        def tolist(self):
            return self.values

    fake_embedding = FakeEmbedding(embedding)

    face_repository.save(
        person_id="TEST_REPO",
        embedding=fake_embedding
    )

    result = face_repository.find_by_person_id(
        "TEST_REPO"
    )

    print("RESULTADO:")
    print(result)

    if result is None:
        raise RuntimeError(
            "No se encontró el rostro guardado"
        )

    print("FACE REPOSITORY PERSISTENCE OK")


if __name__ == "__main__":
    main()