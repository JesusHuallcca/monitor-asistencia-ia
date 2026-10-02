import base64

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import Usuario
from app.services.attendance_face_service import attendance_face_service
from app.services.attendance_service import attendance_service
from app.services.liveness_service import liveness_service


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance AI"]
)


class AttendanceRequest(BaseModel):
    image: str


def decode_image(image_data: str):
    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)

        array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            array,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            raise ValueError("Imagen inválida")

        return frame

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="No se pudo decodificar la imagen"
        )


@router.get("/health")
def attendance_health():
    return {
        "status": "ok",
        "module": "attendance-ai"
    }


@router.get("/")
def get_attendances(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_roles("admin", "superadmin", "profesor"))
):
    attendances = attendance_service.get_all(db)

    return {
        "count": len(attendances),
        "attendances": attendances
    }


@router.post("/check-in")
def check_in(
    request: AttendanceRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    frame = decode_image(request.image)

    try:
        reconocimiento = attendance_face_service.recognize(
            db=db,
            image_data=request.image
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if reconocimiento is None:
        return {
            "success": False,
            "status": "UNKNOWN_FACE",
            "message": "Rostro no reconocido"
        }

    if reconocimiento["usuario_id"] != user.id:
        return {
            "success": False,
            "status": "IDENTITY_MISMATCH",
            "message": "El rostro no coincide con el usuario autenticado"
        }

    liveness = liveness_service.check(frame)

    if not liveness["is_live"]:
        return {
            "success": False,
            "status": "LIVENESS_FAILED",
            "message": "No se pudo validar que el rostro corresponda a una persona presente",
            "usuario_id": reconocimiento["usuario_id"],
            "confidence": reconocimiento["confidence"],
            "liveness": liveness
        }

    result = attendance_service.register(
        db=db,
        usuario_id=reconocimiento["usuario_id"],
        confidence=reconocimiento["confidence"],
        liveness_score=liveness["score"]
    )

    return {
        **result,
        "recognition": reconocimiento,
        "liveness": liveness
    }


@router.delete("/")
def clear_attendances():
    return {
        "success": False,
        "message": "Las asistencias ahora se almacenan en MySQL y no se eliminan desde este endpoint"
    }


@router.post("/camera/reset")
def reset_attendance_camera(user: Usuario = Depends(get_current_user)):
    from app.services.attendance_camera_service import attendance_camera_service

    attendance_camera_service.reset()

    return {
        "success": True,
        "message": "Sesión de cámara reiniciada"
    }


@router.post("/camera/check-in")
def camera_check_in(
    request: AttendanceRequest,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    frame = decode_image(request.image)

    try:
        reconocimiento = attendance_face_service.recognize(
            db=db,
            image_data=request.image
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    if reconocimiento is None:
        return {
            "success": False,
            "status": "UNKNOWN_FACE",
            "message": "Rostro no reconocido"
        }

    if reconocimiento["usuario_id"] != user.id:
        return {
            "success": False,
            "status": "IDENTITY_MISMATCH",
            "message": "El rostro no coincide con el usuario autenticado"
        }

    liveness = liveness_service.check(frame)

    if not liveness["is_live"]:
        return {
            "success": False,
            "status": "LIVENESS_FAILED",
            "message": "No se pudo validar que el rostro corresponda a una persona presente",
            "usuario_id": reconocimiento["usuario_id"],
            "confidence": reconocimiento["confidence"],
            "liveness": liveness
        }

    result = attendance_service.register(
        db=db,
        usuario_id=reconocimiento["usuario_id"],
        confidence=reconocimiento["confidence"],
        liveness_score=liveness["score"]
    )

    return {
        **result,
        "recognition": reconocimiento,
        "liveness": liveness
    }


