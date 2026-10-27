#!/usr/bin/env python3
"""
EmoScan: Configuration Settings
Centralized configuration for the emotion recognition system
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"
DATASET_DIR = PROJECT_ROOT / "dataset"
UI_DIR = PROJECT_ROOT / "ui"

# Create directories if they don't exist
for directory in [MODELS_DIR, LOGS_DIR, DATASET_DIR, UI_DIR]:
    directory.mkdir(exist_ok=True)

# Emotion recognition settings
EMOTIONS = ['happy', 'sad', 'angry', 'neutral', 'surprise', 'fear', 'disgust', 'contempt']
EMOTION_COLORS = {
    'happy': '#2ecc71',      # Green
    'sad': '#3498db',        # Blue
    'angry': '#e74c3c',      # Red
    'neutral': '#95a5a6',    # Gray
    'surprise': '#f39c12',   # Orange
    'fear': '#9b59b6',       # Purple
    'disgust': '#e67e22',    # Dark Orange
    'contempt': '#7f8c8d'
}

# Face detection settings
FACE_DETECTION = {
    'scale_factor': 1.1,
    'min_neighbors': 8,
    'min_size': (100, 100),
    'cascade_file': 'haarcascade_frontalface_default.xml'
}

# Video processing settings
VIDEO_SETTINGS = {
    'camera_index': 0,
    'frame_width': 640,
    'frame_height': 480,
    'fps': 30,
    'processing_interval': 0.03  # seconds between frame processing
}

# DeepFace settings
DEEPFACE_SETTINGS = {
    'enforce_detection': False,
    'detector_backend': 'opencv',
    'actions': ['emotion'],
    'models': ['emotion']
}

# UI settings
UI_SETTINGS = {
    'window_width': 1200,
    'window_height': 800,
    'theme': {
        'primary_bg': '#2c3e50',
        'secondary_bg': '#34495e',
        'text_color': '#ecf0f1',
        'accent_color': '#3498db'
    }
}

# Web interface settings
WEB_SETTINGS = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'threaded': True
}

# Logging settings
LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'emotion_detection.log'
}

# CSV logging settings
CSV_LOGGING = {
    'enabled': True,
    'directory': LOGS_DIR,
    'filename_prefix': 'emotion_session',
    'include_timestamp': True,
    'columns': ['timestamp', 'dominant_emotion', *EMOTIONS]
}

# Visualization settings
VISUALIZATION = {
    'enabled': True,
    'max_data_points': 100,
    'update_interval': 1000,  # milliseconds
    'chart_types': ['line', 'bar', 'pie'],
    'save_format': 'png',
    'dpi': 300
}

# Performance settings
PERFORMANCE = {
    'max_faces': 10,
    'confidence_threshold': 0.5,
    'batch_processing': False,
    'gpu_acceleration': False
}

# Model paths
MODEL_PATHS = {
    'emotion_onnx': PROJECT_ROOT / 'emotion-ferplus-8.onnx',
    'haar_cascade': MODELS_DIR / FACE_DETECTION['cascade_file']
}

# Development settings
DEVELOPMENT = {
    'debug_mode': True,
    'verbose_logging': True,
    'save_debug_frames': False,
    'test_mode': False
}

# Environment variables
def get_env_setting(key, default=None):
    """Get setting from environment variable"""
    return os.environ.get(f'EMOSCAN_{key.upper()}', default)

# Override settings with environment variables if present
CAMERA_INDEX = get_env_setting('camera_index', VIDEO_SETTINGS['camera_index'])
WEB_PORT = get_env_setting('web_port', WEB_SETTINGS['port'])
DEBUG_MODE = get_env_setting('debug_mode', DEVELOPMENT['debug_mode'])

# Update settings with environment variables
VIDEO_SETTINGS['camera_index'] = CAMERA_INDEX
WEB_SETTINGS['port'] = WEB_PORT
DEVELOPMENT['debug_mode'] = DEBUG_MODE

# Validation functions
def validate_config():
    """Validate configuration settings"""
    errors = []

    # Check if required directories exist
    for dir_name, dir_path in [('models', MODELS_DIR), ('logs', LOGS_DIR)]:
        if not dir_path.exists():
            errors.append(f"Required directory '{dir_name}' does not exist: {dir_path}")

    # Check if camera index is valid
    if not isinstance(VIDEO_SETTINGS['camera_index'], int) or VIDEO_SETTINGS['camera_index'] < 0:
        errors.append("Camera index must be a non-negative integer")

    # Check if emotions list is valid
    if not EMOTIONS or len(EMOTIONS) < 2:
        errors.append("At least 2 emotions must be defined")

    # Check if port is valid
    if not isinstance(WEB_SETTINGS['port'], int) or not (1024 <= WEB_SETTINGS['port'] <= 65535):
        errors.append("Web port must be between 1024 and 65535")

    return errors

def print_config_summary():
    """Print a summary of the current configuration"""
    print("EmoScan Configuration Summary")
    print("=" * 40)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print(f"Camera Index: {VIDEO_SETTINGS['camera_index']}")
    print(f"Web Port: {WEB_SETTINGS['port']}")
    print(f"Debug Mode: {DEVELOPMENT['debug_mode']}")
    print(f"Emotions: {', '.join(EMOTIONS)}")
    print("=" * 40)

if __name__ == "__main__":
    # Validate configuration when run directly
    errors = validate_config()
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    else:
        print_config_summary()
        print("✅ Configuration is valid!")
