"""FERPlus ONNX real expression classification (not inner emotional state)."""
from pathlib import Path
if __package__:
    from . import config
else:
    import config
import cv2
import numpy as np
import onnxruntime as ort

MODEL = config.MODEL_PATHS['emotion_onnx']
CLASSES = ("neutral", "happy", "surprise", "sad", "angry", "disgust", "fear", "contempt")

class EmotionONNX:
    def __init__(self, model_path=MODEL, *, threads=None):
        model_path = Path(model_path)
        if not model_path.is_file() or model_path.stat().st_size < 1000000:
            raise FileNotFoundError(f"Modelo FERPlus no encontrado o incompleto: {model_path}")
        try:
            options = ort.SessionOptions()
            if threads is not None:
                options.intra_op_num_threads = threads
                options.inter_op_num_threads = threads
            self.session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            shape = self.session.get_inputs()[0].shape
            if len(shape) != 4 or shape[1:] != [1, 64, 64] or self.session.get_inputs()[0].type != 'tensor(float)':
                raise ValueError(f"Dimensiones inesperadas del modelo: {shape}")
        except Exception as exc:
            raise RuntimeError(f"No se pudo inicializar ONNX: {exc}") from exc

    def predict(self, face_bgr):
        if face_bgr is None or face_bgr.size == 0:
            raise RuntimeError("Recorte facial vacío")
        if face_bgr.ndim != 3 or face_bgr.shape[2] != 3 or face_bgr.dtype != np.uint8:
            raise RuntimeError("Se requiere un recorte BGR uint8 de tres canales")
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_LINEAR)
        data = resized.astype(np.float32)[None, None, :, :]
        try:
            result = self.session.run(None, {self.input_name: data})[0]
            scores = np.asarray(result, dtype=np.float64).reshape(-1)
            if scores.size != 8 or not np.isfinite(scores).all():
                raise ValueError("El modelo no devolvió 8 puntuaciones válidas")
            scores -= np.max(scores)
            exp = np.exp(scores)
            probs = exp / exp.sum()
            # Informar las ocho clases reales en el orden de salida FERPlus.
            winner = CLASSES[int(np.argmax(probs))]
            return winner, {key: float(probs[i]) for i, key in enumerate(CLASSES)}
        except Exception as exc:
            raise RuntimeError(f"Fallo en inferencia ONNX: {exc}") from exc