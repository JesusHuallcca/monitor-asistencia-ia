"""Servidor SOLO de pruebas con SQLite en memoria, sin MySQL ni identidades reales."""
from pathlib import Path
import sys,secrets
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db.database import Base,get_db
from app.db.models import Matricula
from app.core.config import settings
from app.parte6 import create_app
from app.services import parte6_service as service
from red_neuronal.tests.test_system import seed,NOW
from datetime import datetime
engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
Base.metadata.create_all(engine)
with Session(engine) as db:
    seed(db);db.add(Matricula(id=3,curso_id=1,estudiante_id=2,matriculado_en=datetime(2025,1,1)));db.commit()
settings.JWT_SECRET_KEY=secrets.token_urlsafe(48)
service.now_local=lambda:NOW
app=create_app(configuration_check=lambda:None,database_kind='sqlite_fixture',integration_ready=True)
def test_db():
    with Session(engine,autoflush=False) as db:yield db
app.dependency_overrides[get_db]=test_db
# The synthetic JWT report uses the same fixture connection and the real JWT verifier.
import app.parte6 as entry
entry.read_only_db=test_db
