"""Análisis voluntario independiente de la asistencia. Fotografías solo en RAM."""
import io

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, StrictBool
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.personal_expression_consent import TEXT, VERSION, read_revision, set_consent
from app.services.emoscan_personal_service import personal_service

router = APIRouter(prefix='/api/emoscan-personal', tags=['EmoScan personal'])
student = require_roles('estudiante')
MAX_IMAGE_BYTES = 300 * 1024


class ConsentRequest(BaseModel):
    accepted: StrictBool
    text_version: str


@router.get('/consent')
def consent(response: Response, user=Depends(student), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    try:
        accepted = bool(read_revision(db, user.id))
    except Exception:
        raise HTTPException(503, 'Consentimiento personal no disponible. La asistencia no se ve afectada.')
    return {'accepted': accepted, 'text_version': VERSION, 'text': TEXT, 'enabled': personal_service.enabled}


@router.put('/consent')
def update(data: ConsentRequest, response: Response, user=Depends(student), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    if data.accepted and data.text_version != VERSION:
        raise HTTPException(409, 'Recarga el texto de consentimiento antes de aceptar.')
    try:
        set_consent(db, user.id, data.accepted)
    except Exception:
        db.rollback()
        raise HTTPException(503, 'No se pudo confirmar el cambio. Puedes volver a retirar el consentimiento.')
    personal_service.revoke(user.id)
    return {'accepted': data.accepted, 'text_version': VERSION}


def decode_and_submit(owner, data):
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            if image.format != 'JPEG' or not (100 <= width <= 1280 and 100 <= height <= 1280):
                raise ValueError('Usa un JPEG de entre 100 y 1280 píxeles por lado.')
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as error:
        raise ValueError('La captura JPEG no es válida.') from error
    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError('No se pudo decodificar la captura JPEG.')
    return personal_service.submit(owner, frame)


@router.post('/analizar', status_code=202)
async def analyze(request: Request, response: Response, user=Depends(student), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    if not personal_service.enabled:
        raise HTTPException(503, 'EmoScan está desactivado. La asistencia sigue disponible.')
    try:
        revision = read_revision(db, user.id)
    except Exception:
        raise HTTPException(503, 'No se pudo verificar el consentimiento personal.')
    if not revision:
        raise HTTPException(403, 'Se requiere tu consentimiento personal antes de analizar.')
    if request.headers.get('content-type', '').split(';')[0].lower() != 'image/jpeg':
        raise HTTPException(415, 'Envía una captura JPEG.')
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_IMAGE_BYTES:
            raise HTTPException(413, 'La captura supera 300 KiB.')
        content.extend(chunk)
    try:
        result = await run_in_threadpool(decode_and_submit, user.id, bytes(content))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except Exception:
        raise HTTPException(503, 'EmoScan no está disponible. Puedes volver a intentarlo.')
    statuses = {'NO_CONSENT': 403, 'DISABLED': 503, 'UNAVAILABLE': 503, 'BUSY': 429}
    if result['status'] != 'QUEUED':
        raise HTTPException(statuses.get(result['status'], 503), 'Análisis no disponible: ' + result['status'])
    return result


from app.db.emoscan_repository import (
    obtener_historial_por_estudiante,
    obtener_historial_por_usuario,
    obtener_resumen_emocional_estudiante,
    registrar_historial_emocion,
)

docente_o_admin = require_roles('profesor', 'administrador')


@router.get('/jobs/{job_id}')
def result(job_id: str, response: Response, user=Depends(student), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    value = personal_service.get(user.id, job_id)
    if value is None:
        raise HTTPException(404, 'Resultado no disponible o caducado.', headers={'Cache-Control': 'no-store'})

    # Persistir en MySQL el resultado según estudiante_id/usuario_id
    if value.get('status') == 'READY' and not value.get('_guardado'):
        try:
            registrar_historial_emocion(db, user.id, value, origen='personal')
            value['_guardado'] = True
        except Exception:
            db.rollback()

    return value


@router.get('/historial')
def mi_historial(user=Depends(student), db: Session = Depends(get_db), limit: int = 50):
    """Devuelve el historial de emociones del propio estudiante autenticado."""
    registros = obtener_historial_por_usuario(db, user.id, limit=limit)
    return [
        {
            "id": r.id,
            "emocion": r.emocion_predominante,
            "confianza": float(r.confianza) if r.confianza is not None else None,
            "origen": r.origen,
            "fecha": r.fecha_registro.isoformat() if r.fecha_registro else None,
        }
        for r in registros
    ]


@router.get('/estudiante/{estudiante_id}/historial')
def historial_estudiante(
    estudiante_id: int,
    user=Depends(docente_o_admin),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Permite a profesores o administradores verificar el historial emocional según estudiante_id."""
    registros = obtener_historial_por_estudiante(db, estudiante_id, limit=limit)
    return [
        {
            "id": r.id,
            "estudiante_id": r.estudiante_id,
            "usuario_id": r.usuario_id,
            "emocion": r.emocion_predominante,
            "confianza": float(r.confianza) if r.confianza is not None else None,
            "origen": r.origen,
            "sesion_id": r.sesion_id,
            "fecha": r.fecha_registro.isoformat() if r.fecha_registro else None,
        }
        for r in registros
    ]


@router.get('/estudiante/{estudiante_id}/resumen')
def resumen_estudiante(
    estudiante_id: int,
    user=Depends(docente_o_admin),
    db: Session = Depends(get_db),
):
    """Devuelve la distribución agregada de emociones de un estudiante para el profesor."""
    return obtener_resumen_emocional_estudiante(db, estudiante_id)


@router.delete('/jobs', status_code=204)
def clear(response: Response, user=Depends(student)):
    response.headers['Cache-Control'] = 'no-store'
    personal_service.revoke(user.id)

