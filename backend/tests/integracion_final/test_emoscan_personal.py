import io
import time
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from PIL import Image

from app.api import attendance, emoscan_personal
from app.db.expression_consent import ExpressionConsent, CONSENT_VERSION, read_revision as attendance_revision
from app.db.personal_expression_consent import VERSION, PersonalExpressionConsent, read_revision
from app.services.expression_service import Job


def picture(width=120, height=120):
    out = io.BytesIO()
    Image.new('RGB', (width, height), color=(50, 50, 50)).save(out, format='JPEG')
    return out.getvalue()


def accept(client, headers, accepted=True, version=VERSION):
    return client.put('/api/emoscan-personal/consent', headers=headers, json={'accepted': accepted, 'text_version': version})


@pytest.mark.parametrize('path,method', [('/consent', 'get'), ('/consent', 'put'), ('/analizar', 'post'), ('/jobs/none', 'get'), ('/jobs', 'delete')])
def test_personal_requires_authenticated_student(integration, path, method):
    client, _, _, headers = integration
    request = getattr(client, method)
    assert request('/api/emoscan-personal' + path).status_code == 401
    for uid in [1, 3, 5]:
        assert request('/api/emoscan-personal' + path, headers=headers(uid)).status_code == 403


def test_personal_consent_separate_from_attendance(integration):
    client, manager, sessions, headers = integration
    status = client.get('/api/emoscan-personal/consent', headers=headers(2))
    assert not status.json()['accepted']
    assert status.headers['cache-control'] == 'no-store'
    assert accept(client, headers(2), version=CONSENT_VERSION).status_code == 409
    assert accept(client, headers(2)).status_code == 200
    with sessions() as db:
        assert read_revision(db, 2)
        assert attendance_revision(db, 2) is None
        assert db.get(ExpressionConsent, 2) is None
        assert set(PersonalExpressionConsent.__table__.columns.keys()) == {
            'usuario_id', 'aceptado', 'texto_version', 'revision', 'actualizado_en'}
    assert accept(client, headers(2), False, version='old').status_code == 200
    assert not manager.jobs


def test_independent_analysis_never_registers_attendance(integration, monkeypatch):
    client, manager, _, headers = integration
    register = Mock(side_effect=AssertionError('No debe registrar asistencia'))
    monkeypatch.setattr(attendance.attendance_service, 'register', register)
    submit = Mock(return_value={'status': 'QUEUED', 'job_id': 'synthetic-job', 'expires_in': 10})
    monkeypatch.setattr(manager, 'submit', submit)
    opts = {'headers': {**headers(2), 'Content-Type': 'image/jpeg'}, 'content': picture()}
    assert client.post('/api/emoscan-personal/analizar', **opts).status_code == 403
    assert not submit.called
    accept(client, headers(2))
    for _ in range(2):
        response = client.post('/api/emoscan-personal/analizar', **opts)
        assert response.status_code == 202 and response.headers['cache-control'] == 'no-store'
    assert submit.call_count == 2
    assert submit.call_args.args[0] == 2
    assert submit.call_args.args[1].shape == (120, 120, 3)
    register.assert_not_called()


def test_private_results_revocation_and_expiry(integration):
    client, manager, sessions, headers = integration
    accept(client, headers(2))
    with sessions() as db:
        revision = read_revision(db, 2)
    manager.jobs['private'] = Job(2, revision, time.monotonic() + 30, None, 'READY', {'status': 'READY', 'scores': {'happy': 1.0}})
    assert client.get('/api/emoscan-personal/jobs/private', headers=headers(4)).status_code == 404
    own = client.get('/api/emoscan-personal/jobs/private', headers=headers(2))
    assert own.status_code == 200 and own.headers['cache-control'] == 'no-store'
    accept(client, headers(2), False)
    assert client.get('/api/emoscan-personal/jobs/private', headers=headers(2)).status_code == 404
    assert not manager.jobs
    accept(client, headers(2))
    with sessions() as db:
        revision = read_revision(db, 2)
    manager.jobs['expired'] = Job(2, revision, time.monotonic() - 1, None)
    assert client.get('/api/emoscan-personal/jobs/expired', headers=headers(2)).status_code == 404
    manager.jobs['clear'] = Job(2, revision, time.monotonic() + 30, None)
    assert client.delete('/api/emoscan-personal/jobs', headers=headers(2)).status_code == 204
    assert not manager.jobs


def test_images_limits_and_unavailable_services(integration, monkeypatch):
    client, manager, _, headers = integration
    accept(client, headers(2))
    h = {**headers(2), 'Content-Type': 'image/jpeg'}
    for content, status in [(b'x' * (300 * 1024 + 1), 413), (b'not-jpeg', 422), (picture(1300, 100), 422)]:
        assert client.post('/api/emoscan-personal/analizar', headers=h, content=content).status_code == status
    assert client.post('/api/emoscan-personal/analizar', headers={**h, 'Content-Type': 'image/png'}, content=picture()).status_code == 415
    manager.enabled = False
    assert client.post('/api/emoscan-personal/analizar', headers=h, content=picture()).status_code == 503
    manager.enabled = True
    monkeypatch.setattr(manager, 'submit', Mock(return_value={'status': 'BUSY'}))
    assert client.post('/api/emoscan-personal/analizar', headers=h, content=picture()).status_code == 429
    monkeypatch.setattr(emoscan_personal, 'read_revision', Mock(side_effect=RuntimeError('offline')))
    assert client.post('/api/emoscan-personal/analizar', headers=h, content=picture()).status_code == 503
