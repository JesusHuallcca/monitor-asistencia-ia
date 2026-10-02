import base64

import cv2
import numpy as np

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.face_service import face_service
from backend.app.services.liveness_service import liveness_service
from backend.app.db.face_repository import face_repository


router = APIRouter(
    prefix="/api/face",
    tags=["Face AI"]
)


class FrameRequest(BaseModel):
    image: str


class FaceRegistrationRequest(BaseModel):
    person_id: str
    image: str


class FaceDeactivateRequest(BaseModel):
    person_id: str


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
            raise ValueError(
                "No se pudo decodificar la imagen"
            )

        return frame

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Imagen inválida: {error}"
        )


@router.get("/health")
def face_health():
    return {
        "status": "ok",
        "module": "face-ai"
    }


@router.get("/registered")
def get_registered_faces():
    records = face_repository.find_all()

    return {
        "count": len(records),
        "faces": [
            {
                "person_id": record["person_id"]
            }
            for record in records
        ]
    }


@router.post("/detect")
def detect_face(request: FrameRequest):
    frame = decode_image(request.image)

    faces = face_service.detect(frame)

    return {
        "faces_detected": len(faces),
        "faces": [
            {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height)
            }
            for x, y, width, height in faces
        ]
    }


@router.post("/process")
def process_frame(request: FrameRequest):
    frame = decode_image(request.image)

    results = face_service.process_frame(frame)

    return {
        "faces_detected": len(results),
        "faces": results
    }


@router.post("/liveness")
def check_liveness(request: FrameRequest):
    frame = decode_image(request.image)

    result = liveness_service.check(frame)

    return result


@router.post("/register")
def register_face(request: FaceRegistrationRequest):
    person_id = request.person_id.strip()

    if not person_id:
        raise HTTPException(
            status_code=400,
            detail="person_id es obligatorio"
        )

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
            detail="Debe haber un solo rostro en la imagen"
        )

    face = face_service.extract_face(
        frame,
        faces[0]
    )

    if face.size == 0:
        raise HTTPException(
            status_code=400,
            detail="No se pudo extraer el rostro"
        )

    return face_service.register_face(
        person_id,
        face
    )


@router.post("/deactivate")
def deactivate_face(
    request: FaceDeactivateRequest
):
    person_id = request.person_id.strip()

    if not person_id:
        raise HTTPException(
            status_code=400,
            detail="person_id es obligatorio"
        )

    deactivated = face_repository.deactivate(
        person_id
    )

    if not deactivated:
        raise HTTPException(
            status_code=404,
            detail="Rostro no encontrado"
        )

    face_service.recognizer.known_faces.pop(
        person_id,
        None
    )

    return {
        "success": True,
        "person_id": person_id,
        "message": "Rostro desactivado correctamente"
    }

class MultiFaceRegistrationRequest(BaseModel):
    person_id: str
    images: list[str]


@router.post("/register/multiple")
def register_multiple_faces(
    request: MultiFaceRegistrationRequest
):
    from backend.app.services.face_registration_service import (
        face_registration_service
    )

    person_id = request.person_id.strip()

    if not person_id:
        raise HTTPException(
            status_code=400,
            detail="person_id es obligatorio"
        )

    if len(request.images) < 3:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 3 imágenes"
        )

    faces = []

    for image in request.images:
        frame = decode_image(image)

        detected_faces = face_service.detect(
            frame
        )

        if len(detected_faces) != 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cada imagen debe contener "
                    "exactamente un rostro"
                )
            )

        face = face_service.extract_face(
            frame,
            detected_faces[0]
        )

        if face.size == 0:
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer un rostro"
            )

        faces.append(face)

    embeddings = (
        face_registration_service.generate_samples(
            faces
        )
    )

    embedding = (
        face_registration_service.build_embedding(
            embeddings
        )
    )

    face_repository.save(
        person_id,
        embedding
    )

    face_service.recognizer.known_faces[
        person_id
    ] = embedding

    return {
        "success": True,
        "person_id": person_id,
        "samples": len(embeddings),
        "message": "Rostro registrado correctamente"
    }
@router.post("/camera/start")
def start_camera():
    from backend.app.services.camera_service import camera_service

    try:
        camera_service.start()

        return {
            "success": True,
            "message": "Cámara iniciada"
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.post("/camera/frame")
def camera_frame():
    from backend.app.services.camera_service import camera_service

    try:
        return camera_service.process_current_frame()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.post("/camera/stop")
def stop_camera():
    from backend.app.services.camera_service import camera_service

    camera_service.stop()

    return {
        "success": True,
        "message": "Cámara detenida"
    }