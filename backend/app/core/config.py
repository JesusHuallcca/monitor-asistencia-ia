from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
# Raíz del repo: backend/app/core/config.py -> subir 3 niveles
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "monitor_asistencia"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    JWT_SECRET_KEY: str = "monitor-asistencia-default-secret-key-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Reconocimiento facial
    FACE_ENCRYPTION_KEY: str = ""
    FACE_THRESHOLD: float = 0.363
    FACE_MODELS_DIR: str = str(ROOT_DIR / "ai" / "face" / "models")
    # Análisis opcional de expresiones; separado del reconocimiento facial.
    EMOSCAN_ENABLED: bool = False
    EMOSCAN_MODEL_PATH: str = str(ROOT_DIR / "integraciones" / "emoscan" / "emotion-ferplus-8.onnx")
    EMOSCAN_QUEUE_SIZE: int = 4
    EMOSCAN_JOB_TTL_SECONDS: float = 10.0
    EMOSCAN_RESULT_TTL_SECONDS: float = Field(default=30.0, gt=0, le=30)
    EMOSCAN_MAX_RESULTS: int = 32
        # Chatbot IA
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    APP_TIMEZONE: str = "America/Lima"

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")


settings = Settings()
TIMEZONE = settings.APP_TIMEZONE
DEMO_MODE = os.getenv("CHATBOT_DEMO_MODE", "false").lower() == "true"
