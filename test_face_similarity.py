import cv2
import json
import numpy as np

from ai.face.detect import detect_faces
from ai.face.embeddings import (
    generate_embedding,
    compare_embeddings
)
from backend.app.db.face_repository import face_repository


PERSON_ID = "TEST001"


def main():
    print("====================================")
    print("EVALUACION DE SIMILITUD FACIAL")
    print("====================================")
    print()

    record = face_repository.find_by_person_id(PERSON_ID)

    if record is None:
        raise RuntimeError(
            f"No existe un rostro registrado para {PERSON_ID}"
        )

    registered_embedding = np.asarray(
        json.loads(record["embedding"]),
        dtype=np.float32
    )

    print("Persona registrada:", PERSON_ID)
    print(
        "Embedding registrado:",
        registered_embedding.shape
    )
    print(
        "Norma registrada:",
        np.linalg.norm(registered_embedding)
    )
    print()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "No se pudo abrir la cámara"
        )

    print("Mira a la cámara.")
    print("Mantén un solo rostro visible.")
    print("Presiona ENTER para evaluar.")
    print("Presiona Q para cancelar.")
    print()

    try:
        while True:
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
                f"Rostros: {len(faces)}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Evaluacion Facial",
                display
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == 13:
                print()
                print(
                    "Rostros detectados:",
                    len(faces)
                )

                if len(faces) != 1:
                    print(
                        "ERROR: debe haber exactamente "
                        "un rostro"
                    )
                    continue

                x, y, width, height = faces[0]

                height_frame, width_frame = frame.shape[:2]

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
                        "ERROR: rostro vacío"
                    )
                    continue

                print(
                    "Generando embedding actual..."
                )

                current_embedding = (
                    generate_embedding(face)
                )

                print(
                    "Embedding actual:",
                    current_embedding.shape
                )

                similarity = compare_embeddings(
                    current_embedding,
                    registered_embedding
                )

                print()
                print(
                    "========== RESULTADO =========="
                )
                print(
                    "PERSONA:",
                    PERSON_ID
                )
                print(
                    "SIMILITUD:",
                    similarity
                )
                print(
                    "THRESHOLD:",
                    0.82
                )

                if similarity >= 0.82:
                    print(
                        "RESULTADO: MATCH"
                    )
                else:
                    print(
                        "RESULTADO: NO MATCH"
                    )

                print(
                    "==============================="
                )
                print()

                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()