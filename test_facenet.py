import cv2
import numpy as np

from ai.face.detect import detect_faces
from ai.face.embeddings import generate_embedding


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")

    print("====================================")
    print("PRUEBA DEEP LEARNING - FACENET")
    print("====================================")
    print()
    print("Mira a la cámara.")
    print("Mantén un solo rostro visible.")
    print("Presiona ENTER para capturar.")
    print("Presiona Q en la ventana para cancelar.")
    print()

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("No se pudo capturar el frame")
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
                "Prueba FaceNet",
                display
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == 13:
                print()
                print("Rostros detectados:", len(faces))

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
                    print("ERROR: rostro vacío")
                    continue

                print("Generando embedding FaceNet...")

                embedding = generate_embedding(face)

                print()
                print("========== RESULTADO ==========")
                print("MODELO: FaceNet")
                print("SHAPE:", embedding.shape)
                print(
                    "DIMENSIONES:",
                    embedding.size
                )
                print(
                    "NORMA L2:",
                    np.linalg.norm(embedding)
                )
                print(
                    "MIN:",
                    embedding.min()
                )
                print(
                    "MAX:",
                    embedding.max()
                )
                print(
                    "TIPO:",
                    embedding.dtype
                )
                print("===============================")
                print()

                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()