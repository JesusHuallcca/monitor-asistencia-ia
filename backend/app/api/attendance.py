from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.attendance_service import attendance_service
from backend.app.services.face_service import face_service
from backend.app.services.liveness_service import liveness_service
from backend.app.services.attendance_camera_service import attendance_camera_service
from backend.app.api.face import decode_image


router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance AI"]
)


class AttendanceRequest(BaseModel):
    image: str


@router.get("/health")
def attendance_health():
    return {
        "status": "ok",
        "module": "attendance-ai"
    }


@router.get("/")
def get_attendances():
    return {
        "count": len(attendance_service.get_all()),
        "attendances": attendance_service.get_all()
    }


@router.post("/check-in")
def check_in(request: AttendanceRequest):
    frame = decode_image(request.image)

    faces = face_service.detect(frame)

    if len(faces) == 0:
        raise HTTPException(
            status_code=400,
            detail="No se detectó ningún rostro"
        )

    if len(faces) > 1:
        raise HTTPException(
            status_code=400,
            detail="Debe haber un solo rostro para registrar asistencia"
        )

    detected_face = faces[0]

    face_image = face_service.extract_face(
        frame,
        detected_face
    )

    if face_image.size == 0:
        raise HTTPException(
            status_code=400,
            detail="No se pudo extraer el rostro"
        )

    recognition = face_service.recognize(face_image)

    if recognition is None:
        return {
            "success": False,
            "status": "UNKNOWN_FACE",
            "message": "Rostro no reconocido"
        }

    liveness = liveness_service.check(frame)

    if not liveness["is_live"]:
        return {
            "success": False,
            "status": "LIVENESS_FAILED",
            "message": "No se pudo validar que el rostro corresponda a una persona presente",
            "person_id": recognition["person_id"],
            "confidence": recognition["confidence"],
            "liveness": liveness
        }

    result = attendance_service.register(
        person_id=recognition["person_id"],
        confidence=recognition["confidence"],
        liveness_score=liveness["score"]
    )

    return {
        **result,
        "recognition": recognition,
        "liveness": liveness
    }


@router.delete("/")
def clear_attendances():
    attendance_service.clear()

    return {
        "success": True,
        "message": "Asistencias temporales eliminadas"
    }


@router.post("/camera/reset")
def reset_attendance_camera():
    attendance_camera_service.reset()

    return {
        "success": True,
        "message": "Sesión de cámara reiniciada"
    }


@router.post("/camera/check-in")
def camera_check_in(request: AttendanceRequest):
    frame = decode_image(request.image)

    try:
        return attendance_camera_service.process_frame(frame)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )