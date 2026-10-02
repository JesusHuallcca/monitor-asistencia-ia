import base64
import binascii

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.face_crypto import CryptoError, decrypt_embedding
from app.db.models import Rostro, Usuario
from app.services.face_engine import FaceError, FaceUnavailable, get_engine


class AttendanceFaceService:

    def _decode_image(self, image_data: str) -> bytes:
        if image_data.startswith("data:") and "," in image_data[:100]:
            image_data = image_data.split(",", 1)[1]

        try:
            return base64.b64decode(
                image_data,
                validate=True
            )
        except (binascii.Error, ValueError):
            raise FaceError("Imagen inválida")

    def recognize(
        self,
        db: Session,
        image_data: str
    ):
        try:
            engine = get_engine()
        except FaceUnavailable:
            raise

        image_bytes = self._decode_image(image_data)

        try:
            captured = engine.embedding(image_bytes)
        except FaceError:
            raise

        rostros = (
            db.query(Rostro, Usuario)
            .join(
                Usuario,
                Usuario.id == Rostro.usuario_id
            )
            .filter(
                Usuario.estado == "activo",
                Usuario.rol == "estudiante",
                Rostro.consentimiento == True,
                Rostro.login_facial_activo == True
            )
            .all()
        )

        if not rostros:
            return None

        mejor_usuario = None
        mejor_similitud = -1.0

        for rostro, usuario in rostros:
            try:
                guardado = decrypt_embedding(
                    rostro.embedding
                )
            except CryptoError:
                continue

            similitud = engine.similarity(
                captured,
                guardado
            )

            if similitud > mejor_similitud:
                mejor_similitud = similitud
                mejor_usuario = usuario

        if (
            mejor_usuario is None
            or mejor_similitud < settings.FACE_THRESHOLD
        ):
            return None

        return {
            "usuario_id": mejor_usuario.id,
            "username": mejor_usuario.username,
            "nombre": (
                f"{mejor_usuario.nombres} "
                f"{mejor_usuario.apellidos}"
            ),
            "confidence": mejor_similitud
        }


attendance_face_service = AttendanceFaceService()
