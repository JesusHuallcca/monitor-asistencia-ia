import base64
from datetime import date, datetime

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import Asistencia, SesionClase, Usuario
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
    user: Usuario = Depends(
        require_roles(
            "admin",
            "superadmin",
            "profesor"
        )
    )
):
    attendances = attendance_service.get_all(db)

    return {
        "count": len(attendances),
        "attendances": attendances
    }


@router.get("/my-course/{curso_id}")
def get_my_course_attendance(
    curso_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    return attendance_service.get_my_course_attendance(
        db=db,
        usuario_id=user.id,
        curso_id=curso_id
    )


@router.get("/current-session-status")
def get_current_session_status(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    ahora = datetime.now()
    hoy = date.today()

    sesion = (
        db.query(SesionClase)
        .filter(
            SesionClase.fecha == hoy,
            SesionClase.estado == "ACTIVA",
            SesionClase.hora_inicio <= ahora.time(),
            SesionClase.hora_fin >= ahora.time()
        )
        .order_by(
            SesionClase.hora_inicio.asc()
        )
        .first()
    )

    if sesion is None:
        return {
            "sesion_activa": False,
            "ya_registrada": False,
            "sesion": None
        }

    asistencia = (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == user.id,
            Asistencia.sesion_id == sesion.id
        )
        .first()
    )

    estudiante = (
        f"{user.nombres} {user.apellidos}"
    )

    if asistencia is not None:

        if asistencia.estado == "PRESENTE":
            calificacion = 100
        elif asistencia.estado == "TARDANZA":
            calificacion = 50
        else:
            calificacion = 0

        return {
            "sesion_activa": True,
            "ya_registrada": True,
            "sesion": {
                "id": sesion.id,
                "curso_id": sesion.curso_id,
                "fecha": sesion.fecha.isoformat(),
                "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
                "hora_fin": sesion.hora_fin.strftime("%H:%M"),
                "tolerancia_minutos": (
                    sesion.tolerancia_minutos
                )
            },
            "asistencia": {
                "id": asistencia.id,
                "fecha": str(asistencia.fecha),
                "hora": str(asistencia.hora),
                "estado": asistencia.estado,
                "calificacion": calificacion
            },
            "estudiante": estudiante
        }

    return {
        "sesion_activa": True,
        "ya_registrada": False,
        "sesion": {
            "id": sesion.id,
            "curso_id": sesion.curso_id,
            "fecha": sesion.fecha.isoformat(),
            "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
            "hora_fin": sesion.hora_fin.strftime("%H:%M"),
            "tolerancia_minutos": (
                sesion.tolerancia_minutos
            )
        },
        "estudiante": estudiante
    }


@router.get("/session/{curso_id}")
def get_course_session(
    curso_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    ahora = datetime.now()
    hoy = date.today()

    sesion = (
        db.query(SesionClase)
        .filter(
            SesionClase.curso_id == curso_id,
            SesionClase.fecha == hoy,
            SesionClase.estado == "ACTIVA"
        )
        .order_by(
            SesionClase.hora_inicio.asc()
        )
        .first()
    )

    if sesion is None:
        return {
            "activa": False,
            "sesion": None
        }

    hora_actual = ahora.time()

    dentro_horario = (
        sesion.hora_inicio
        <= hora_actual
        < sesion.hora_fin
    )

    return {
        "activa": dentro_horario,
        "sesion": {
            "id": sesion.id,
            "curso_id": sesion.curso_id,
            "fecha": sesion.fecha.isoformat(),
            "hora_inicio": sesion.hora_inicio.strftime("%H:%M"),
            "hora_fin": sesion.hora_fin.strftime("%H:%M"),
            "tolerancia_minutos": (
                sesion.tolerancia_minutos
            ),
            "estado": sesion.estado
        }
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
            "message": (
                "El rostro no coincide "
                "con el usuario autenticado"
            )
        }

    liveness = liveness_service.check(frame)

    if not liveness["is_live"]:
        return {
            "success": False,
            "status": "LIVENESS_FAILED",
            "message": (
                "No se pudo validar que el rostro "
                "corresponda a una persona presente"
            ),
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
        "message": (
            "Las asistencias ahora se almacenan "
            "en MySQL y no se eliminan desde este endpoint"
        )
    }


@router.post("/camera/reset")
def reset_attendance_camera(
    user: Usuario = Depends(get_current_user)
):
    from app.services.attendance_camera_service import (
        attendance_camera_service
    )

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
            "message": (
                "El rostro no coincide "
                "con el usuario autenticado"
            )
        }

    liveness = liveness_service.check(frame)

    if not liveness["is_live"]:
        return {
            "success": False,
            "status": "LIVENESS_FAILED",
            "message": (
                "No se pudo validar que el rostro "
                "corresponda a una persona presente"
            ),
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