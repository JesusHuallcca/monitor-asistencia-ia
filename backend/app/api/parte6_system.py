from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Path
from pydantic import BaseModel,ConfigDict,Field
from app.api.deps import get_current_user
from app.db.database import get_db
from app.services import parte6_service as service
from red_neuronal.inference import AttendanceInference

router=APIRouter(prefix='/api/parte6/system',tags=['Parte 6 — datos académicos'])
ID=Annotated[int,Path(gt=0)]

def professor(user=Depends(get_current_user)):
    if str(user.rol).lower()!='profesor':raise HTTPException(403,'Solo profesores autorizados.')
    return user

class Selection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    curso_id:int=Field(gt=0)
    estudiante_id:int=Field(gt=0)
    sesion_id:int=Field(gt=0)

@router.get('/courses')
def courses(user=Depends(professor),db=Depends(get_db)):return service.courses(db,user)
@router.get('/courses/{course}/students')
def students(course:ID,user=Depends(professor),db=Depends(get_db)):return service.students(db,user,course)
@router.get('/courses/{course}/sessions')
def sessions(course:ID,user=Depends(professor),db=Depends(get_db)):return service.sessions(db,user,course)
@router.post('/context')
def context(payload:Selection,user=Depends(professor),db=Depends(get_db)):
    return service.context(db,user,payload.curso_id,payload.estudiante_id,payload.sesion_id)
@router.post('/predict')
def predict(payload:Selection,user=Depends(professor),db=Depends(get_db)):
    result=service.context(db,user,payload.curso_id,payload.estudiante_id,payload.sesion_id)
    if not result['ready']:raise HTTPException(409,detail=dict(message='No se puede inferir con este historial.',blockers=result['blockers']))
    try:
        prediction=AttendanceInference().predict(result['features'],source='mysql_experimental',cutoff=result['cutoff'],session_at=result['session_at'])
    except (OSError,ValueError):raise HTTPException(503,'Artefactos ausentes o incompatibles. No se reentrena durante consultas.')
    result.update(prediction)
    return result
