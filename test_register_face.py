import base64
import time

import cv2
import requests


API_URL = "http://127.0.0.1:8000/api/face/register/multiple"

PERSON_ID = "TEST001"


def frame_to_base64(frame):
    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 90]
    )

    if not success:
        raise RuntimeError("No se pudo convertir el frame")

    return base64.b64encode(buffer).decode("utf-8")


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("====================================")
    print("REGISTRO FACIAL")
    print("====================================")
    print("Persona:", PERSON_ID)
    print()
    print("Mira a la cámara.")
    print("Mantén el rostro centrado.")
    print("Se capturarán 5 muestras.")
    print("Presiona Q para cancelar.")
    print()

    samples = []

    try:
        while len(samples) < 5:
            success, frame = camera.read()

            if not success:
                print("No se pudo capturar el frame")
                break

            cv2.putText(
                frame,
                f"Registro facial: {len(samples)}/5",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Mira a la camara",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Registro Facial - Monitor IA",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Registro cancelado")
                return

            if len(samples) == 0:
                time.sleep(1.0)
                samples.append(frame.copy())
                print("Muestra 1 capturada")
                continue

            if len(samples) == 1:
                time.sleep(0.8)
                samples.append(frame.copy())
                print("Muestra 2 capturada")
                continue

            if len(samples) == 2:
                time.sleep(0.8)
                samples.append(frame.copy())
                print("Muestra 3 capturada")
                continue

            if len(samples) == 3:
                time.sleep(0.8)
                samples.append(frame.copy())
                print("Muestra 4 capturada")
                continue

            if len(samples) == 4:
                time.sleep(0.8)
                samples.append(frame.copy())
                print("Muestra 5 capturada")
                continue

        if len(samples) < 5:
            print("No se obtuvieron suficientes muestras")
            return

        print()
        print("Enviando muestras al backend...")

        images = [
            frame_to_base64(frame)
            for frame in samples
        ]

        response = requests.post(
            API_URL,
            json={
                "person_id": PERSON_ID,
                "images": images
            },
            timeout=60
        )

        print()
        print("HTTP:", response.status_code)
        print("RESPUESTA:")

        try:
            print(response.json())
        except Exception:
            print(response.text)

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

