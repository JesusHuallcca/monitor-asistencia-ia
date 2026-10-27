"""Solo SQLite en RAM, identidades ficticias y conexiones MySQL bloqueadas."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend')]
os.environ.update(DB_HOST='invalid.test', DB_NAME='integration_tests_only', DB_USER='test',
                  DB_PASSWORD='test', JWT_SECRET_KEY='integration-test-only-' * 3, EMOSCAN_ENABLED='false')

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.security import create_access_token
from app.db import database
from app.db.expression_consent import ExpressionConsent
from app.db.personal_expression_consent import PersonalExpressionConsent, read_revision
from app.db.models import Usuario
from app.api import emoscan_personal
from app.services.expression_service import ExpressionService


@event.listens_for(database.engine, 'do_connect')
def reject_mysql(*args, **kwargs):
    raise AssertionError('Las pruebas no pueden conectarse a MySQL.')


@pytest.fixture
def integration(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine, tables=[Usuario.__table__, ExpressionConsent.__table__, PersonalExpressionConsent.__table__])
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        for uid, role in [(1, 'profesor'), (2, 'estudiante'), (3, 'admin'), (4, 'estudiante'), (5, 'superadmin')]:
            db.add(Usuario(id=uid, username=f'test{uid}', email=f'test{uid}@example.test', password_hash='unused', nombres='Test', apellidos='Synthetic', rol=role, estado='activo'))
        db.commit()
    def get_db():
        with sessions() as db:
            yield db
    def consent_reader(uid):
        with sessions() as db:
            return read_revision(db, uid)
    manager = ExpressionService(consent_reader, enabled=True, job_ttl=15)
    monkeypatch.setattr(emoscan_personal, 'personal_service', manager)
    app.dependency_overrides[database.get_db] = get_db
    def headers(uid=1):
        return {'Authorization': 'Bearer ' + create_access_token(uid, 'ignored-token-role')}
    with TestClient(app) as client:
        yield client, manager, sessions, headers
    app.dependency_overrides.clear()
    manager.close()
    engine.dispose()
