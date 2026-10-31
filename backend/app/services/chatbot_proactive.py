"""Acciones propias con revisión, permisos actuales, deduplicación y auditoría mínima."""
from collections import Counter
from datetime import datetime,time,timedelta,timezone
import hashlib
import json
import logging
import uuid
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import inspect,select,func,delete
from sqlalchemy.exc import IntegrityError
from app.core.config import TIMEZONE,DEMO_MODE
from app.db.models import Usuario,SesionClase,Evaluacion,Asistencia,Estudiante,Matricula
from app.db.proactive_models import ProactiveBase,ProactiveAction as Action,ProactiveNotification as Notification,ProactivePreference as Preference,ProactiveAudit as Audit,ProactiveWorkerState as WorkerState
from app.schemas.chatbot_proactive import ActionSpec
from app.schemas.chatbot_reports import ReportSpec
from app.services.chatbot_security import academic_scope,history_scope_key,deny
from app.services.chatbot_reports import build_dataset
from app.services.chatbot_report_store import audit as safe_log

UTC=timezone.utc
logger=logging.getLogger("monitor.chatbot.proactive")
TITLES={"next_class":"Recordatorio de clase","evaluation":"Recordatorio de evaluación","weekly_summary":"Resumen semanal de asistencia","absence_alert":"Aviso de ausencias acumuladas","tardy_alert":"Aviso de tardanzas acumuladas","scheduled_report":"Reporte programado disponible","tutoring":"Recordatorio de tutoría","meeting":"Recordatorio de reunión","communication":"Borrador de comunicación académica"}

def utcnow():return datetime.now(UTC).replace(tzinfo=None)
def encode(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(value):return hashlib.sha256(encode(value).encode()).hexdigest()
def stamp(value):return value.replace(tzinfo=UTC).isoformat() if value else None
def local_now(now,zone):return now.replace(tzinfo=UTC).astimezone(ZoneInfo(zone))
def utc_naive(value):return value.astimezone(UTC).replace(tzinfo=None)

def ready(db):
    names=set(inspect(db.get_bind()).get_table_names())
    if not set(ProactiveBase.metadata.tables)<=names:
        raise HTTPException(503,"Proactividad no habilitada: migración aditiva pendiente de revisión y aplicación en desarrollo.")

def audit(db,user_id,action_id,event,now=None):
    db.add(Audit(owner_id=user_id,action_id=action_id,event=event,created_at=now or utcnow()))
    safe_log("proactive_"+event,actor=user_id)

def preference(db,user):
    row=db.get(Preference,user.id)
    return {"enabled":row.enabled if row else True,"timezone":row.timezone if row else TIMEZONE,"recipient":"Mi cuenta","channel":"in_app"}

def set_preference(db,user,body):
    academic_scope(db,user);ready(db)
    row=db.get(Preference,user.id)
    if row is None:row=Preference(owner_id=user.id);db.add(row)
    row.enabled=body.enabled;row.timezone=body.timezone;row.updated_at=utcnow()
    audit(db,user.id,None,"preferences_changed")
    return preference(db,user)

def scope_for(db,user,spec):
    if user.estado!="activo":deny("proactive_inactive")
    scope=academic_scope(db,user)
    if spec.course_id is not None and spec.course_id not in scope.course_ids:deny("proactive_course")
    if spec.kind in {"scheduled_report","communication"} and str(user.rol).lower()!="profesor":deny("proactive_professor")
    student=spec.student_id or scope.own_student_id
    if student is not None:
        ids=[spec.course_id] if spec.course_id is not None else scope.course_ids
        if student not in {s.id for s,_,_ in db.execute(scope.students_query(ids)).unique()}:deny("proactive_student")
    return scope,student

def next_occurrence(spec,after):
    from apscheduler.triggers.cron import CronTrigger
    hour,minute=map(int,spec.local_time.split(":"))
    trigger=CronTrigger(hour=hour,minute=minute,second=0,day_of_week=spec.weekday if spec.frequency=="weekly" else "*",timezone=ZoneInfo(spec.timezone))
    candidate=trigger.get_next_fire_time(None,(after+timedelta(seconds=1)).replace(tzinfo=UTC))
    return utc_naive(candidate)

def source_info(db,user,spec,now):
    scope,student=scope_for(db,user,spec)
    now_local=local_now(now,TIMEZONE)
    if spec.kind=="next_class":
        row=db.get(SesionClase,spec.source_id)
        if row is None or row.curso_id!=spec.course_id or row.estado!="ACTIVA":raise HTTPException(409,"La clase ya no está disponible en ese curso.")
        event=datetime.combine(row.fecha,row.hora_inicio,tzinfo=ZoneInfo(TIMEZONE))
        if utc_naive(event)<=now:raise HTTPException(409,"La clase ya comenzó; selecciona otra fecha verificada.")
        source={"course":next(c.nombre for c in scope.courses if c.id==spec.course_id),"type":"sesiones_clase","id":row.id,"course_id":row.curso_id,"event_at":event.isoformat(),"description":"Fecha y hora verificadas en sesiones_clase."}
        return max(utc_naive(event)-timedelta(minutes=spec.reminder_minutes),now+timedelta(seconds=2)),source
    if spec.kind=="evaluation":
        row=db.get(Evaluacion,spec.source_id)
        if row is None or row.curso_id!=spec.course_id or row.fecha_vencimiento is None:raise HTTPException(409,"Evaluación sin vencimiento verificable en este curso.")
        if row.fecha_vencimiento<now_local.date():raise HTTPException(409,"El vencimiento ya pasó.")
        hour,minute=map(int,spec.local_time.split(":"))
        chosen=datetime.combine(row.fecha_vencimiento,time(hour,minute),tzinfo=ZoneInfo(spec.timezone))
        # Es una hora elegida de AVISO, no una hora de vencimiento inventada.
        source={"type":"evaluaciones","id":row.id,"course_id":row.curso_id,"date":row.fecha_vencimiento.isoformat(),"name":row.nombre,"description":"Solo fecha DATE verificada; sin hora de vencimiento. Hora de aviso elegida por el usuario."}
        return max(utc_naive(chosen),now+timedelta(seconds=2)),source
    if spec.kind in {"tutoring","meeting"}:
        if utc_naive(spec.event_at)<=now:raise HTTPException(422,"La fecha declarada debe ser futura.")
        return max(utc_naive(spec.event_at)-timedelta(minutes=spec.reminder_minutes),now+timedelta(seconds=2)),{"type":"usuario_confirmado","event_at":spec.event_at.isoformat(),"description":"Evento declarado por el usuario, no un evento verificado de MySQL."}
    if spec.kind=="communication":return None,{"type":"borrador","description":"Preparación local; no se envía a terceros."}
    return next_occurrence(spec,now),{"type":"registros_academicos","description":"Solo registros explícitos del ámbito autorizado; sin imputar ausencias."}

def identity(user,spec):
    values=spec.model_dump(mode="json")
    if spec.kind in {"next_class","evaluation"}:values={key:values[key] for key in ["kind","course_id","source_id"]}
    return digest({"owner":user.id,"spec":values})

def saved_spec(action):return ActionSpec.model_validate(json.loads(action.config_json)["spec"])

def view(db,user,action,scope_key=None):
    scope_key=scope_key or history_scope_key(db,user)
    valid=action.scope_key==scope_key
    return {"id":action.id,"kind":action.kind,"title":("Reporte programado" if action.kind=="scheduled_report" else TITLES[action.kind]) if valid else "Acción con permisos cambiados","status":action.status if valid else "blocked","version":action.version,
            "timezone":action.timezone,"frequency":action.frequency,"recipient":"Mi cuenta","channel":"in_app","next_run":stamp(action.next_run) if valid else None,
            "config":json.loads(action.config_json) if valid else None,"created_at":stamp(action.created_at),"external_delivery":False}

def owned(db,user,key,lock=False):
    query=select(Action).where(Action.id==key,Action.owner_id==user.id)
    if lock:query=query.with_for_update()
    row=db.scalar(query)
    if row is None:raise HTTPException(404,"Acción no disponible para esta cuenta.")
    return row

def communication_text(db,user,spec,now):
    today=local_now(now,TIMEZONE).date()
    data=build_dataset(db,user,ReportSpec(report_type="asistencia",course_id=spec.course_id,student_id=spec.student_id,period_start=today-timedelta(days=29),period_end=today))
    m=data["metrics"]
    intro=spec.text or "Propuesta para revisar el historial de asistencia y coordinar acompañamiento académico."
    return intro+"\nResumen verificado de los últimos 30 días: "+str(m["registros"])+" registros, "+str(m["tardanzas"])+" tardanzas y "+str(m["ausencias"])+" ausencias registradas. No se infieren faltas sin registro. Borrador para revisión; no enviado."

def save_action(db,user,spec,existing=None,version=None):
    ready(db);_,student=scope_for(db,user,spec)
    if student is not None:spec=spec.model_copy(update={"student_id":student})
    now=utcnow();due,source=source_info(db,user,spec,now)
    key=identity(user,spec)
    match=db.scalar(select(Action).where(Action.identity==key))
    if match is not None and (existing is None or existing.id!=match.id):
        if json.loads(match.config_json)["spec"]!=spec.model_dump(mode="json"):raise HTTPException(409,"Ya existe un recordatorio para ese evento. Edita la acción existente.")
        return view(db,user,match)
    scope_key=history_scope_key(db,user)
    config={"spec":spec.model_dump(mode="json"),"source":source,"source_fingerprint":digest(source)}
    if spec.kind=="communication":config["draft_text"]=communication_text(db,user,spec,now)
    if existing is None:
        if db.scalar(select(func.count()).select_from(Action).where(Action.owner_id==user.id,Action.status.notin_(["cancelled","completed","reviewed"])))>=40:raise HTTPException(429,"Máximo de 40 acciones pendientes por cuenta.")
        action=Action(id=str(uuid.uuid4()),owner_id=user.id,recipient_id=user.id,created_at=now,version=1)
        db.add(action)
    else:
        action=existing
        if action.version!=version:raise HTTPException(409,"La acción cambió. Actualiza la lista antes de editar.")
        if action.status in {"completed","reviewed","cancelled"}:raise HTTPException(409,"La acción está cerrada.")
        action.version+=1
    action.kind=spec.kind;action.course_id=spec.course_id;action.student_id=student;action.source_id=spec.source_id
    action.config_json=encode(config);action.timezone=spec.timezone;action.frequency=spec.frequency;action.next_run=due
    action.status="draft";action.scope_key=scope_key;action.identity=key;action.updated_at=now;action.last_signature=None
    try:db.flush()
    except IntegrityError:
        db.rollback();raise HTTPException(409,"La misma acción se creó simultáneamente; actualiza la lista.") from None
    audit(db,user.id,action.id,"draft_saved",now)
    return view(db,user,action)

def transition(db,user,key,body):
    ready(db);academic_scope(db,user)
    action=owned(db,user,key,True)
    if action.version!=body.version:raise HTTPException(409,"Versión de acción desactualizada.")
    if action.status in {"completed","cancelled","reviewed"}:raise HTTPException(409,"La acción está cerrada.")
    now=utcnow()
    if body.operation in {"activate","review"}:
        if not body.confirmed:raise HTTPException(422,"Revisa y confirma explícitamente esta acción.")
        spec=saved_spec(action);_,student=scope_for(db,user,spec);due,source=source_info(db,user,spec,now)
        if digest(source)!=json.loads(action.config_json)["source_fingerprint"]:raise HTTPException(409,"La fecha o fuente cambió; edita y revisa el recordatorio.")
        if body.operation=="review":
            if action.scope_key!=history_scope_key(db,user):raise HTTPException(409,"El ámbito cambió; regenera y revisa el borrador.")
            if action.kind!="communication":raise HTTPException(422,"Solo los borradores de comunicación se revisan con esta operación.")
            action.status="reviewed";action.next_run=None
        else:
            if action.kind=="communication":raise HTTPException(422,"Una comunicación solo puede aprobarse como borrador; no existe envío externo.")
            if not preference(db,user)["enabled"]:raise HTTPException(409,"Los recordatorios están desactivados. Actívalos en configuración primero.")
            action.status="active";action.next_run=due
        action.scope_key=history_scope_key(db,user)
    else:
        action.status={"pause":"paused","cancel":"cancelled","complete":"completed"}[body.operation]
        if body.operation!="pause":action.next_run=None
    action.version+=1;action.updated_at=now
    audit(db,user.id,action.id,body.operation,now)
    return view(db,user,action)

def sources(db,user):
    scope=academic_scope(db,user);now=utcnow();local=local_now(now,TIMEZONE)
    result={"classes":[],"evaluations":[],"manual_events":"Tutorías y reuniones no existen en el esquema; requieren datos y confirmación del usuario.","timezone":TIMEZONE}
    for row in db.scalars(select(SesionClase).where(SesionClase.curso_id.in_(scope.course_ids),SesionClase.estado=="ACTIVA",SesionClase.fecha>=local.date(),SesionClase.fecha<=local.date()+timedelta(days=90)).order_by(SesionClase.fecha,SesionClase.hora_inicio).limit(101)):
        event=datetime.combine(row.fecha,row.hora_inicio,tzinfo=ZoneInfo(TIMEZONE))
        if utc_naive(event)>now:result["classes"].append({"id":row.id,"course_id":row.curso_id,"event_at":event.isoformat()})
    for row in db.scalars(select(Evaluacion).where(Evaluacion.curso_id.in_(scope.course_ids),Evaluacion.fecha_vencimiento>=local.date(),Evaluacion.fecha_vencimiento<=local.date()+timedelta(days=90)).order_by(Evaluacion.fecha_vencimiento,Evaluacion.id).limit(100)):
        result["evaluations"].append({"id":row.id,"course_id":row.curso_id,"name":row.nombre,"date":row.fecha_vencimiento.isoformat(),"has_verified_time":False})
    return result

def closed_period(spec,now):
    today=local_now(now,TIMEZONE).date()
    if spec.frequency=="daily":return today-timedelta(days=1),today-timedelta(days=1)
    end=today-timedelta(days=today.weekday()+1)
    return end-timedelta(days=6),end

def alert_data(db,user,spec,now):
    scope,student=scope_for(db,user,spec)
    allowed={s.id for s,_,_ in db.execute(scope.students_query([spec.course_id])).unique()}
    if student is not None:allowed&={student}
    today=local_now(now,TIMEZONE).date();start=today-timedelta(days=spec.window_days-1)
    states=["AUSENTE"] if spec.kind=="absence_alert" else ["TARDE","TARDANZA"]
    rows=db.execute(select(Asistencia.id,Estudiante.id.label("student_id"),SesionClase.fecha,SesionClase.hora_fin).join(SesionClase,SesionClase.id==Asistencia.sesion_id).join(Estudiante,Estudiante.usuario_id==Asistencia.usuario_id).join(Matricula,(Matricula.estudiante_id==Estudiante.id)&(Matricula.curso_id==SesionClase.curso_id)).where(SesionClase.curso_id==spec.course_id,Estudiante.id.in_(allowed),Asistencia.estado.in_(states),SesionClase.estado!="CANCELADA",SesionClase.fecha>=start,SesionClase.fecha<=today,Asistencia.fecha==SesionClase.fecha).distinct().limit(2001)).all()
    if len(rows)>2000:raise HTTPException(413,"El aviso supera el volumen permitido.")
    rows=[r for r in rows if utc_naive(datetime.combine(r.fecha,r.hora_fin,tzinfo=ZoneInfo(TIMEZONE)))<now]
    counts=Counter(r.student_id for r in rows);triggered={sid:count for sid,count in counts.items() if count>=spec.threshold}
    signature=digest(sorted((r.id,r.student_id) for r in rows if r.student_id in triggered)) if triggered else None
    return {"counts":[{"student_id":sid,"count":count} for sid,count in sorted(triggered.items())],"threshold":spec.threshold,"window_days":spec.window_days,"from":start.isoformat(),"to":today.isoformat(),"methodology":"Solo ausencias o tardanzas explícitas; no se infieren faltas ni sanciones."},signature

def execution_data(db,user,action,spec,now):
    if spec.kind in {"next_class","evaluation","tutoring","meeting"}:
        _,source=source_info(db,user,spec,now)
        if digest(source)!=json.loads(action.config_json)["source_fingerprint"]:raise HTTPException(409,"Fuente modificada.")
        return {"source":source},None,TITLES[spec.kind]+". "+source["description"]
    if spec.kind in {"absence_alert","tardy_alert"}:
        data,signature=alert_data(db,user,spec,now)
        return data,signature,"Se alcanzó el umbral configurado en "+str(len(data["counts"]))+" perfiles del ámbito autorizado. Es un aviso revisable, sin decisiones automáticas."
    start,end=closed_period(spec,now)
    data=build_dataset(db,user,ReportSpec(report_type="asistencia",course_id=spec.course_id,student_id=spec.student_id,period_start=start,period_end=end))
    data["generated_at"]=stamp(now)
    return {"report":data},None,"Reporte de "+start.isoformat()+" a "+end.isoformat()+": "+str(data["report_rows"])+" registros. "+("Sin datos disponibles." if not data["report_rows"] else "Revisa la vista previa para descargarlo.")

def tick(sessions,now=None):
    """Efectos solo en la BD: notificación y avance en la MISMA transacción."""
    now=now or utcnow()
    counters={"processed":0,"notifications":0,"blocked":0,"errors":0}
    with sessions() as db:
        ready(db)
        if db.get_bind().dialect.name=="sqlite":
            from sqlalchemy.dialects.sqlite import insert
            db.execute(insert(WorkerState).values(id="main",last_seen=now).on_conflict_do_update(index_elements=["id"],set_={"last_seen":now}))
        elif db.get_bind().dialect.name=="mysql":
            from sqlalchemy.dialects.mysql import insert
            db.execute(insert(WorkerState).values(id="main",last_seen=now).on_duplicate_key_update(last_seen=now))
        else:raise RuntimeError("Motor no compatible con este worker.")
        db.execute(delete(Notification).where(Notification.expires_at<=now))
        db.execute(delete(Audit).where(Audit.created_at<now-timedelta(days=90)))
        db.commit()
        ids=list(db.scalars(select(Action.id).where(Action.status=="active",Action.next_run<=now).order_by(Action.next_run).limit(50)))
    for key in ids:
        with sessions() as db:
            try:
                action=db.scalar(select(Action).where(Action.id==key,Action.status=="active",Action.next_run<=now).with_for_update())
                if action is None:continue
                made=0
                user=db.get(Usuario,action.owner_id);scheduled=action.next_run
                if user is None or user.estado!="activo":raise HTTPException(403,"Usuario inactivo.")
                spec=saved_spec(action);scope_for(db,user,spec)
                if action.recipient_id!=user.id or history_scope_key(db,user)!=action.scope_key:raise HTTPException(403,"Ámbito cambiado.")
                if not preference(db,user)["enabled"]:
                    if spec.frequency=="once":action.status="paused"
                    else:action.next_run=next_occurrence(spec,now)
                    action.updated_at=now;action.version+=1;audit(db,user.id,action.id,"disabled_skip",now);db.commit();continue
                data,signature,message=execution_data(db,user,action,spec,now)
                if len(encode(data).encode())>2_000_000:raise HTTPException(413,"Resultado demasiado grande.")
                should_notify=spec.kind not in {"absence_alert","tardy_alert"} or (signature is not None and signature!=action.last_signature)
                if should_notify:
                    execution_key=digest({"action":action.id,"scheduled":stamp(scheduled)})
                    if not db.scalar(select(Notification.id).where(Notification.execution_key==execution_key)):
                        notification=Notification(id=str(uuid.uuid4()),action_id=action.id,owner_id=user.id,execution_key=execution_key,scheduled_for=scheduled,title=TITLES[spec.kind],message=message,data_json=encode(data),scope_key=action.scope_key,state="unread",created_at=now,expires_at=now+timedelta(days=30))
                        db.add(notification);db.flush()
                        made=1
                action.last_signature=signature;action.last_run=now;action.next_run=next_occurrence(spec,now) if spec.frequency!="once" else None
                action.status="active" if spec.frequency!="once" else "completed";action.updated_at=now;action.version+=1
                audit(db,user.id,action.id,"executed",now);db.commit();counters["processed"]+=1;counters["notifications"]+=made
            except IntegrityError:
                db.rollback() # Otro worker completó la misma ejecución; sin efecto externo.
            except HTTPException:
                db.rollback()
                action=db.get(Action,key)
                if action and action.status=="active":
                    action.status="blocked";action.next_run=None;action.version+=1;action.updated_at=now
                    audit(db,action.owner_id,key,"blocked",now);db.commit();counters["blocked"]+=1
            except Exception:
                db.rollback()
                logger.error("proactive_execution_failed code=internal_error") # Sin repr(exc), SQL, nombres o secretos.
                action=db.get(Action,key)
                if action and action.status=="active":
                    action.status="blocked";action.next_run=None;action.version+=1;action.updated_at=now
                    audit(db,action.owner_id,key,"execution_failed",now);db.commit()
                counters["errors"]+=1
    return counters

def notification_owned(db,user,key):
    value=db.scalar(select(Notification).where(Notification.id==key,Notification.owner_id==user.id,Notification.expires_at>utcnow()))
    if value is None:raise HTTPException(404,"Notificación no disponible para esta cuenta o vencida.")
    action=owned(db,user,value.action_id)
    scope_for(db,user,saved_spec(action))
    if value.scope_key!=history_scope_key(db,user):deny("proactive_notification_scope_changed")
    return value

def inbox(db,user):
    current=history_scope_key(db,user);ready(db)
    values=db.scalars(select(Notification).where(Notification.owner_id==user.id,Notification.expires_at>utcnow(),Notification.scope_key==current).order_by(Notification.created_at.desc()).limit(100)).all()
    return [{"id":n.id,"title":n.title,"message":n.message,"state":n.state,"created_at":stamp(n.created_at),"expires_at":stamp(n.expires_at),"has_report":"report" in json.loads(n.data_json),"source":json.loads(n.data_json).get("source")} for n in values]

def proactive_message(db,user,turn,selection):
    academic_scope(db,user)
    data=sources(db,user)
    reply="Puedes revisar y activar recordatorios en el Centro de notificaciones del dashboard. "
    reply+=str(len(data["classes"]))+" clases próximas y "+str(len(data["evaluations"]))+" evaluaciones con fecha disponibles en tu ámbito. "
    reply+="No activo acciones por interpretar una frase: primero revisa fecha, zona horaria, frecuencia y destinatario. Tutorías y reuniones requieren una fecha declarada por ti. Las comunicaciones permanecen como borradores, sin envío."
    return {"reply":reply,"intent":"PROACTIVE","provider":"local","data":[],"proactive":{"open_center":True,"sources":data}}
