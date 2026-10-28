"""Spawn-safe inference entry point. Receives an already validated frame in RAM."""


def infer_expression(connection, frame, model_path):
    try:
        import os, sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        import cv2
        import numpy as np
        from integraciones.emoscan.emotion_onnx import EmotionONNX

        h, w = frame.shape[:2]
        face_crop = None

        # 1. Usar el detector moderno YuNet (ONNX) presente en el repo
        yunet_path = os.path.join(root_dir, 'ai', 'face', 'models', 'face_detection_yunet_2023mar.onnx')
        if os.path.exists(yunet_path) and hasattr(cv2, 'FaceDetectorYN'):
            try:
                detector = cv2.FaceDetectorYN.create(yunet_path, '', (w, h), 0.55, 0.3, 5000)
                detector.setInputSize((w, h))
                _, faces = detector.detect(frame)
                if faces is not None and len(faces) == 1:
                    box = faces[0][:4].astype(int)
                    bx, by, bw, bh = max(0, box[0]), max(0, box[1]), max(1, box[2]), max(1, box[3])
                    face_crop = frame[by:by+bh, bx:bx+bw]
                elif faces is not None and len(faces) > 1:
                    connection.send({'status': 'NO_SINGLE_FACE'})
                    return
            except Exception:
                pass

        # 2. Fallback a CascadeClassifier si está disponible
        if face_crop is None and hasattr(cv2, 'CascadeClassifier'):
            try:
                cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = cascade.detectMultiScale(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                    scaleFactor=1.1, minNeighbors=8, minSize=(100, 100))
                if len(faces) == 1:
                    fx, fy, fw, fh = faces[0]
                    face_crop = frame[fy:fy+fh, fx:fx+fw]
                elif len(faces) > 1:
                    connection.send({'status': 'NO_SINGLE_FACE'})
                    return
            except Exception:
                pass

        # 3. Si no se detectó exactamente un rostro
        if face_crop is None:
            connection.send({'status': 'NO_SINGLE_FACE'})
            return

        # 4. Clasificar expresión con el modelo ONNX
        model = EmotionONNX(model_path, threads=1)
        label, scores = model.predict(face_crop)
        connection.send({
            'status': 'READY',
            'estimated_expression': label,
            'scores': scores,
            'model': 'FERPlus',
            'notice': 'Expresión facial estimada; no demuestra emociones internas.'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        connection.send({'status': 'UNAVAILABLE', 'error_detail': f'{type(e).__name__}: {str(e)}'})
    finally:
        connection.close()
