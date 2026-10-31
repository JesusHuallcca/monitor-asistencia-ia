"""Contratos ML autenticados, reutilizando el ámbito, conversación y exportaciones."""
from dataclasses import replace
from datetime import datetime
import re
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from app.api.deps import get_current_user
from app.db.database import get_db
from app.core.config import TIMEZONE
from app.schemas.chatbot import ChatMessage
from app.services.chatbot_service import answer
from app.services.chatbot_conversation import prepare_turn, normalize
from app.services.chatbot_security import academic_scope, history_scope_key
from app.services import chatbot_ml as service, chatbot_report_store as storage
from app.services.chatbot_reports import preview

router=APIRouter(prefix="/ml",tags=["Chatbot · modelos de solo lectura"])
COLUMNS=[["model","Modelo"],["origin","Origen"],["version","Versión"],["metric","Indicador / estado"],["value","Valor"],["note","Alcance y limitaciones"]]

class MLQuery(BaseModel):
    model_config=ConfigDict(extra="forbid")
    model:Literal["kmeans","regresion_logistica","red_neuronal_parte6"]
    operation:Literal["explain","results","predict"]="results"
    course_id:int|None=Field(default=None,gt=0)
    student_id:int|None=Field(default=None,gt=0)


@router.get("/catalog")
def catalog(user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user)
    return service.evaluation_catalog()


@router.post("/query")
def query(body:MLQuery,user=Depends(get_current_user),db=Depends(get_db)):
    kind="ML_EXPLAIN" if body.operation=="explain" else {"kmeans":"ML_SEGMENTS","regresion_logistica":"ML_REGRESSION","red_neuronal_parte6":"ML_NEURAL"}[body.model]
    message={"kmeans":"K-Means","regresion_logistica":"regresión logística","red_neuronal_parte6":"red neuronal Parte 6"}[body.model]
    if body.operation=="results" and body.model!="kmeans":
        # Resultados significa evaluación, no inferencia implícita.
        selection={"course_id":body.course_id,"student_id":body.student_id}
        service.authorized_selection(db,user,selection)
        academic_scope(db,user)
        return service.regression_metadata() if body.model=="regresion_logistica" else service.neural_status()
    if body.operation=="predict" and body.model=="kmeans":
        from fastapi import HTTPException
        raise HTTPException(422,"K-Means agrupa; este contrato no predice asistencia ni ajusta nuevos clusters.")
    turn=prepare_turn(user,ChatMessage(message=message,course_id=body.course_id,student_id=body.student_id),history_scope_key(db,user))
    checked=answer(db,user,turn.body,turn=replace(turn,intent="HELP"))
    return service.ml_message(db,user,replace(turn,intent=kind),checked["_selection"])


def create_snapshot(db,user,selection):
    scope,_,_=service.authorized_selection(db,user,selection)
    storage.store.limiter.check(user.id,"preview",10)
    catalog=service.evaluation_catalog();rows=[]
    for model in catalog["models"]:
        for key,value in (model.get("metrics") or {"estado":None}).items():
            rows.append(dict(model=model["model"],origin=model["origin"],version=model["model_version"] or ("Modelo no disponible; reporte "+model["report_version"] if model.get("report_version") else "No disponible"),metric=key,value=value,note=model.get("limitations",model["reason"])))
    data=dict(kind="ml_evaluation",schema_version=1,title="Evaluación y comparación de modelos ML",source="Artefactos ML guardados, de solo lectura; origen indicado por modelo",synthetic=False,mode_label="Resultados sintéticos y origen no verificado, según modelo; sin inferencia individual",
        generated_at=datetime.now(ZoneInfo(TIMEZONE)).isoformat(),spec=dict(report_type="modelos-ml",course_id=selection.get("course_id"),student_id=selection.get("student_id")),
        courses=[],periods=["Evaluaciones archivadas; no se aplica un filtro de sesiones académicas"],metrics={},report_rows=len(rows),rows=rows,columns=COLUMNS,grades=[],comparison=[],comparison_delta_pp=None,chart=[],
        models=catalog["models"],comparable=False,winner=None,methodology=catalog["comparison_reason"]+" "+service.NOTICE+" Las métricas de regresión carecen de manifiesto de procedencia. No representan el rendimiento de los cursos seleccionados. No se reentrena ni se evalúa de nuevo ningún modelo.")
    key,entry=storage.store.add(user.id,history_scope_key(db,user),data)
    storage.audit("ml_preview_created",actor=user.id)
    return preview(key,entry,storage.store.clock())


@router.post("/reports")
def report(user=Depends(get_current_user),db=Depends(get_db)):
    return create_snapshot(db,user,{"course_id":None,"student_id":None})


def report_message(db,user,turn,selection):
    q=normalize(turn.body.message)
    formats=[fmt for pattern,fmt in [(r"excel|xlsx","xlsx"),(r"pdf|imprim","pdf"),(r"word|docx","docx")] if re.search(pattern,q)]
    changed=bool(turn.explicit_fields & {"course_id","student_id","period_start","period_end"})
    if turn.report_id and turn.previous_intent=="ML_REPORT" and not changed and not re.search(r"nuevo|actualiza|refresca",q):
        entry=storage.store.get(turn.report_id,user.id,history_scope_key(db,user))
        if entry.dataset().get("kind")=="ml_evaluation":value=preview(turn.report_id,entry,storage.store.clock())
        else:value=create_snapshot(db,user,selection)
    else:value=create_snapshot(db,user,selection)
    turn.report_id=value["id"]
    return dict(reply=value["title"]+". "+value["methodology"]+" Revisa la vista previa y descarga Excel, PDF o Word.",intent="ML_REPORT",data=[],provider="local",report=dict(value,requested_formats=formats))
