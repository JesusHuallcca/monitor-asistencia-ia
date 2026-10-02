import base64
import time

import cv2
import requests


API_URL = "http://127.0.0.1:8000/api/attendance/camera/check-in"
RESET_URL = "http://127.0.0.1:8000/api/attendance/camera/reset"


def frame_to_base64(frame):
    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 75]
    )

    if not success:
        raise RuntimeError("No se pudo convertir el frame")

    return base64.b64encode(buffer).decode("utf-8")


def main():
    requests.post(RESET_URL)

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("No se pudo abrir la cámara")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Cámara iniciada.")
    print("Mira a la cámara y mueve ligeramente la cabeza.")
    print("Presiona Q para salir.")

    last_request = 0
    request_interval = 1.0

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("No se pudo capturar el frame")
                break

            current_time = time.time()

            if current_time - last_request >= request_interval:
                last_request = current_time

                image = frame_to_base64(frame)

                response = requests.post(
                    API_URL,
                    json={"image": image},
                    timeout=10
                )

                data = response.json()

                status = data.get("status", "")

                print(
                    f"STATUS: {status} | "
                    f"PERSONA: {data.get('person_id', '-')}"
                )

                if status == "REGISTERED":
                    print("ASISTENCIA REGISTRADA")
                    break

                if status == "ALREADY_REGISTERED":
                    print("ASISTENCIA YA REGISTRADA HOY")
                    break

                if status == "UNKNOWN_FACE":
                    print("ROSTRO NO RECONOCIDO")

                if status == "LIVENESS_PENDING":
                    liveness = data.get("liveness", {})
                    print(
                        f"  Liveness: {liveness.get('score', 0):.2f}"
                    )

                if status == "RECOGNITION_PENDING":
                    print(
                        f"  Reconocimientos: "
                        f"{data.get('recognitions', 0)}/"
                        f"{data.get('required', 3)}"
                    )

            cv2.putText(
                frame,
                "Monitor de Asistencia IA",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Monitor de Asistencia IA",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()