from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repo: backend/app/core/config.py -> subir 3 niveles
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Reconocimiento facial
    FACE_ENCRYPTION_KEY: str = ""
    FACE_THRESHOLD: float = 0.363
    FACE_MODELS_DIR: str = str(ROOT_DIR / "ai" / "face" / "models")

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")


settings = Settings()