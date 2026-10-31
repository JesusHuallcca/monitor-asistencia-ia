"""API interna de acciones y notificaciones; ninguna ruta de envío externo."""
import json
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select
from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.proactive_models import ProactiveAction as Action,ProactiveWorkerState as WorkerState
from app.schemas.chatbot_proactive import ActionSpec,Transition,Preferences,NotificationState
from app.services import chatbot_proactive as service,chatbot_report_store as storage
from app.services.chatbot_security import academic_scope,history_scope_key
from app.services.chatbot_reports import preview

router=APIRouter(prefix="/proactive",tags=["Chatbot · acciones revisables"])
class Edit(BaseModel):
    model_config=ConfigDict(extra="forbid")
    version:int=Field(gt=0)
    spec:ActionSpec

@router.get("/status")
def status(user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user)
    try:service.ready(db)
    except HTTPException:return {"available":False,"message":"Migración aditiva pendiente; no se aplicará automáticamente.","external_delivery":False}
    worker=db.get(WorkerState,"main")
    running=bool(worker and 0<=(service.utcnow()-worker.last_seen).total_seconds()<=120)
    return {"available":True,"worker_running":running,"worker_last_seen":service.stamp(worker.last_seen) if worker else None,"message":"Notificaciones internas; acciones con revisión y confirmación.","external_delivery":False}

@router.get("/sources")
def sources(user=Depends(get_current_user),db=Depends(get_db)):return service.sources(db,user)

@router.get("/students")
def students(course_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    scope=academic_scope(db,user)
    return [{"id":s.id,"name":first+" "+last} for s,first,last in db.execute(scope.students_query([course_id])).unique()]

@router.get("/preferences")
def preferences(user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user);service.ready(db)
    return service.preference(db,user)

@router.put("/preferences")
def set_preferences(body:Preferences,user=Depends(get_current_user),db=Depends(get_db)):
    result=service.set_preference(db,user,body);db.commit();return result

@router.get("/actions")
def actions(user=Depends(get_current_user),db=Depends(get_db)):
    service.ready(db);scope_key=history_scope_key(db,user)
    rows=db.scalars(select(Action).where(Action.owner_id==user.id).order_by(Action.created_at.desc()).limit(100)).all()
    return [service.view(db,user,a,scope_key) for a in rows]

@router.post("/actions")
def create(body:ActionSpec,user=Depends(get_current_user),db=Depends(get_db)):
    result=service.save_action(db,user,body);db.commit();return result

@router.put("/actions/{key}")
def edit(key:str,body:Edit,user=Depends(get_current_user),db=Depends(get_db)):
    service.ready(db);academic_scope(db,user)
    value=service.save_action(db,user,body.spec,service.owned(db,user,key,True),body.version);db.commit();return value

@router.post("/actions/{key}/transition")
def transition(key:str,body:Transition,user=Depends(get_current_user),db=Depends(get_db)):
    value=service.transition(db,user,key,body);db.commit();return value

@router.get("/notifications")
def notifications(user=Depends(get_current_user),db=Depends(get_db)):return service.inbox(db,user)

@router.get("/notifications/{key}")
def notification(key:str,user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user);service.ready(db)
    row=service.notification_owned(db,user,key)
    return {"id":row.id,"title":row.title,"message":row.message,"data":json.loads(row.data_json),"state":row.state}

@router.patch("/notifications/{key}")
def mark(key:str,body:NotificationState,user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user);service.ready(db)
    row=service.notification_owned(db,user,key);row.state=body.state
    service.audit(db,user.id,row.action_id,"notification_"+body.state);db.commit()
    return {"id":key,"state":body.state}

@router.post("/notifications/{key}/report")
def report(key:str,user=Depends(get_current_user),db=Depends(get_db)):
    academic_scope(db,user);service.ready(db)
    storage.store.limiter.check(user.id,"preview",10)
    row=service.notification_owned(db,user,key);data=json.loads(row.data_json)
    if "report" not in data:raise HTTPException(422,"Esta notificación no contiene un reporte.")
    scope_key=history_scope_key(db,user)
    report_id,entry=storage.store.add(user.id,scope_key,data["report"])
    service.audit(db,user.id,row.action_id,"report_opened");db.commit()
    return preview(report_id,entry,storage.store.clock())
