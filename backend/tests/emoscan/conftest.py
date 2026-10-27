"""Dedicated isolated suite: fake settings, SQLite RAM, fail on MySQL connections."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))
os.environ.update(DB_HOST='invalid.test', DB_NAME='emoscan_tests_only',
                  DB_USER='test', DB_PASSWORD='test', JWT_SECRET_KEY='test-only-secret-' * 3,
                  EMOSCAN_ENABLED='false')

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import attendance, expressions
from app.core.security import create_access_token
from app.db import database
from app.db.expression_consent import ExpressionConsent, read_revision
from app.db.models import Usuario
from app.services import expression_service as service_module
from app.services.expression_service import ExpressionService


@event.listens_for(database.engine, 'do_connect')
def reject_mysql(*args, **kwargs):
    raise AssertionError('The EmoScan suite must never connect to MySQL')


@pytest.fixture
def integration(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    database.Base.metadata.create_all(engine, tables=[Usuario.__table__, ExpressionConsent.__table__])
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        for uid, role in ((1, 'estudiante'), (2, 'estudiante'), (3, 'profesor')):
            db.add(Usuario(id=uid, username=f'test{uid}', email=f'test{uid}@example.test',
                           password_hash='not-a-real-password', nombres='Synthetic',
                           apellidos='Test', rol=role, estado='activo'))
        db.commit()

    def consent_reader(uid):
        with sessions() as db:
            return read_revision(db, uid)

    manager = ExpressionService(consent_reader, enabled=True)
    monkeypatch.setattr(service_module, 'expression_service', manager)
    monkeypatch.setattr(expressions, 'expression_service', manager)
    app = FastAPI()
    app.include_router(attendance.router)
    app.include_router(expressions.router)

    def get_db():
        with sessions() as db:
            yield db

    app.dependency_overrides[database.get_db] = get_db

    def headers(uid=1):
        return {'Authorization': 'Bearer ' + create_access_token(uid, 'estudiante')}

    with TestClient(app) as client:
        yield client, manager, sessions, headers
    manager.close()
    engine.dispose()
