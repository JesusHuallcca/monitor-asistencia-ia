import cv2
import json
import numpy as np

from ai.face.detect import detect_faces
from ai.face.embeddings import generate_embedding
from ai.face.embeddings import compare_embeddings
from backend.app.db.face_repository import face_repository


PERSON_ID = "TEST001"
SAMPLES = 5


def load_registered_embedding():
    record = face_repository.find_by_person_id(
        PERSON_ID
    )

    if record is None:
        raise RuntimeError(
            f"No existe el rostro registrado: {PERSON_ID}"
        )

    embedding = np.asarray(
        json.loads(record["embedding"]),
        dtype=np.float32
    )

    return embedding


def capture_face():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "No se pudo abrir la cámara"
        )

    print()
    print("====================================")
    print("EVALUACION DE ROSTRO DESCONOCIDO")
    print("====================================")
    print()
    print(
        f"Se capturarán {SAMPLES} muestras."
    )
    print(
        "Usa una persona que NO sea TEST001."
    )
    print(
        "Presiona ENTER para cada muestra."
    )
    print(
        "Presiona Q para cancelar."
    )
    print()

    embeddings = []

    try:
        while len(embeddings) < SAMPLES:

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
                    f"{len(embeddings)}/{SAMPLES}"
                ),
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Evaluacion Rostro Desconocido",
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
                f"{len(embeddings) + 1}..."
            )

            embedding = generate_embedding(
                face
            )

            if embedding.size == 0:
                print(
                    "Embedding vacío."
                )
                continue

            embeddings.append(
                embedding
            )

            print("Muestra capturada.")
            print()

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return embeddings


def main():
    registered_embedding = (
        load_registered_embedding()
    )

    print(
        "Embedding TEST001:",
        registered_embedding.shape
    )

    embeddings = capture_face()

    if not embeddings:
        print(
            "No se capturaron muestras."
        )
        return

    similarities = []

    for embedding in embeddings:

        similarity = compare_embeddings(
            embedding,
            registered_embedding
        )

        similarities.append(
            float(similarity)
        )

    values = np.asarray(
        similarities,
        dtype=np.float32
    )

    print()
    print("====================================")
    print("RESULTADOS IMPOSTOR")
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
        "===================================="
    )


if __name__ == "__main__":
    main()