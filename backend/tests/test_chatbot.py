"""Legacy cases retained against the current scoped router and explicit fixtures."""
from pathlib import Path
import pytest
from backend.tests.parte7.conftest import harness
from app.db.models import Asistencia, Usuario

def ask(h, uid, question, **values):
    return h[0].post("/api/chatbot/message", headers=h[2](uid), json={"message":question, **values})

def test_auth_required(harness):
    assert harness[0].post("/api/chatbot/message", json={"message":"Mis cursos"}).status_code == 401

def test_scope_context(harness, monkeypatch):
    for uid, courses, students in [(3,2,1),(2,1,2)]:
        value=harness[0].get("/api/chatbot/context",headers=harness[2](uid))
        assert value.status_code==200
        assert len(value.json()["courses"])==courses and len(value.json()["students"])==students
    assert harness[0].get("/api/chatbot/context",headers=harness[2](1)).status_code==403
    monkeypatch.setenv("CHATBOT_INSTITUTIONAL_READ_USER_IDS","1")
    assert len(harness[0].get("/api/chatbot/context",headers=harness[2](1)).json()["courses"])==3

@pytest.mark.parametrize("uid,target",[(3,2),(2,3)])
def test_forbidden_student(harness,uid,target):
    assert ask(harness,uid,"Ver historial",student_id=target).status_code==403

@pytest.mark.parametrize("uid,name",[(3,"Luis"),(3,"Maria"),(2,"Maria")])
def test_forbidden_name(harness,uid,name):
    assert ask(harness,uid,"Dame la asistencia de "+name).status_code==403

def test_forbidden_course_and_forged_role(harness):
    assert ask(harness,3,"Asistencia",course_id=3).status_code==403
    assert ask(harness,3,"Mis cursos",role="ADMIN").status_code==422

def test_student_data_only(harness):
    rows=ask(harness,3,"Mi historial").json()["data"]
    assert len(rows)==2 and {row["estudiante"] for row in rows}=={"Ana Perfil3"}

def test_tardy_intent_priority(harness):
    with harness[1]() as db:
        db.get(Asistencia,1).estado="TARDANZA";db.commit()
    value=ask(harness,2,"Ver historial de tardanzas").json()
    assert value["intent"]=="LATE_STUDENTS"
    assert len(value["data"])==1 and all(row["estado"]=="TARDANZA" for row in value["data"])

def test_statistics_and_filter(harness):
    value=ask(harness,3,"Resumen de asistencia").json()["data"]
    assert value=={"registros":2,"presentes":1,"tardanzas":0,"ausentes":1,"porcentaje_asistencia":50.0}
    assert ask(harness,2,"Resumen de asistencia",course_id=2).status_code==403

def test_today_and_voice(harness):
    value=ask(harness,2,"Cuántos faltaron hoy",source="voice").json()
    assert value["intent"]=="ATTENDANCE_TODAY" and len(value["data"])==2
    assert "1 ausencias" in value["reply"]

def test_no_invented_predictions(harness):
    response=ask(harness,2,"Consulta probabilidad de asistencia con Parte 6")
    assert response.status_code==200
    assert response.json()["ml"]["status"] in {"pending","unavailable"}
    assert "probability" not in response.json()["ml"]
    assert ask(harness,2,"Métricas del modelo").status_code==403

def test_sql_input_does_not_execute(harness,monkeypatch):
    monkeypatch.setenv("CHATBOT_INSTITUTIONAL_READ_USER_IDS","1")
    assert ask(harness,1,"DROP TABLE usuarios; SELECT * FROM usuarios").status_code==200
    with harness[1]() as db:assert db.get(Usuario,3).estado=="activo"

def test_history_isolation_and_clear(harness):
    ask(harness,3,"Mis cursos")
    c,_,headers=harness
    assert len(c.get("/api/chatbot/history",headers=headers(3)).json())==1
    assert c.get("/api/chatbot/history",headers=headers(2)).json()==[]
    assert c.delete("/api/chatbot/history",headers=headers(2)).status_code==200
    assert len(c.get("/api/chatbot/history",headers=headers(3)).json())==1
    assert c.delete("/api/chatbot/history",headers=headers(3)).status_code==200
    assert c.get("/api/chatbot/history",headers=headers(3)).json()==[]

@pytest.mark.parametrize("question",[""," "*5,"x"*2001])
def test_invalid_question(harness,question):
    assert ask(harness,3,question).status_code==422

def test_static_pages_are_served_by_the_frontend_deployment():
    root=Path(__file__).resolve().parents[2]/"frontend"
    for name in ["login.html","admin/usuarios.html","profesor/ia.html","estudiante/ia.html","components/chatbot.js","css/chatbot.css"]:
        assert (root/name).stat().st_size>0
