import base64
import time
import threading
import subprocess
import sys
from datetime import datetime, time as daytime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from app.api import attendance
from app.db.expression_consent import CONSENT_VERSION, ExpressionConsent
from app.services.expression_service import ExpressionService, after_attendance
from app.services.expression_worker import infer_expression
from worker_stubs import ready, hang, crash


def photo():
    frame = np.full((120, 120, 3), 42, dtype=np.uint8)
    ok, encoded = cv2.imencode('.jpg', frame)
    assert ok
    return frame, base64.b64encode(encoded).decode()


def accept(client, headers, accepted=True, version=CONSENT_VERSION):
    return client.put('/api/expressions/consent', headers=headers,
                      json={'accepted': accepted, 'text_version': version})


def wait_for(check, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if value := check():
            return value
        time.sleep(.03)
    raise AssertionError('Timed out waiting for the isolated worker')


def test_consent_is_separate_voluntary_and_versioned(integration):
    client, manager, sessions, headers = integration
    status = client.get('/api/expressions/consent', headers=headers())
    assert status.status_code == 200
    assert not status.json()['accepted']
    assert 'voluntariamente' in status.json()['text']
    assert accept(client, headers(), version='old').status_code == 409
    assert accept(client, headers()).status_code == 200
    with sessions() as db:
        row = db.get(ExpressionConsent, 1)
        assert row.aceptado and row.texto_version == CONSENT_VERSION
        assert set(row.__table__.columns.keys()) == {
            'usuario_id', 'aceptado', 'texto_version', 'revision', 'actualizado_en'}
    assert accept(client, headers(), False, version='old').status_code == 200
    assert not client.get('/api/expressions/consent', headers=headers()).json()['accepted']


@pytest.mark.parametrize('path,method,body', [
    ('/api/expressions/consent', 'get', None),
    ('/api/expressions/consent', 'put', {'accepted': True, 'text_version': CONSENT_VERSION}),
    ('/api/expressions/jobs/unknown', 'get', None),
])
def test_authentication_and_roles(integration, path, method, body):
    client, _, _, headers = integration
    options = {'json': body} if body is not None else {}
    assert getattr(client, method)(path, **options).status_code == 401
    assert getattr(client, method)(path, headers=headers(3), **options).status_code == 403


def test_no_consent_no_copy_no_inference(integration):
    _, manager, _, _ = integration
    frame, _ = photo()
    assert manager.submit(1, frame)['status'] == 'NO_CONSENT'
    assert not manager.jobs and manager.thread is None
    manager.enabled = False
    assert manager.submit(1, frame)['status'] == 'DISABLED'


@pytest.mark.parametrize('path', ['/api/attendance/check-in', '/api/attendance/camera/check-in'])
def test_attendance_commits_before_enqueue_same_frame(integration, monkeypatch, path):
    client, manager, _, headers = integration
    frame, image = photo()
    events = []
    monkeypatch.setattr(attendance.attendance_face_service, 'recognize',
                        lambda **kw: {'usuario_id': 1, 'confidence': .95})
    monkeypatch.setattr(attendance.liveness_service, 'check', lambda frame: {'is_live': True, 'score': 12})

    def register(**kwargs):
        events.append('committed')  # Stub represents the existing committed repository.
        return {'success': True, 'status': 'REGISTERED', 'attendance': {'id': 100}}

    def submit(uid, actual):
        assert events == ['committed'] and uid == 1
        np.testing.assert_array_equal(actual, frame)
        events.append('submitted')
        return {'status': 'QUEUED', 'job_id': 'synthetic-job'}

    monkeypatch.setattr(attendance.attendance_service, 'register', register)
    monkeypatch.setattr(manager, 'submit', submit)
    response = client.post(path, headers=headers(), json={'image': image})
    assert response.status_code == 200
    assert response.json()['status'] == 'REGISTERED'
    assert response.json()['expression_analysis']['status'] == 'QUEUED'
    assert events == ['committed', 'submitted']


def test_optional_failure_cannot_undo_attendance(integration, monkeypatch):
    client, manager, _, headers = integration
    _, image = photo()
    monkeypatch.setattr(attendance.attendance_face_service, 'recognize',
                        lambda **kw: {'usuario_id': 1, 'confidence': .95})
    monkeypatch.setattr(attendance.liveness_service, 'check', lambda frame: {'is_live': True, 'score': 12})
    monkeypatch.setattr(attendance.attendance_service, 'register',
                        lambda **kw: {'success': True, 'status': 'REGISTERED'})
    monkeypatch.setattr(manager, 'submit', Mock(side_effect=RuntimeError('synthetic error')))
    response = client.post('/api/attendance/camera/check-in', headers=headers(), json={'image': image})
    assert response.status_code == 200
    assert response.json()['status'] == 'REGISTERED'
    assert response.json()['expression_analysis'] == {'status': 'UNAVAILABLE'}


@pytest.mark.parametrize('recognition,live,status', [
    (None, True, 'UNKNOWN_FACE'),
    ({'usuario_id': 2, 'confidence': .9}, True, 'IDENTITY_MISMATCH'),
    ({'usuario_id': 1, 'confidence': .9}, False, 'LIVENESS_FAILED'),
])
def test_unvalidated_identity_never_enqueues(integration, monkeypatch, recognition, live, status):
    client, manager, _, headers = integration
    _, image = photo()
    monkeypatch.setattr(attendance.attendance_face_service, 'recognize', lambda **kw: recognition)
    monkeypatch.setattr(attendance.liveness_service, 'check', lambda frame: {'is_live': live, 'score': 0})
    submit = Mock(side_effect=AssertionError('Must not enqueue'))
    monkeypatch.setattr(manager, 'submit', submit)
    response = client.post('/api/attendance/camera/check-in', headers=headers(), json={'image': image})
    assert response.json()['status'] == status
    submit.assert_not_called()


@pytest.mark.parametrize('status', ['ALREADY_REGISTERED', 'NO_ACTIVE_SESSION'])
def test_no_analysis_without_new_attendance(integration, monkeypatch, status):
    _, manager, _, _ = integration
    submit = Mock(side_effect=AssertionError('Must not enqueue'))
    monkeypatch.setattr(manager, 'submit', submit)
    original = {'success': False, 'status': status}
    assert after_attendance(original, 1, photo()[0]) is original
    submit.assert_not_called()


def test_bounded_queue_timeout_and_recovery():
    manager = ExpressionService(lambda uid: 'revision', enabled=True, capacity=1,
                                job_ttl=1, target=hang)
    try:
        first = manager.submit(1, photo()[0])
        assert first['status'] == 'QUEUED'
        assert manager.submit(2, photo()[0])['status'] == 'BUSY'
        wait_for(lambda: manager.get(1, first['job_id']) is None, seconds=4)
        manager.target = ready
        manager.job_ttl = 8
        second = manager.submit(2, photo()[0])
        assert second['status'] == 'QUEUED'
        assert wait_for(lambda: (value if (value := manager.get(2, second['job_id']))
                                and value['status'] == 'READY' else None))['synthetic_test_pixel'] == 42
    finally:
        manager.close()
    assert not manager.thread.is_alive() and not manager.jobs


def test_child_result_is_private_expires_and_frame_is_released():
    manager = ExpressionService(lambda uid: 'revision', enabled=True, target=ready,
                                job_ttl=8, result_ttl=.3)
    try:
        frame, _ = photo()
        job_id = manager.submit(1, frame)['job_id']
        frame[:] = 99
        result = wait_for(lambda: (value if (value := manager.get(1, job_id))
                                  and value['status'] == 'READY' else None))
        assert result['synthetic_test_pixel'] == 42
        assert manager.get(2, job_id) is None
        assert manager.jobs[job_id].frame is None
        wait_for(lambda: manager.get(1, job_id) is None)
        assert not manager.jobs
    finally:
        manager.close()


def test_crashed_child_is_unavailable():
    manager = ExpressionService(lambda uid: 'revision', enabled=True, target=crash, job_ttl=8)
    try:
        job_id = manager.submit(1, photo()[0])['job_id']
        result = wait_for(lambda: (value if (value := manager.get(1, job_id))
                                  and value['status'] == 'UNAVAILABLE' else None))
        assert result['status'] == 'UNAVAILABLE'
    finally:
        manager.close()


def test_revocation_discards_running_job_and_cannot_be_reaccepted(integration):
    client, manager, _, headers = integration
    manager.target = hang
    assert accept(client, headers()).status_code == 200
    job_id = manager.submit(1, photo()[0])['job_id']
    assert accept(client, headers(), False).status_code == 200
    assert not manager.jobs
    assert client.get('/api/expressions/jobs/' + job_id, headers=headers()).status_code == 404
    assert accept(client, headers()).status_code == 200
    assert manager.get(1, job_id) is None


def test_result_endpoint_checks_owner_and_consent_and_disables_cache(integration):
    client, manager, _, headers = integration
    manager.target = ready
    manager.job_ttl = 8
    accept(client, headers())
    accept(client, headers(2))
    job_id = manager.submit(1, photo()[0])['job_id']
    response = client.get('/api/expressions/jobs/' + job_id, headers=headers(2))
    assert response.status_code == 404
    response = client.get('/api/expressions/jobs/' + job_id, headers=headers())
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    accept(client, headers(), False)
    assert client.get('/api/expressions/jobs/' + job_id, headers=headers()).status_code == 404


def test_real_onnx_photo_through_isolated_queue():
    root = Path(__file__).resolve().parents[3]
    image = cv2.imread(str(root / 'integraciones/emoscan/imagenes_prueba/astronauta.png'))
    assert image is not None
    manager = ExpressionService(lambda uid: 'authorized-public-photo-test', enabled=True,
                                target=infer_expression, job_ttl=10,
                                model_path=str(root / 'integraciones/emoscan/emotion-ferplus-8.onnx'))
    try:
        job_id = manager.submit(1, image)['job_id']
        result = wait_for(lambda: (value if (value := manager.get(1, job_id))
                                  and value['status'] == 'READY' else None), seconds=12)
        assert result['estimated_expression'] == 'happy'
        assert result['scores']['happy'] > .9
        assert len(result['scores']) == 8
        assert sum(result['scores'].values()) == pytest.approx(1)
        assert manager.jobs[job_id].frame is None
    finally:
        manager.close()


def test_real_worker_missing_model_is_unavailable():
    root = Path(__file__).resolve().parents[3]
    image = cv2.imread(str(root / 'integraciones/emoscan/imagenes_prueba/astronauta.png'))
    manager = ExpressionService(lambda uid: 'authorized-public-photo-test', enabled=True,
                                model_path='absent-test-model.onnx', job_ttl=8)
    try:
        job_id = manager.submit(1, image)['job_id']
        assert wait_for(lambda: (value if (value := manager.get(1, job_id))
                                and value['status'] == 'UNAVAILABLE' else None))
    finally:
        manager.close()


def test_consent_changed_without_local_notification_is_rechecked():
    revision = ['accepted-v1']
    manager = ExpressionService(lambda uid: revision[0], enabled=True, target=ready, job_ttl=8)
    try:
        job_id = manager.submit(1, photo()[0])['job_id']
        revision[0] = 'accepted-v2'
        assert manager.get(1, job_id) is None
        assert not manager.jobs
    finally:
        manager.close()


def test_consent_storage_failure_is_closed(integration, monkeypatch):
    client, manager, _, headers = integration
    manager.consent_reader = Mock(side_effect=RuntimeError('synthetic database error'))
    assert manager.submit(1, photo()[0])['status'] == 'NO_CONSENT'
    assert not manager.jobs


@pytest.mark.parametrize('arrival,expected', [(daytime(8, 5), 'PRESENTE'), (daytime(8, 11), 'TARDANZA')])
def test_existing_attendance_rules_unchanged(monkeypatch, arrival, expected):
    from app.services import attendance_service as module

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2026, 10, 25, arrival.hour, arrival.minute)

    monkeypatch.setattr(module, 'datetime', FixedDateTime)
    session = SimpleNamespace(id=9, hora_inicio=daytime(8), tolerancia_minutos=10)
    repo = Mock()
    repo.find_active_session.return_value = session
    repo.exists_in_session.return_value = False

    def save(**kwargs):
        return SimpleNamespace(id=101, usuario_id=kwargs['usuario_id'], sesion_id=kwargs['sesion_id'],
                               fecha=kwargs['attendance_date'], hora=kwargs['attendance_time'],
                               confianza=kwargs['confidence'], liveness_score=kwargs['liveness_score'],
                               estado=kwargs['status'])

    repo.save.side_effect = save
    monkeypatch.setattr(module, 'attendance_repository', repo)
    result = module.attendance_service.register(object(), 1, .95, 12)
    assert result['attendance']['estado'] == expected
    repo.exists_in_session.return_value = True
    assert module.attendance_service.register(object(), 1, .95, 12)['status'] == 'ALREADY_REGISTERED'
    repo.find_active_session.return_value = None
    assert module.attendance_service.register(object(), 1, .95, 12)['status'] == 'NO_ACTIVE_SESSION'
    assert repo.save.call_count == 1


def test_real_sqlite_commit_survives_optional_failure(integration, monkeypatch):
    from sqlalchemy import text, select
    from app.db.models import Asistencia, Curso, SesionClase
    from app.services import attendance_service as module

    client, manager, sessions, headers = integration
    with sessions() as db:
        Curso.__table__.create(db.get_bind())
        SesionClase.__table__.create(db.get_bind())
        # SQLite needs INTEGER for autoincrement; production MySQL keeps BIGINT.
        db.execute(text('''CREATE TABLE asistencias (
            id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL, sesion_id INTEGER NOT NULL,
            fecha DATE NOT NULL, hora TIME NOT NULL, confianza NUMERIC NOT NULL,
            liveness_score NUMERIC NOT NULL, estado VARCHAR(30) NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
        db.add(Curso(id=9, codigo='SYNTHETIC', nombre='Test only', periodo='test'))
        db.add(SesionClase(id=9, curso_id=9, fecha=datetime(2026, 10, 25).date(),
                           hora_inicio=daytime(8), hora_fin=daytime(9),
                           tolerancia_minutos=10, estado='ACTIVA'))
        db.commit()

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2026, 10, 25, 8, 5)

    monkeypatch.setattr(module, 'datetime', FixedDateTime)
    monkeypatch.setattr(attendance.attendance_face_service, 'recognize',
                        lambda **kw: {'usuario_id': 1, 'confidence': .95})
    monkeypatch.setattr(attendance.liveness_service, 'check', lambda frame: {'is_live': True, 'score': 12})
    monkeypatch.setattr(manager, 'submit', Mock(side_effect=RuntimeError('synthetic model failure')))
    response = client.post('/api/attendance/camera/check-in', headers=headers(), json={'image': photo()[1]})
    assert response.json()['status'] == 'REGISTERED'
    assert response.json()['expression_analysis']['status'] == 'UNAVAILABLE'
    with sessions() as db:
        rows = db.execute(select(Asistencia)).scalars().all()
        assert len(rows) == 1 and rows[0].estado == 'PRESENTE'
    duplicate = client.post('/api/attendance/camera/check-in', headers=headers(), json={'image': photo()[1]})
    assert duplicate.json()['status'] == 'ALREADY_REGISTERED'
    assert manager.submit.call_count == 1


def test_model_delay_does_not_delay_attendance_response(integration, monkeypatch):
    client, manager, _, headers = integration
    accept(client, headers())
    manager.target = hang
    manager.job_ttl = 8
    monkeypatch.setattr(attendance.attendance_face_service, 'recognize',
                        lambda **kw: {'usuario_id': 1, 'confidence': .95})
    monkeypatch.setattr(attendance.liveness_service, 'check', lambda frame: {'is_live': True, 'score': 12})
    monkeypatch.setattr(attendance.attendance_service, 'register',
                        lambda **kw: {'success': True, 'status': 'REGISTERED'})
    before = time.monotonic()
    response = client.post('/api/attendance/camera/check-in', headers=headers(), json={'image': photo()[1]})
    assert time.monotonic() - before < 2
    assert response.json()['status'] == 'REGISTERED'
    assert response.json()['expression_analysis']['status'] == 'QUEUED'


def test_expiry_cleans_frames_even_when_consent_reader_is_slow():
    unblock = threading.Event()
    calls = [0]

    def reader(uid):
        calls[0] += 1
        if calls[0] > 1:
            unblock.wait(5)
        return 'revision'

    manager = ExpressionService(reader, enabled=True, target=hang, job_ttl=.2)
    try:
        job_id = manager.submit(1, photo()[0])['job_id']
        with manager.lock:
            job = manager.jobs[job_id]
        wait_for(lambda: not manager.jobs, seconds=2)
        assert job.frame is None
    finally:
        unblock.set()
        manager.close()


def test_ready_results_also_have_a_bounded_capacity():
    manager = ExpressionService(lambda uid: 'revision', enabled=True, target=ready,
                                capacity=1, max_results=1, job_ttl=8)
    try:
        job_id = manager.submit(1, photo()[0])['job_id']
        wait_for(lambda: (value if (value := manager.get(1, job_id)) and value['status'] == 'READY' else None))
        assert manager.submit(2, photo()[0])['status'] == 'BUSY'
        manager.revoke(1)
        assert manager.submit(2, photo()[0])['status'] == 'QUEUED'
    finally:
        manager.close()


def test_original_flask_interface_still_works_without_camera():
    root = Path(__file__).resolve().parents[3]
    script = '''
import sys
from unittest.mock import patch
sys.path.insert(0, 'integraciones/emoscan')
with patch('cv2.VideoCapture', side_effect=AssertionError('No second camera')):
    import app
    client = app.app.test_client()
    assert client.get('/').status_code == 200
    health = client.get('/health').get_json()
    assert health['onnx_loaded'] is True
    assert health['camera_running'] is False
'''
    result = subprocess.run([sys.executable, '-c', script], cwd=root,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
