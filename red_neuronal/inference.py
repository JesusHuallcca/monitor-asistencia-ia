"""Contrato INTERNO. No es un endpoint que acepte variables del navegador."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .prepare import FEATURES

class HistoricalInputs(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    asistencia_30d:float=Field(ge=0,le=1)
    tardanzas_30d:float=Field(ge=0,le=1)
    asistencia_ultimas5:float=Field(ge=0,le=1)
    sesiones_previas:int=Field(ge=5,le=1000,strict=True)
    promedio_previo:float=Field(ge=0,le=20)
    sin_notas:int=Field(ge=0,le=1,strict=True)
    dia_sin:float=Field(ge=-1,le=1)
    dia_cos:float=Field(ge=-1,le=1)
    hora:float=Field(ge=0,lt=24)
    @model_validator(mode='after')
    def consistency(self):
        import math
        if self.tardanzas_30d>self.asistencia_30d+1e-10:raise ValueError('Las tardanzas son parte de las asistencias.')
        if self.sin_notas and self.promedio_previo!=0:raise ValueError('Sin notas requiere promedio codificado en cero.')
        if not any(abs(self.dia_sin-math.sin(2*math.pi*d/7))<1e-5 and abs(self.dia_cos-math.cos(2*math.pi*d/7))<1e-5 for d in range(7)):raise ValueError('El seno y coseno deben corresponder al mismo día de semana.')
        return self

class InferenceContext(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source:Literal['sintetico','mysql_experimental']
    cutoff:datetime
    session_at:datetime
    @model_validator(mode='after')
    def chronology(self):
        if (self.cutoff.tzinfo is None)!=(self.session_at.tzinfo is None):raise ValueError('Usa una zona horaria consistente.')
        if self.cutoff>=self.session_at:raise ValueError('El corte debe ser anterior a la sesión objetivo.')
        return self

class AttendanceInference:
    def __init__(self,predictor=None):self._predictor=predictor
    def predict(self,values,*,source,cutoff,session_at):
        inputs=HistoricalInputs.model_validate(values)
        context=InferenceContext(source=source,cutoff=cutoff,session_at=session_at)
        import math
        angle=2*math.pi*context.session_at.weekday()/7
        if abs(inputs.dia_sin-math.sin(angle))>1e-5 or abs(inputs.dia_cos-math.cos(angle))>1e-5 or abs(inputs.hora-(context.session_at.hour+context.session_at.minute/60))>1e-6:raise ValueError('Día u hora no coinciden con la sesión objetivo.')
        if self._predictor is None:
            from .api import get_predictor
            self._predictor=get_predictor()
        ordered={name:getattr(inputs,name) for name in FEATURES}
        result=self._predictor.predict_features(ordered)
        return dict(result,**self._predictor.model_info(),source=context.source,cutoff=context.cutoff.isoformat(),session_at=context.session_at.isoformat(),experimental=True,validation_scope='Evaluación sintética; no validado con estudiantes reales.')
