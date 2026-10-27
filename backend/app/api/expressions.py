from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, StrictBool
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.expression_consent import CONSENT_TEXT, CONSENT_VERSION, read_revision, set_consent
from app.services.expression_service import expression_service

router = APIRouter(prefix='/api/expressions', tags=['Expresiones estimadas'])
student = require_roles('estudiante')


class ConsentRequest(BaseModel):
    accepted: StrictBool
    text_version: str


@router.get('/consent')
def consent_status(response: Response, db: Session = Depends(get_db), user=Depends(student)):
    response.headers['Cache-Control'] = 'no-store'
    try:
        accepted = bool(read_revision(db, user.id))
    except Exception:
        raise HTTPException(503, 'Consentimiento no disponible; la asistencia sigue habilitada')
    return {'accepted': accepted, 'text_version': CONSENT_VERSION, 'text': CONSENT_TEXT,
            'enabled': expression_service.enabled}


@router.put('/consent')
def update_consent(data: ConsentRequest, response: Response,
                   db: Session = Depends(get_db), user=Depends(student)):
    response.headers['Cache-Control'] = 'no-store'
    if data.accepted and data.text_version != CONSENT_VERSION:
        raise HTTPException(409, 'Recarga el texto de consentimiento antes de aceptar')
    try:
        set_consent(db, user.id, data.accepted)
    except Exception:
        db.rollback()
        raise HTTPException(503, 'No se pudo actualizar el consentimiento')
    # Also discard jobs on re-acceptance: old revisions must never become valid again.
    expression_service.revoke(user.id)
    return {'accepted': data.accepted, 'text_version': CONSENT_VERSION}


@router.get('/jobs/{job_id}')
def result(job_id: str, response: Response, user=Depends(student), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    value = expression_service.get(user.id, job_id)
    if value is None:
        raise HTTPException(404, 'Resultado no disponible o caducado', headers={'Cache-Control': 'no-store'})
    if value.get('status') == 'READY' and not value.get('_guardado'):
        try:
            from app.db.emoscan_repository import registrar_historial_emocion
            registrar_historial_emocion(db, user.id, value, origen='asistencia')
            value['_guardado'] = True
        except Exception:
            db.rollback()
    return value

