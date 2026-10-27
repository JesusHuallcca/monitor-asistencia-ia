#!/usr/bin/env python3
"""
EmoScan: Flask Web Interface
Web-based alternative to the Tkinter UI for emotion recognition
"""

from flask import Flask, render_template, Response, jsonify, request, abort
import cv2
import numpy as np
import pandas as pd
import os
import threading
import time
from datetime import datetime
import logging
import json
import config  # <-- Add this import

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app with correct template folder
app = Flask(__name__, template_folder='ui/templates')

# Orígenes permitidos para embeber / acceder a EmoScan desde el Monitor (desarrollo).
# En producción, restringir a tu dominio real y preferir un proxy inverso con JWT.
ALLOWED_REFERER_HINTS = (
    "127.0.0.1:8001",
    "localhost:8001",
    "127.0.0.1:5500",
    "localhost:5500",
    "127.0.0.1:5000",
    "localhost:5000",
)

@app.after_request
def permitir_iframe_desde_monitor(response):
    """Permite embeber EmoScan en iframe del mismo equipo (Monitor en :8001)."""
    # SAMEORIGIN evita clickjacking desde sitios externos; el Monitor y EmoScan
    # en local usan puertos distintos, así que se relaja solo en desarrollo.
    response.headers["X-Frame-Options"] = "ALLOWALL"
    # Cabecera moderna equivalente (mejor soporte en navegadores actuales)
    response.headers["Content-Security-Policy"] = "frame-ancestors 'self' http://127.0.0.1:8001 http://localhost:8001 http://127.0.0.1:5500 http://localhost:5500"
    # ALLOWALL no es estándar en todos los navegadores; se complementa con CSP.
    if "X-Frame-Options" in response.headers and response.headers["X-Frame-Options"] == "ALLOWALL":
        del response.headers["X-Frame-Options"]
    return response

@app.before_request
def bloquear_accesos_no_autorizados():
    """
    Bloqueo básico de accesos directos en desarrollo.
    - Permite peticiones cuyo Referer viene del Monitor o del propio EmoScan.
    - Permite rutas de API/streaming usadas por la interfaz (video_feed, etc.).
    - No sustituye autenticación JWT del Monitor; documentado como pendiente de proxy.
    """
    # Rutas internas de la app (streaming y controles) deben funcionar siempre
    # una vez cargada la interfaz, aunque el Referer varíe.
    path = request.path or ""
    if path.startswith(("/video_feed", "/start_detection", "/stop_detection",
                        "/get_stats", "/save_log", "/reset_stats", "/static")):
        return

    referer = request.referrer or ""
    # Acceso directo sin referer a la página principal: se permite en desarrollo
    # para poder depurar EmoScan solo, pero se registra.
    if not referer:
        logger.info("Acceso a EmoScan sin Referer (depuración o acceso directo)")
        return

    if any(hint in referer for hint in ALLOWED_REFERER_HINTS):
        return

    logger.warning(f"Acceso bloqueado por seguridad. Origen intentado: {referer}")
    abort(403)

class WebEmotionDetector:
    """Web-based emotion detector for Flask interface"""

    def __init__(self):
        self.emotions = list(config.EMOTIONS)
        self.emotion_counts = {emotion: 0 for emotion in self.emotions}
        self.session_data = []
        self.is_running = False
        self.cap = None
        self.face_cascade = None
        self.current_frame = None
        self.fer_model = None
        self.setup_face_detection()
        self.setup_emotion_detection()

    def setup_face_detection(self):
        """Initialize face detection cascade classifier"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + config.FACE_DETECTION['cascade_file'])
            if self.face_cascade.empty():
                raise Exception("Failed to load face cascade")
            logger.info("Face detection cascade loaded successfully")
        except Exception as e:
            logger.error(f"Error loading face cascade: {e}")

    def setup_emotion_detection(self):
        """Carga un modelo real FERPlus ONNX. Nunca genera etiquetas aleatorias."""
        from emotion_onnx import EmotionONNX
        try:
            self.fer_model = EmotionONNX()
            logger.info("Modelo de expresiones FERPlus ONNX cargado correctamente")
        except (FileNotFoundError, RuntimeError, ImportError) as error:
            self.fer_model = None
            logger.error("Clasificador ONNX no disponible: %s", error)

    def detect_emotion(self, face_img):
        if self.fer_model is None:
            raise RuntimeError("Modelo ONNX no disponible. Ejecuta descargar_modelo.py")
        return self.fer_model.predict(face_img)

    def process_frame(self, frame):
        """Process a single frame for face detection and emotion recognition"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Configuración más estricta: scaleFactor=1.1, minNeighbors=8, minSize=(100, 100)
        settings = config.FACE_DETECTION
        faces = self.face_cascade.detectMultiScale(
            gray, settings['scale_factor'], settings['min_neighbors'], minSize=settings['min_size'])

        processed_frame = frame.copy()
        emotions_detected = []

        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = frame[y:y+h, x:x+w]

            # Detect emotion
            try:
                dominant_emotion, emotion_scores = self.detect_emotion(face_roi)
            except RuntimeError as error:
                logger.warning("No se pudo clasificar el rostro: %s", error)
                continue
            emotions_detected.append(dominant_emotion)

            # Update emotion counts
            self.emotion_counts[dominant_emotion] += 1

            # Draw rectangle around face
            # Marco Tech Neón
            l = int(w * 0.2)
            cv2.rectangle(processed_frame, (x, y), (x + w, y + h), (248, 189, 56), 1)
            # Esquinas destacadas
            cv2.line(processed_frame, (x, y), (x + l, y), (248, 189, 56), 3)
            cv2.line(processed_frame, (x, y), (x, y + l), (248, 189, 56), 3)
            cv2.line(processed_frame, (x + w, y), (x + w - l, y), (248, 189, 56), 3)
            cv2.line(processed_frame, (x + w, y), (x + w, y + l), (248, 189, 56), 3)
            cv2.line(processed_frame, (x, y + h), (x + l, y + h), (248, 189, 56), 3)
            cv2.line(processed_frame, (x, y + h), (x, y + h - l), (248, 189, 56), 3)
            cv2.line(processed_frame, (x + w, y + h), (x + w - l, y + h), (248, 189, 56), 3)
            cv2.line(processed_frame, (x + w, y + h), (x + w, y + h - l), (248, 189, 56), 3)

            # Add emotion label
            label = f"{dominant_emotion.upper()}"
            cv2.putText(processed_frame, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Log emotion data
            self.log_emotion(dominant_emotion, emotion_scores)

        return processed_frame, emotions_detected

    def log_emotion(self, dominant_emotion, emotion_scores):
        """Log emotion data to session storage"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = {
            'timestamp': timestamp,
            'dominant_emotion': dominant_emotion,
            **emotion_scores
        }
        self.session_data.append(log_entry)

    def save_session_log(self):
        """Save session data to CSV file"""
        if not self.session_data:
            return None

        os.makedirs(config.LOGS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(config.LOGS_DIR / f"emotion_session_web_{timestamp}.csv")

        df = pd.DataFrame(self.session_data)
        df.to_csv(filename, index=False)
        logger.info(f"Session log saved to {filename}")
        return filename

    def start_detection(self):
        """Start the emotion detection process"""
        try:
            if self.fer_model is None:
                raise RuntimeError("Modelo ONNX no está disponible. Instala las dependencias y descarga el modelo.")
            self.session_data = []
            self.emotion_counts = {emotion: 0 for emotion in self.emotions}
            self.cap = cv2.VideoCapture(int(config.VIDEO_SETTINGS['camera_index']))  # Use config camera index
            if not self.cap.isOpened():
                raise Exception("Could not open webcam")

            self.is_running = True
            logger.info("Web emotion detection started")
            return True
        except Exception as e:
            logger.error(f"Error starting detection: {e}")
            return False

    def stop_detection(self):
        """Stop the emotion detection process"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info("Web emotion detection stopped")

    def get_frame(self):
        """Get current frame for web streaming"""
        if not self.is_running or not self.cap:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        processed_frame, emotions = self.process_frame(frame)
        self.current_frame = processed_frame
        return processed_frame

# Global detector instance
detector = WebEmotionDetector()

def generate_frames():
    """Generate video frames for web streaming"""
    while detector.is_running:
        frame = detector.get_frame()
        if frame is not None:
            # Encode frame for web streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start emotion detection"""
    try:
        success = detector.start_detection()
        if success:
            return jsonify({'status': 'success', 'message': 'Detection started'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to start detection'})
    except Exception as e:
        logger.error(f"Error in start_detection: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    """Stop emotion detection"""
    try:
        detector.stop_detection()
        return jsonify({'status': 'success', 'message': 'Detection stopped'})
    except Exception as e:
        logger.error(f"Error in stop_detection: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/health')
def health():
    return jsonify({'status': 'ok' if detector.fer_model is not None else 'model_unavailable',
                    'onnx_loaded': detector.fer_model is not None,
                    'camera_running': detector.is_running,
                    'mode': 'onnx_ferplus_real_only'})

@app.route('/get_stats')
def get_stats():
    """Get current emotion statistics"""
    try:
        return jsonify({
            'status': 'success',
            'emotion_counts': detector.emotion_counts,
            'total_detections': sum(detector.emotion_counts.values())
        })
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save_log', methods=['POST'])
def save_log():
    """Save session log"""
    try:
        filename = detector.save_session_log()
        if filename:
            return jsonify({
                'status': 'success',
                'message': 'Session log saved',
                'filename': filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No session data to save'
            })
    except Exception as e:
        logger.error(f"Error in save_log: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    """Reset emotion statistics"""
    try:
        detector.emotion_counts = {emotion: 0 for emotion in detector.emotions}
        detector.session_data = []
        return jsonify({'status': 'success', 'message': 'Statistics reset'})
    except Exception as e:
        logger.error(f"Error in reset_stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("🌐 Starting EmoScan Web Interface")
    print("=" * 50)
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"❌ Error: {e}")
    finally:
        detector.stop_detection()
