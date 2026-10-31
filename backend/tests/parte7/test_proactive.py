"""Proactividad: SQLite aislado, reloj controlado y worker real, sin envíos."""
from datetime import datetime,date,time,timedelta,timezone
from threading import Event,Barrier
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import pytest
from sqlalchemy import select,func,create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import SesionClase,Asistencia,Evaluacion,AsignacionProfesor,Usuario,Matricula
from app.db.proactive_models import ProactiveBase,ProactiveAction as Action,ProactiveNotification as Notification,ProactiveAudit as Audit
from app.services import chatbot_proactive as svc,chatbot_report_store as storage
from app.services.chatbot_proactive_scheduler import make_scheduler

ROOT=Path(__file__).resolve().parents[3]
NOW=datetime(2026,11,2,13) # lunes 08:00 America/Lima

@pytest.fixture
def proactive(harness,monkeypatch):
    client,sessions,headers=harness
    with sessions() as db:
        ProactiveBase.metadata.create_all(db.get_bind())
        for sid in (1,2):
            row=db.get(SesionClase,sid);row.fecha=date(2026,10,28)
        for aid in (1,2,3,4):db.get(Asistencia,aid).fecha=date(2026,10,28)
        db.get(SesionClase,4).fecha=date(2026,11,3)
        db.get(SesionClase,3).fecha=date(2026,11,3)
        db.get(Evaluacion,1).fecha_vencimiento=date(2026,11,4)
        db.get(Evaluacion,2).fecha_vencimiento=date(2026,11,5)
        db.commit()
    clock=[NOW];monkeypatch.setattr(svc,"utcnow",lambda:clock[0])
    store=storage.ReportStore();monkeypatch.setattr(storage,"store",store)
    yield harness,clock
    store.close()

def create(h,uid=2,**kw):
    c,_,headers=h
    return c.post("/api/chatbot/proactive/actions",headers=headers(uid),json={"kind":"next_class","course_id":1,"source_id":4,**kw})

def change(h,action,operation="activate",uid=2,confirmed=True):
    c,_,headers=h
    return c.post("/api/chatbot/proactive/actions/"+action["id"]+"/transition",headers=headers(uid),json={"version":action["version"],"operation":operation,"confirmed":confirmed})

def inbox(h,uid=2):
    c,_,headers=h
    return c.get("/api/chatbot/proactive/notifications",headers=headers(uid))

def activate(proactive,**kw):
    h,_=proactive;response=create(h,**kw);assert response.status_code==200,response.text
    value=change(h,response.json(),uid=kw.get("uid",2));assert value.status_code==200,value.text
    return value.json()

def run_due(proactive,action):
    h,clock=proactive
    clock[0]=datetime.fromisoformat(action["next_run"]).replace(tzinfo=None)+timedelta(seconds=1)
    return svc.tick(h[1])

def weekly(proactive,**kw):
    return activate(proactive,kind="scheduled_report",source_id=None,frequency="weekly",local_time="08:01",weekday=0,**kw)

def test_no_automatic_schema_migration(harness):
    c,_,headers=harness
    assert not set(ProactiveBase.metadata.tables)&set(Base.metadata.tables)
    assert c.get("/api/chatbot/proactive/status",headers=headers(2)).json()["available"] is False
    assert create(harness).status_code==503
    sql=(ROOT/"database/mysql/migrations/parte7/001_proactividad_additive.sql").read_text(encoding="utf-8")
    commands=[line.strip().split()[0].upper() for line in sql.splitlines() if line.strip() and not line.startswith("--")]
    assert "CREATE" in commands and not {"DROP","ALTER","DELETE","UPDATE","INSERT"}&set(commands)

@pytest.mark.parametrize("method,path,body",[
 ("get","/status",None),("get","/sources",None),("get","/actions",None),("get","/preferences",None),("get","/notifications",None),
 ("post","/actions",{"kind":"next_class","course_id":1,"source_id":4}),("put","/preferences",{"enabled":False}),
 ("post","/actions/fake/transition",{"version":1,"operation":"activate","confirmed":True}),("get","/notifications/fake",None),("post","/notifications/fake/report",None),("patch","/notifications/fake",{"state":"read"})])
def test_all_endpoints_require_auth(proactive,method,path,body):
    h,_=proactive;assert h[0].request(method,"/api/chatbot/proactive"+path,json=body).status_code==401

@pytest.mark.parametrize("uid,values",[(2,{"course_id":2}),(2,{"student_id":3}),(3,{"student_id":2}),(3,{"course_id":2,"source_id":4}),(6,{}),(8,{}),(1,{}),(9,{})])
def test_scopes_and_source_binding(proactive,uid,values):
    h,_=proactive
    assert create(h,uid,**values).status_code in {403,409}

@pytest.mark.parametrize("values",[
 {"recipient_id":5},{"channel":"email"},{"callback":"os.system"},{"sql":"SELECT *"},{"timezone":"Invalid/Zone"},{"frequency":"hourly"},{"threshold":0},{"threshold":101},{"local_time":"25:99"},{"source_id":99999},{"event_at":"2026-11-04T09:00:00-05:00"}])
def test_closed_action_contract(proactive,values):
    h,_=proactive
    assert create(h,**values).status_code in {422,409}

def test_sources_are_verified_and_scoped(proactive):
    h,_=proactive;c,_,hdr=h
    value=c.get("/api/chatbot/proactive/sources",headers=hdr(2)).json()
    assert [r["id"] for r in value["classes"]]==[4]
    assert [r["id"] for r in value["evaluations"]]==[1]
    assert value["evaluations"][0]["has_verified_time"] is False
    assert "no existen" in value["manual_events"]
    assert c.get("/api/chatbot/proactive/students?course_id=2",headers=hdr(2)).status_code==403

def test_draft_review_confirmation_and_idempotency(proactive):
    h,_=proactive
    a=create(h).json();b=create(h).json()
    assert a["id"]==b["id"] and a["status"]=="draft" and a["recipient"]=="Mi cuenta"
    assert svc.tick(h[1])["notifications"]==0
    assert change(h,a,confirmed=False).status_code==422
    assert change(h,a,uid=3).status_code==404
    active=change(h,a);assert active.status_code==200
    assert change(h,a).status_code==409 # revisión obsoleta
    assert create(h,reminder_minutes=15).status_code==409 # editar en lugar de duplicar evento
    assert len(h[0].get("/api/chatbot/proactive/actions",headers=h[2](2)).json())==1

def test_class_reminder_worker_and_no_duplicate(proactive):
    a=activate(proactive);h,_=proactive
    result=run_due(proactive,a)
    assert result["notifications"]==1
    values=inbox(h).json();assert len(values)==1
    assert values[0]["source"]["type"]=="sesiones_clase" and values[0]["source"]["event_at"].startswith("2026-11-03")
    assert svc.tick(h[1])["notifications"]==0
    assert inbox(h,3).json()==[]
    assert change(h,a,uid=3).status_code==404

def test_evaluation_has_date_not_fabricated_deadline_hour(proactive):
    a=activate(proactive,kind="evaluation",source_id=1,local_time="07:00")
    h,_=proactive;run_due(proactive,a)
    source=inbox(h).json()[0]["source"]
    assert source["date"]=="2026-11-04" and "event_at" not in source
    assert "sin hora de vencimiento" in source["description"].lower()
    with h[1]() as db:db.get(Evaluacion,1).fecha_vencimiento=None;db.commit()
    assert create(h,kind="evaluation",source_id=1).status_code==409

@pytest.mark.parametrize("mutation",["cancel","change_date","revoke","inactive"])
def test_revalidation_before_execution(proactive,mutation):
    a=activate(proactive);h,_=proactive
    with h[1]() as db:
        if mutation=="cancel":db.get(SesionClase,4).estado="CANCELADA"
        if mutation=="change_date":db.get(SesionClase,4).fecha=date(2026,11,4)
        if mutation=="revoke":db.delete(db.scalar(select(AsignacionProfesor)))
        if mutation=="inactive":db.get(Usuario,2).estado="inactivo"
        db.commit()
    result=run_due(proactive,a)
    assert result["notifications"]==0 and result["blocked"]==1
    with h[1]() as db:assert db.scalar(select(func.count()).select_from(Notification))==0

def test_master_disable_pause_and_resume(proactive):
    a=activate(proactive);h,_=proactive;c,_,hdr=h
    assert c.put("/api/chatbot/proactive/preferences",headers=hdr(2),json={"enabled":False,"timezone":"America/Lima"}).status_code==200
    assert run_due(proactive,a)["notifications"]==0
    paused=c.get("/api/chatbot/proactive/actions",headers=hdr(2)).json()[0]
    assert paused["status"]=="paused"
    assert change(h,paused).status_code==409
    assert c.put("/api/chatbot/proactive/preferences",headers=hdr(2),json={"enabled":True,"timezone":"America/Lima"}).status_code==200
    assert change(h,paused).status_code==200

def test_edit_requires_revision_and_new_confirmation(proactive):
    a=create(proactive[0]).json();h,_=proactive;c,_,hdr=h
    body={"version":a["version"],"spec":{**a["config"]["spec"],"reminder_minutes":10}}
    revised=c.put("/api/chatbot/proactive/actions/"+a["id"],headers=hdr(2),json=body)
    assert revised.status_code==200 and revised.json()["status"]=="draft"
    assert revised.json()["version"]==a["version"]+1
    assert c.put("/api/chatbot/proactive/actions/"+a["id"],headers=hdr(2),json=body).status_code==409

def test_weekly_report_real_counts_download_and_scope_revocation(proactive):
    a=weekly(proactive);h,_=proactive;c,_,hdr=h
    assert run_due(proactive,a)["notifications"]==1
    n=inbox(h).json()[0];assert n["has_report"]
    result=c.post("/api/chatbot/proactive/notifications/"+n["id"]+"/report",headers=hdr(2))
    assert result.status_code==200,result.text
    value=result.json()
    assert value["report_rows"]==2 and value["metrics"]["asistencia_pct"]==50
    assert value["spec"]["period_start"]=="2026-10-26" and value["spec"]["period_end"]=="2026-11-01"
    assert c.post("/api/chatbot/proactive/notifications/"+n["id"]+"/report",headers=hdr(3)).status_code==404
    exported=c.post("/api/chatbot/reports/"+value["id"]+"/exports/pdf",headers=hdr(2));assert exported.status_code==200
    assert c.get(exported.json()["url"],headers=hdr(2)).content.startswith(b"%PDF")
    with h[1]() as db:db.delete(db.scalar(select(AsignacionProfesor)));db.commit()
    assert inbox(h).json()==[]
    assert c.get("/api/chatbot/proactive/notifications/"+n["id"],headers=hdr(2)).status_code==403
    assert c.get(exported.json()["url"],headers=hdr(2)).status_code==403

def test_student_summary_only_own_records(proactive):
    a=activate(proactive,uid=3,kind="weekly_summary",source_id=None,frequency="weekly",local_time="08:01")
    h,_=proactive;run_due(proactive,a)
    n=inbox(h,3).json()[0]
    value=h[0].post("/api/chatbot/proactive/notifications/"+n["id"]+"/report",headers=h[2](3)).json()
    assert value["report_rows"]==1 and value["metrics"]["asistencia_pct"]==100
    assert all(row["estudiante"].startswith("Ana") for row in value["rows"])
    assert create(h,uid=3,kind="scheduled_report",source_id=None,frequency="weekly").status_code==403

@pytest.mark.parametrize("kind",["absence_alert","tardy_alert"])
def test_alert_threshold_and_dedup_unchanged_condition(proactive,kind):
    h,clock=proactive
    if kind=="tardy_alert":
        with h[1]() as db:db.get(Asistencia,2).estado="TARDE";db.commit()
    a=activate(proactive,kind=kind,source_id=None,frequency="daily",threshold=1,local_time="08:01")
    assert run_due(proactive,a)["notifications"]==1
    clock[0]+=timedelta(days=1)
    assert svc.tick(h[1])["notifications"]==0
    assert len(inbox(h).json())==1
    n=inbox(h).json()[0]
    content=h[0].get("/api/chatbot/proactive/notifications/"+n["id"],headers=h[2](2)).json()["data"]
    assert content["counts"]==[{"student_id":2,"count":1}]

def test_no_absence_inference_when_records_missing(proactive):
    a=activate(proactive,kind="absence_alert",source_id=None,frequency="daily",threshold=2,local_time="08:01")
    assert run_due(proactive,a)["notifications"]==0

@pytest.mark.parametrize("kind",["tutoring","meeting"])
def test_manual_events_are_explicit_not_mysql_verified(proactive,kind):
    h,_=proactive
    a=activate(proactive,kind=kind,source_id=None,course_id=None,event_at="2026-11-03T12:00:00-05:00",title="Seguimiento sintético")
    assert a["config"]["source"]["type"]=="usuario_confirmado"
    run_due(proactive,a)
    assert inbox(h).json()[0]["source"]["type"]=="usuario_confirmado"

def test_communications_reviewed_but_never_sent(proactive):
    h,clock=proactive
    draft=create(h,kind="communication",source_id=None,text="Propuesta sintética de tutoría.").json()
    assert draft["status"]=="draft" and draft["next_run"] is None
    assert "no enviado" in draft["config"]["draft_text"].lower()
    assert change(h,draft).status_code==422
    reviewed=change(h,draft,operation="review")
    assert reviewed.status_code==200 and reviewed.json()["status"]=="reviewed"
    clock[0]+=timedelta(days=30);assert svc.tick(h[1])["notifications"]==0
    assert reviewed.json()["external_delivery"] is False

def test_conversation_offers_only_no_action_created(proactive):
    h,_=proactive
    for q in ["Recuérdame mi próxima clase","Programa un reporte semanal","Alerta de ausencias acumuladas","Recordatorio de tutoría"]:
        value=h[0].post("/api/chatbot/message",headers=h[2](2),json={"message":q})
        assert value.status_code==200 and value.json()["intent"]=="PROACTIVE"
    with h[1]() as db:assert db.scalar(select(func.count()).select_from(Action))==0

def test_background_scheduler_without_browser(proactive):
    a=weekly(proactive);h,clock=proactive
    clock[0]=datetime.fromisoformat(a["next_run"]).replace(tzinfo=None)+timedelta(seconds=1)
    executed=Event();scheduler=make_scheduler(h[1],background=True,seconds=.05)
    from apscheduler.events import EVENT_JOB_EXECUTED
    scheduler.add_listener(lambda event:executed.set(),EVENT_JOB_EXECUTED)
    scheduler.start()
    try:assert executed.wait(5)
    finally:scheduler.shutdown(wait=True)
    # No se consultó la API ni hubo navegador durante la ejecución.
    assert len(inbox(h).json())==1 and inbox(h).json()[0]["has_report"]

def test_two_workers_and_restart_do_not_duplicate(proactive,tmp_path):
    a=weekly(proactive);h,clock=proactive
    clock[0]=datetime.fromisoformat(a["next_run"]).replace(tzinfo=None)+timedelta(seconds=1)
    path=tmp_path/"synthetic-worker-only.sqlite"
    target=create_engine("sqlite:///"+path.as_posix(),connect_args={"check_same_thread":False,"timeout":10})
    with h[1]() as db:
        source=db.get_bind().raw_connection();dest=target.raw_connection()
        try:source.driver_connection.backup(dest.driver_connection)
        finally:source.close();dest.close()
    factory=sessionmaker(bind=target,expire_on_commit=False)
    gate=Barrier(2)
    def run():gate.wait();return svc.tick(factory,clock[0])
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:run(),range(2)))
    with factory() as db:assert db.scalar(select(func.count()).select_from(Notification))==1
    target.dispose()
    restarted=create_engine("sqlite:///"+path.as_posix())
    try:
        assert svc.tick(sessionmaker(bind=restarted),clock[0])["notifications"]==0
        with sessionmaker(bind=restarted)() as db:assert db.scalar(select(func.count()).select_from(Notification))==1
    finally:restarted.dispose()

def test_notification_state_expiration_and_audit_minimization(proactive,caplog):
    a=activate(proactive);h,clock=proactive;run_due(proactive,a)
    n=inbox(h).json()[0];c,_,hdr=h
    assert c.patch("/api/chatbot/proactive/notifications/"+n["id"],headers=hdr(2),json={"state":"completed"}).status_code==200
    assert c.patch("/api/chatbot/proactive/notifications/"+n["id"],headers=hdr(3),json={"state":"read"}).status_code==404
    with h[1]() as db:
        events=db.scalars(select(Audit.event)).all()
        assert "draft_saved" in events and "executed" in events and "notification_completed" in events
    assert "Ana" not in caplog.text and "password" not in caplog.text
    clock[0]+=timedelta(days=31)
    assert inbox(h).json()==[]
    assert c.get("/api/chatbot/proactive/notifications/"+n["id"],headers=hdr(2)).status_code==404
    svc.tick(h[1])
    with h[1]() as db:assert db.scalar(select(func.count()).select_from(Notification))==0


def test_daily_report_uses_previous_closed_day(proactive):
    h,clock=proactive;clock[0]=datetime(2026,10,29,13)
    a=activate(proactive,kind="scheduled_report",source_id=None,frequency="daily",local_time="08:01")
    assert run_due(proactive,a)["notifications"]==1
    n=inbox(h).json()[0]
    value=h[0].post("/api/chatbot/proactive/notifications/"+n["id"]+"/report",headers=h[2](2)).json()
    assert value["spec"]["period_start"]==value["spec"]["period_end"]=="2026-10-28"
    assert value["report_rows"]==2


def test_worker_liveness_is_honest(proactive):
    h,clock=proactive;c,_,hdr=h
    assert c.get("/api/chatbot/proactive/status",headers=hdr(2)).json()["worker_running"] is False
    svc.tick(h[1])
    assert c.get("/api/chatbot/proactive/status",headers=hdr(2)).json()["worker_running"] is True
    clock[0]+=timedelta(minutes=3)
    assert c.get("/api/chatbot/proactive/status",headers=hdr(2)).json()["worker_running"] is False


@pytest.mark.parametrize("frequency,expected",[("weekly",("2026-10-19","2026-10-25")),("daily",("2026-10-31","2026-10-31"))])
def test_closed_period_uses_institutional_dates_across_timezones(frequency,expected):
    from app.schemas.chatbot_proactive import ActionSpec
    spec=ActionSpec(kind="scheduled_report",course_id=1,frequency=frequency,timezone="Asia/Tokyo")
    # Lunes en Tokio, todavía domingo en Lima. No se incluye un día institucional abierto.
    start,end=svc.closed_period(spec,datetime(2026,11,1,15))
    assert (start.isoformat(),end.isoformat())==expected


def test_preferences_timezone_length_is_bounded(proactive):
    h,_=proactive
    response=h[0].put("/api/chatbot/proactive/preferences",headers=h[2](2),json={"enabled":True,"timezone":"X"*100})
    assert response.status_code==422
