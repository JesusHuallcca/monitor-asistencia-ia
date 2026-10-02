import numpy as np
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CryptoError(Exception):
    pass


def _fernet() -> Fernet:
    if not settings.FACE_ENCRYPTION_KEY:
        raise CryptoError("Falta FACE_ENCRYPTION_KEY en el .env")
    try:
        return Fernet(settings.FACE_ENCRYPTION_KEY.encode())
    except ValueError:
        raise CryptoError("FACE_ENCRYPTION_KEY no es una clave Fernet válida")


def encrypt_embedding(vector: np.ndarray) -> bytes:
    return _fernet().encrypt(vector.astype(np.float32).tobytes())


def decrypt_embedding(blob: bytes) -> np.ndarray:
    try:
        crudo = _fernet().decrypt(blob)
    except InvalidToken:
        raise CryptoError("No se pudo descifrar el rostro guardado")
    return np.frombuffer(crudo, dtype=np.float32)