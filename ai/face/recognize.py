from ai.face.embeddings import generate_embedding, compare_embeddings


class FaceRecognizer:
    def __init__(self, threshold=0.82):
        self.threshold = threshold
        self.known_faces = {}

    def register(self, person_id, face):
        embedding = generate_embedding(face)
        self.known_faces[str(person_id)] = embedding

    def recognize(self, face):
        if not self.known_faces:
            return None

        embedding = generate_embedding(face)

        best_person = None
        best_score = 0.0

        for person_id, known_embedding in self.known_faces.items():
            score = compare_embeddings(embedding, known_embedding)

            if score > best_score:
                best_score = score
                best_person = person_id

        if best_score >= self.threshold:
            return {
                "person_id": best_person,
                "confidence": best_score
            }

        return None


def recognize_face(face, known_faces, threshold=0.82):
    recognizer = FaceRecognizer(threshold)

    for person_id, known_face in known_faces.items():
        recognizer.register(person_id, known_face)

    return recognizer.recognize(face)