"""Current login and course contracts; synthetic identities, SQLite only."""
import pytest
from backend.tests.parte7.conftest import harness
from app.api import auth, users, cursos
from app.core.security import hash_password
from app.db.models import Usuario

@pytest.fixture
def login_harness(harness):
    client,sessions,headers=harness
    for router in (auth.router,users.router,cursos.router):client.app.include_router(router)
    with sessions() as db:
        for uid in (1,2,3):db.get(Usuario,uid).password_hash=hash_password("synthetic-local-password")
        db.commit()
    return harness

def test_existing_logins_and_me(login_harness):
    client,_,headers=login_harness
    for uid,role in [(1,"admin"),(2,"profesor"),(3,"estudiante")]:
        response=client.get("/api/users/me",headers=headers(uid))
        assert response.status_code==200 and response.json()["rol"]==role
        path="/api/auth/admin/login" if role=="admin" else "/api/auth/login"
        result=client.post(path,json={"identificador":"synthetic"+str(uid),"password":"synthetic-local-password"})
        assert result.status_code==200 and result.json()["rol"]==role
    assert client.post("/api/auth/login",json={"identificador":"synthetic1","password":"synthetic-local-password"}).status_code==401

def test_superadmin(login_harness,monkeypatch):
    client,sessions,_=login_harness
    with sessions() as db:db.get(Usuario,1).rol="superadmin";db.commit()
    value=client.post("/api/auth/admin/login",json={"identificador":"synthetic1","password":"synthetic-local-password"})
    assert value.status_code==200 and value.json()["rol"]=="superadmin"
    headers={"Authorization":"Bearer "+value.json()["access_token"]}
    assert client.get("/api/chatbot/context",headers=headers).status_code==403
    monkeypatch.setenv("CHATBOT_INSTITUTIONAL_READ_USER_IDS","1")
    assert len(client.get("/api/chatbot/context",headers=headers).json()["courses"])==3

def test_reuses_course_permissions(login_harness):
    client,_,headers=login_harness
    visible={course["id"] for course in client.get("/api/cursos",headers=headers(2)).json()}
    chatbot={course["id"] for course in client.get("/api/chatbot/context",headers=headers(2)).json()["courses"]}
    assert visible==chatbot=={1}
