"""Router independiente: la integración proporciona su dependencia de usuario activo."""
from datetime import datetime
from typing import Literal,Annotated
from functools import lru_cache
from threading import Lock
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .predict import Predictor

class Observation(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    session_at: datetime
    estado: Literal['PRESENTE','TARDANZA','AUSENTE']
    nota: float|None=Field(default=None,ge=0,le=20)
    nota_disponible_at: datetime
    @model_validator(mode='after')
    def dates(self):
        if self.session_at.tzinfo or self.nota_disponible_at.tzinfo: raise ValueError('Usa fecha/hora local sin zona, según el dataset.')
        if self.nota_disponible_at<self.session_at: raise ValueError('La nota no puede publicarse antes de la sesión simulada.')
        return self

class PredictionInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    origen: Literal['sintetico']
    session_at: datetime
    history: Annotated[list[Observation],Field(min_length=1,max_length=1000)]
    @model_validator(mode='after')
    def chronology(self):
        if self.session_at.tzinfo: raise ValueError('Usa fecha/hora local sin zona.')
        if any(h.session_at>=self.session_at for h in self.history): raise ValueError('El historial debe ser estrictamente anterior al objetivo.')
        if len({h.session_at for h in self.history})!=len(self.history): raise ValueError('No se admiten sesiones duplicadas.')
        return self

class PredictionOutput(BaseModel):
    probabilidad: float=Field(ge=0,le=1)
    prediccion: Literal[0,1]
    umbral: float
    logistica_probabilidad: float=Field(ge=0,le=1)
    features: dict[str,float]
    origen: Literal['sintetico']
    advertencia: str

_predictor_lock=Lock()
_predictor_instance=None

@lru_cache(maxsize=1)
def get_predictor():
    global _predictor_instance
    with _predictor_lock:
        if _predictor_instance is None:_predictor_instance=Predictor()
        return _predictor_instance

def create_router(current_user):
    router=APIRouter(prefix='/api/parte6',tags=['Parte 6 · red neuronal'])
    def professor(user=Depends(current_user)):
        role=user.get('rol') if isinstance(user,dict) else user.rol
        if str(role).lower()!='profesor': raise HTTPException(403,'Solo el rol profesor puede consultar Parte 6.')
        return user
    def loaded():
        try: return get_predictor()
        except (FileNotFoundError,OSError): raise HTTPException(503,'Modelo no entrenado. Ejecuta python -m red_neuronal.train.')
    @router.get('/report',dependencies=[Depends(professor)])
    def report(): return loaded().report
    @router.post('/predict',response_model=PredictionOutput,dependencies=[Depends(professor)])
    def predict(payload: PredictionInput):
        try: return loaded().predict([h.model_dump() for h in payload.history],payload.session_at)
        except ValueError as e: raise HTTPException(422,str(e))
    return router
