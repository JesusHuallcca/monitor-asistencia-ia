import cv2
import json
import numpy as np

from ai.face.detect import detect_faces
from ai.face.embeddings import generate_embedding
from ai.face.embeddings import compare_embeddings
from backend.app.db.face_repository import face_repository


PERSON_ID = "TEST001"
SAMPLES = 5
THRESHOLD = 0.82


def main():
    print("====================================")
    print("EVALUACION DE RECONOCIMIENTO FACIAL")
    print("====================================")
    print()

    record = face_repository.find_by_person_id(
        PERSON_ID
    )

    if record is None:
        raise RuntimeError(
            f"No existe el rostro registrado: {PERSON_ID}"
        )

    registered_embedding = np.asarray(
        json.loads(record["embedding"]),
        dtype=np.float32
    )

    print("Persona:", PERSON_ID)
    print(
        "Embedding:",
        registered_embedding.shape
    )
    print(
        "Norma:",
        np.linalg.norm(registered_embedding)
    )
    print()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "No se pudo abrir la cámara"
        )

    similarities = []

    print(
        f"Se capturarán {SAMPLES} muestras."
    )
    print(
        "Mira a la cámara y cambia "
        "ligeramente la posición del rostro."
    )
    print()

    try:
        while len(similarities) < SAMPLES:

            success, frame = camera.read()

            if not success:
                print(
                    "No se pudo capturar el frame"
                )
                break

            faces = detect_faces(frame)

            display = frame.copy()

            for x, y, width, height in faces:
                cv2.rectangle(
                    display,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2
                )

            cv2.putText(
                display,
                (
                    f"Muestras: "
                    f"{len(similarities)}/{SAMPLES}"
                ),
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Evaluacion FaceNet",
                display
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key != 13:
                continue

            print()

            if len(faces) != 1:
                print(
                    "Debe haber exactamente "
                    "un rostro."
                )
                continue

            x, y, width, height = faces[0]

            height_frame, width_frame = (
                frame.shape[:2]
            )

            x1 = max(0, x)
            y1 = max(0, y)

            x2 = min(
                width_frame,
                x + width
            )

            y2 = min(
                height_frame,
                y + height
            )

            face = frame[
                y1:y2,
                x1:x2
            ]

            if face.size == 0:
                print(
                    "Rostro inválido."
                )
                continue

            print(
                f"Generando muestra "
                f"{len(similarities) + 1}..."
            )

            current_embedding = (
                generate_embedding(face)
            )

            similarity = compare_embeddings(
                current_embedding,
                registered_embedding
            )

            similarities.append(
                float(similarity)
            )

            print(
                f"Similitud: {similarity:.6f}"
            )

            if similarity >= THRESHOLD:
                print("MATCH")
            else:
                print("NO MATCH")

            print()

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if not similarities:
        print(
            "No se obtuvieron muestras."
        )
        return

    values = np.asarray(
        similarities,
        dtype=np.float32
    )

    print("====================================")
    print("RESULTADOS")
    print("====================================")

    for index, value in enumerate(
        values,
        start=1
    ):
        print(
            f"Muestra {index}: "
            f"{value:.6f}"
        )

    print()
    print(
        f"MIN:  {values.min():.6f}"
    )
    print(
        f"MAX:  {values.max():.6f}"
    )
    print(
        f"MEAN: {values.mean():.6f}"
    )
    print(
        f"STD:  {values.std():.6f}"
    )
    print(
        f"THRESHOLD: {THRESHOLD:.2f}"
    )
    print(
        "===================================="
    )


if __name__ == "__main__":
    main()