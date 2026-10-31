"""Harness del router real: JWT reales, SQLite RAM y MySQL bloqueado."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
os.environ.update(DB_HOST="invalid.test", DB_NAME="parte7_tests_only", DB_USER="test",
                  DB_PASSWORD="test", JWT_SECRET_KEY="parte7-test-only-" * 4,
                  EMOSCAN_ENABLED="false")
# Router aislado; sin conexiones externas ni descarga de modelos.
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles

@compiles(BigInteger, "sqlite")
def sqlite_autoincrement_id(type_, compiler, **kw):
    """SQLite exige INTEGER exacto; MySQL conserva BIGINT sin cambios."""
    return "INTEGER"

from sqlalchemy.pool import StaticPool
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from app.core.config import TIMEZONE
from app.core.security import create_access_token
from app.db import database
from app.db.models import (Usuario, Profesor, Estudiante, Curso, AsignacionProfesor,
                           Matricula, SesionClase, Asistencia, Evaluacion, Nota)
from app.api import chatbot


@event.listens_for(database.engine, "do_connect")
def reject_mysql(*args, **kwargs):
    raise AssertionError("MySQL está bloqueado en las pruebas de Parte 7.")


@pytest.fixture
def harness(monkeypatch):
    monkeypatch.delenv("CHATBOT_INSTITUTIONAL_READ_USER_IDS", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    with sessions() as db:
        roles = {1:"admin",2:"profesor",3:"estudiante",4:"estudiante",5:"estudiante",
                 6:"profesor",7:"estudiante",8:"invitado",9:"superadmin",10:"profesor",11:"estudiante"}
        names = {3:"Ana",4:"Luis",5:"Maria"}
        for uid, role in roles.items():
            db.add(Usuario(id=uid, username=f"synthetic{uid}", email=f"s{uid}@example.test",
                           password_hash="unused", nombres=names.get(uid,"Test"),
                           apellidos=f"Perfil{uid}", rol=role, estado="activo"))
        db.add_all([Profesor(id=1,usuario_id=2),Profesor(id=2,usuario_id=6)])
        db.add_all([Estudiante(id=i,usuario_id=u,codigo=f"S{i}") for i,u in [(1,3),(2,4),(3,5),(4,11)]])
        db.add_all([Curso(id=i,codigo=f"C{i}",nombre=f"Curso {i}",periodo="2026",activo=i!=3) for i in (1,2,3)])
        db.flush()
        db.add(AsignacionProfesor(profesor_id=1,curso_id=1))
        db.add_all([Matricula(estudiante_id=e,curso_id=c) for e,c in [(1,1),(1,2),(2,1),(3,2),(3,3)]])
        for sid,cid,day in [(1,1,0),(2,2,0),(3,2,1),(4,1,2)]:
            db.add(SesionClase(id=sid,curso_id=cid,fecha=today+timedelta(days=day),hora_inicio=time(9),hora_fin=time(10)))
        db.flush()
        for aid,uid,sid,state in [(1,3,1,"PRESENTE"),(2,4,1,"AUSENTE"),(3,3,2,"AUSENTE"),(4,5,2,"TARDANZA")]:
            db.add(Asistencia(id=aid,usuario_id=uid,sesion_id=sid,fecha=today,hora=time(9),confianza=0,liveness_score=0,estado=state))
        db.add_all([Evaluacion(id=1,curso_id=1,nombre="Sintetica"),Evaluacion(id=2,curso_id=2,nombre="Ajena")])
        db.flush()
        db.add_all([Nota(evaluacion_id=1,estudiante_id=1,nota=16),Nota(evaluacion_id=2,estudiante_id=1,nota=2)])
        db.commit()
    def get_db():
        with sessions() as db:
            yield db
    app = FastAPI()
    app.include_router(chatbot.router)
    app.dependency_overrides[database.get_db] = get_db
    def headers(uid, token_role="superadmin"):
        # El rol del token se ignora; get_current_user lee el usuario de SQLite.
        return {"Authorization":"Bearer " + create_access_token(uid, token_role)}
    with TestClient(app) as client:
        yield client, sessions, headers
    engine.dispose()
