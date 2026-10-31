from datetime import date, datetime, time, timedelta, timezone
import pytest
from jose import jwt
from sqlalchemy import delete
from app.api import chatbot
from app.db.models import AsignacionProfesor, Asistencia, SesionClase
from app.services.chatbot_conversation import signing_key, normalize, classify, parse_period


def ask(h,uid,message,context=None,**values):
    client,_,headers=h
    payload={"message":message,**values}
    if context: payload["context_token"]=context["token"]
    return client.post("/api/chatbot/message",headers=headers(uid),json=payload)


@pytest.mark.parametrize("question,intent",[("Hola.","GREETING"),("Buenos días","GREETING"),("¡Muchas gracias!","THANKS"),("Gracias por tu ayuda","THANKS"),("Hasta luego","GOODBYE"),("Chau","GOODBYE"),("¿Cuáles son mis materias?","COURSES"),("Y cuál tiene más tardanzas","LATE_RANKING"),("¿Y ese?","CLARIFY")])
def test_spanish_intents(harness,question,intent):
    response=ask(harness,3,question)
    assert response.status_code==200
    assert response.json()["intent"]==intent
    assert response.json()["reply"]


def test_required_conversation_chain(harness):
    _,sessions,_=harness
    # Perfil ficticio: curso 2 tiene dos observaciones tardías de octubre 2026.
    with sessions() as db:
        for i in (10,11):
            db.add(SesionClase(id=i,curso_id=2,fecha=date(2026,10,i),hora_inicio=time(9),hora_fin=time(10)))
            db.flush()
            db.add(Asistencia(id=i,usuario_id=3,sesion_id=i,fecha=date(2026,10,i),hora=time(9),confianza=0,liveness_score=0,estado="TARDANZA"))
        db.commit()
    hello=ask(harness,3,"Hola").json()
    courses=ask(harness,3,"¿Cuáles son mis cursos?",hello["context"]).json()
    assert {c["id"] for c in courses["data"]}=={1,2}
    rank=ask(harness,3,"¿Y cuál tiene más tardanzas?",courses["context"]).json()
    assert rank["data"][0]["curso_id"]==2
    assert rank["context"]["course_id"]==2
    records=ask(harness,3,"Muéstrame los registros de octubre de 2026",rank["context"]).json()
    assert records["intent"]=="STUDENT_HISTORY"
    assert records["context"]["period_start"]=="2026-10-01"
    assert records["context"]["period_end"]=="2026-10-31"
    assert len([r for r in records["data"] if r["estado"]=="TARDANZA"])==2
    assert {r["curso"] for r in records["data"]}=={"Curso 2"}
    assert all(r["fecha"].startswith("2026-10-") for r in records["data"])
    assert "inclusive" in records["reply"]


def test_period_and_student_persist_and_can_be_cleared(harness):
    first=ask(harness,2,"Mi historial",student_id=1,course_id=1,period_start="2026-10-01",period_end="2026-10-31").json()
    again=ask(harness,2,"¿Y también el resumen?",first["context"]).json()
    assert again["context"]["student_id"]==1
    assert again["context"]["course_id"]==1
    assert again["context"]["period_start"]=="2026-10-01"
    cleared=ask(harness,2,"Mi historial",again["context"],student_id=None,course_id=None,period_start=None,period_end=None).json()
    assert cleared["context"]["student_id"] is None
    assert cleared["context"]["period_start"] is None


def test_natural_course_change_and_show_all_courses(harness):
    first=ask(harness,3,"Mi historial",course_id=1).json()
    second=ask(harness,3,"Muéstrame registros del Curso 2",first["context"]).json()
    assert second["context"]["course_id"]==2
    assert {row["curso"] for row in second["data"]}=={"Curso 2"}
    third=ask(harness,3,"Cuáles son mis cursos",second["context"]).json()
    assert {row["id"] for row in third["data"]}=={1,2}
    assert third["context"]["course_id"] is None


def test_natural_student_change_only_within_scope(harness):
    first=ask(harness,2,"Historial de Ana").json()
    second=ask(harness,2,"Historial de Luis",first["context"])
    assert second.status_code==200
    assert second.json()["context"]["student_id"]==2
    assert ask(harness,2,"Historial de Maria",first["context"]).status_code==403


def test_context_is_bound_to_account(harness):
    first=ask(harness,3,"Mis cursos").json()
    assert ask(harness,4,"Mi historial",first["context"]).status_code==403


def test_tampering_expiry_and_wrong_token_purpose(harness):
    first=ask(harness,3,"Mis cursos").json()
    token=first["context"]["token"]
    assert ask(harness,3,"Mi historial",{"token":token+"invalid"}).status_code==409
    payload=jwt.get_unverified_claims(token)
    payload["exp"]=(datetime.now(timezone.utc)-timedelta(seconds=5)).timestamp()
    expired=jwt.encode(payload,signing_key(),algorithm="HS256")
    assert ask(harness,3,"Mi historial",{"token":expired}).status_code==409
    client,_,_=harness
    assert client.get("/api/chatbot/context",headers={"Authorization":"Bearer "+token}).status_code==401


def test_context_does_not_survive_revocation(harness):
    first=ask(harness,2,"Mi historial",student_id=1).json()
    _,sessions,_=harness
    with sessions() as db:
        db.execute(delete(AsignacionProfesor));db.commit()
    response=ask(harness,2,"Y el resumen",first["context"])
    assert response.status_code==409
    assert ask(harness,2,"Mi historial",student_id=1).status_code==403


def test_explicit_reset_ignores_old_context(harness):
    first=ask(harness,3,"Registros de octubre",course_id=1).json()
    reset=ask(harness,3,"Mis cursos",first["context"],reset_context=True).json()
    assert reset["context"]["course_id"] is None
    assert reset["context"]["period_start"] is None


@pytest.mark.parametrize("values",[{"student_id":2},{"course_id":3},{"intent":"MODEL_METRICS"},{"sql":"SELECT * FROM usuarios"}])
def test_context_never_grants_permissions(harness,values):
    first=ask(harness,3,"Hola").json()
    response=ask(harness,3,"Mi historial",first["context"],**values)
    assert response.status_code==(422 if "intent" in values or "sql" in values else 403)


@pytest.mark.parametrize("values",[{"period_start":"2026-11-01","period_end":"2026-10-01"},{"period_start":"2026-10-01"},{"period_start":None},{"period_start":"2024-01-01","period_end":"2026-12-31"}])
def test_invalid_period_rejected(harness,values):
    assert ask(harness,3,"Mi historial",**values).status_code==422


def test_followup_month_uses_previous_statistics_intent_even_after_thanks(harness):
    first=ask(harness,3,"Resumen de asistencia de octubre").json()
    thanks=ask(harness,3,"Gracias",first["context"]).json()
    second=ask(harness,3,"¿Y en noviembre?",thanks["context"]).json()
    assert second["intent"]=="COURSE_STATS"
    assert second["context"]["period_start"].endswith("-11-01")


def test_ranking_does_not_include_other_students(harness):
    # En curso 2 Maria tiene una tardanza; Ana no. La cuenta Ana no debe contar la de Maria.
    response=ask(harness,3,"Cuál tiene más tardanzas").json()
    assert all(row["tardanzas"]==0 for row in response["data"])
    assert "Maria" not in response["reply"]


def test_structured_gemini_receives_no_context_token(harness,monkeypatch):
    sent=[]
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"candidates":[]}
    class Client:
        def __init__(self,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,url,**kwargs): sent.append(kwargs["json"]);return Response()
    monkeypatch.setenv("GEMINI_API_KEY","test-only")
    monkeypatch.setenv("GEMINI_MODEL","test-only")
    monkeypatch.setattr(chatbot.httpx,"AsyncClient",Client)
    first=ask(harness,3,"Mis cursos").json()
    second=ask(harness,3,"Mi historial",first["context"]).json()
    assert second["provider"]=="local"
    assert first["context"]["token"] not in str(sent)


def test_parse_period_leap_year_and_relative_dates():
    assert parse_period("febrero de 2024",date(2026,10,30))[:2]==(date(2024,2,1),date(2024,2,29))
    assert parse_period("mes pasado",date(2026,1,2))[:2]==(date(2025,12,1),date(2025,12,31))
