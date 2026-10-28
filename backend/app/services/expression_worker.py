"""Spawn-safe inference entry point. Receives an already validated frame in RAM."""


def infer_expression(connection, frame, model_path):
    try:
        import os, sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        import cv2
        from integraciones.emoscan.emotion_onnx import EmotionONNX


        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = cascade.detectMultiScale(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
        if len(faces) != 1:
            connection.send({'status': 'NO_SINGLE_FACE'})
            return
        x, y, width, height = faces[0]
        model = EmotionONNX(model_path, threads=1)
        label, scores = model.predict(frame[y:y+height, x:x+width])
        connection.send({'status': 'READY', 'estimated_expression': label,
                         'scores': scores, 'model': 'FERPlus',
                         'notice': 'Expresión facial estimada; no demuestra emociones internas.'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        connection.send({'status': 'UNAVAILABLE'})

    finally:
        connection.close()
