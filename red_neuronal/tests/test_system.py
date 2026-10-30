"""SQLAlchemy en SQLite RAM: NO se confunde con una prueba MySQL real."""
from datetime import datetime,timedelta,time
import secrets
from types import SimpleNamespace
import numpy as np
import pytest
from sqlalchemy import create_engine,event,select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.database import Base,get_db
from app.db.models import Usuario,Profesor,Estudiante,Curso,AsignacionProfesor,Matricula,SesionClase,Asistencia,Evaluacion,Nota
from app.core.config import settings
from app.core.security import create_access_token,hash_password
from app.parte6 import create_app
from app.services import parte6_service as service
from red_neuronal.system_features import system_features
from red_neuronal.prepare import features
from red_neuronal.api import get_predictor

NOW=datetime(2025,1,22,12)
TEST_PASSWORD_HASH=hash_password('solo-fixture-local')

def seed(db):
    for id,role in [(1,'profesor'),(2,'profesor'),(3,'estudiante'),(4,'estudiante'),(5,'profesor'),(6,'admin')]:
        db.add(Usuario(id=id,username='fixture-'+str(id),email=f'fixture-{id}@example.invalid',password_hash=TEST_PASSWORD_HASH,nombres='Perfil de prueba',apellidos=str(id),rol=role,estado='inactivo' if id==5 else 'activo'))
    db.add_all([Profesor(id=1,usuario_id=1),Profesor(id=2,usuario_id=2),Estudiante(id=1,usuario_id=3,codigo='TEST-1'),Estudiante(id=2,usuario_id=4,codigo='TEST-2'),Curso(id=1,codigo='DEMO-1',nombre='Curso de prueba',periodo='2025',activo=True),Curso(id=2,codigo='DEMO-2',nombre='Otro curso',periodo='2025',activo=True)])
    db.flush()
    db.add_all([AsignacionProfesor(id=1,curso_id=1,profesor_id=1),AsignacionProfesor(id=2,curso_id=2,profesor_id=2),Matricula(id=1,curso_id=1,estudiante_id=1,matriculado_en=datetime(2025,1,1)),Matricula(id=2,curso_id=2,estudiante_id=2,matriculado_en=datetime(2025,1,1))])
    for i in range(8):
        stamp=datetime(2025,1,2,8)+timedelta(days=i*3)
        db.add(SesionClase(id=i+1,curso_id=1,fecha=stamp.date(),hora_inicio=time(8),hora_fin=time(10),estado='ACTIVA',fecha_registro=datetime(2025,1,1)))
        if i<7:db.add(Asistencia(id=i+1,usuario_id=3,sesion_id=i+1,fecha=stamp.date(),hora=time(8,2),estado=['PRESENTE','TARDANZA','AUSENTE'][i%3],confianza=0,liveness_score=0,fecha_registro=stamp+timedelta(minutes=2)))
    db.add_all([Evaluacion(id=1,curso_id=1,nombre='Prueba',creado_en=datetime(2025,1,3)),Evaluacion(id=2,curso_id=1,nombre='Nota futura',creado_en=datetime(2025,1,3)),Evaluacion(id=3,curso_id=2,nombre='No autorizada',creado_en=datetime(2025,1,3))])
    db.flush()
    db.add_all([Nota(id=1,evaluacion_id=1,estudiante_id=1,nota=14,estado='calificado',registrada_en=datetime(2025,1,10)),Nota(id=2,evaluacion_id=2,estudiante_id=1,nota=20,estado='calificado',registrada_en=datetime(2025,1,23)),Nota(id=3,evaluacion_id=3,estudiante_id=2,nota=0,estado='calificado',registrada_en=datetime(2025,1,10))]);db.commit()

@pytest.fixture
def env(monkeypatch):
    engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:seed(db)
    app=create_app()
    def session():
        with Session(engine,autoflush=False) as db:yield db
    app.dependency_overrides[get_db]=session
    monkeypatch.setattr(settings,'JWT_SECRET_KEY',secrets.token_urlsafe(48))
    monkeypatch.setattr(service,'now_local',lambda:NOW)
    client=TestClient(app);headers={'Authorization':'Bearer '+create_access_token(1,'profesor')}
    yield SimpleNamespace(client=client,engine=engine,headers=headers)
    engine.dispose()

PAYLOAD=dict(curso_id=1,estudiante_id=1,sesion_id=8)

def test_courses_scoped(env):
    r=env.client.get('/api/parte6/system/courses',headers=env.headers);assert r.status_code==200 and [x['id'] for x in r.json()]==[1]
    assert env.client.get('/api/parte6/system/courses/2/students',headers=env.headers).status_code==404
    s=env.client.get('/api/parte6/system/courses/1/students',headers=env.headers).json();assert len(s)==1 and s[0]['id']==1
    assert set(s[0])=={'id','nombre','codigo'}

@pytest.mark.parametrize('user,role,expected',[(None,None,401),(3,'profesor',403),(2,'profesor',404),(5,'profesor',401),(6,'profesor',403)])
def test_jwt_and_authorization(env,user,role,expected):
    headers={} if user is None else {'Authorization':'Bearer '+create_access_token(user,role)}
    assert env.client.post('/api/parte6/system/context',headers=headers,json=PAYLOAD).status_code==expected

def test_idor_student(env):
    assert env.client.post('/api/parte6/system/context',headers=env.headers,json=dict(PAYLOAD,estudiante_id=2)).status_code==404

def test_exact_features_and_real_inference(env):
    context=env.client.post('/api/parte6/system/context',headers=env.headers,json=PAYLOAD);assert context.status_code==200
    data=context.json();assert data['ready'] and len(data['features'])==9 and len(data['history'])==7
    assert data['features']['promedio_previo']==14 and data['grades_count']==1
    assert data['features']['asistencia_30d']==pytest.approx(5/7)
    prediction=env.client.post('/api/parte6/system/predict',headers=env.headers,json=PAYLOAD)
    assert prediction.status_code==200
    expected=get_predictor().predict_features(data['features']);assert prediction.json()['probabilidad']==pytest.approx(expected['probabilidad'])
    assert prediction.json()['experimental'] and prediction.json()['training_origin']=='sintetico'
    assert 'prediccion' not in prediction.json() # No etiqueta académica automática.

def test_same_training_transform():
    model=get_predictor();ex=model.report['examples'][0]
    history=[dict(session_at=h['session_at'],estado=h['estado']) for h in ex['history']]
    grades=[dict(nota=h['nota'],available_at=h['nota_disponible_at']) for h in ex['history']]
    target=datetime.fromisoformat(ex['session_at'])
    actual=system_features(history,grades,target,target-timedelta(hours=1))
    expected=features(ex['history'],target)
    np.testing.assert_allclose(list(actual.values()),list(expected.values()),atol=1e-12)

@pytest.mark.parametrize('mutation',['missing','duplicate','invalid','missing_date','future_date','bad_grade','grade_date','enrollment_date'])
def test_insufficient_and_inconsistent_block(env,mutation):
    with Session(env.engine) as db:
        if mutation=='missing':db.delete(db.get(Asistencia,1))
        if mutation=='duplicate':
            a=db.get(Asistencia,1);db.add(Asistencia(id=99,usuario_id=a.usuario_id,sesion_id=a.sesion_id,fecha=a.fecha,hora=a.hora,estado=a.estado,confianza=0,liveness_score=0,fecha_registro=a.fecha_registro))
        if mutation=='invalid':db.get(Asistencia,1).estado='DESCONOCIDO'
        if mutation=='missing_date':db.get(Asistencia,1).fecha_registro=None
        if mutation=='future_date':db.get(Asistencia,1).fecha_registro=NOW+timedelta(days=1)
        if mutation=='bad_grade':
            db.get(Nota,1).nota=21;db.get(Nota,1).registrada_en=datetime(2025,1,11)
        if mutation=='grade_date':db.get(Nota,1).registrada_en=None
        if mutation=='enrollment_date':db.get(Matricula,1).matriculado_en=None
        db.commit()
    context=env.client.post('/api/parte6/system/context',headers=env.headers,json=PAYLOAD).json()
    assert not context['ready'] and context['blockers']
    assert env.client.post('/api/parte6/system/predict',headers=env.headers,json=PAYLOAD).status_code==409

def test_no_future_attendance_or_grade(env):
    before=env.client.post('/api/parte6/system/context',headers=env.headers,json=PAYLOAD).json()['features']
    with Session(env.engine) as db:
        db.get(Nota,2).nota=1
        db.add(Asistencia(id=98,usuario_id=3,sesion_id=8,fecha=datetime(2025,1,23).date(),hora=time(8),estado='AUSENTE',confianza=0,liveness_score=0,fecha_registro=datetime(2025,1,23,8)));db.commit()
    after=env.client.post('/api/parte6/system/context',headers=env.headers,json=PAYLOAD).json()['features']
    assert before==after

@pytest.mark.parametrize('id,value',[(1,0),(2,-1),(3,'x')])
def test_ids_and_extra_fields(env,id,value):
    payload=dict(PAYLOAD);payload[['curso_id','estudiante_id','sesion_id'][id-1]]=value
    assert env.client.post('/api/parte6/system/context',headers=env.headers,json=payload).status_code==422
    assert env.client.post('/api/parte6/system/predict',headers=env.headers,json=dict(PAYLOAD,features={})).status_code==422

def test_only_next_session(env):
    assert env.client.get('/api/parte6/system/courses/1/sessions',headers=env.headers).json()[0]['id']==8
    assert env.client.post('/api/parte6/system/context',headers=env.headers,json=dict(PAYLOAD,sesion_id=1)).status_code==409

def test_login_reuses_hash_and_jwt_readonly(env):
    response=env.client.post('/api/parte6/auth/login',json=dict(identificador='fixture-1',password='solo-fixture-local'))
    assert response.status_code==200
    assert env.client.get('/api/parte6/system/courses',headers={'Authorization':'Bearer '+response.json()['access_token']}).status_code==200
    assert env.client.post('/api/parte6/auth/login',json=dict(identificador='fixture-1',password='incorrecta')).status_code==401

def test_no_database_writes(env):
    sql=[]
    def record(conn,cursor,statement,params,context,many):sql.append(statement)
    event.listen(env.engine,'before_cursor_execute',record)
    try:
        assert env.client.post('/api/parte6/system/predict',headers=env.headers,json=PAYLOAD).status_code==200
        assert all(s.lstrip().upper().startswith('SELECT') for s in sql)
    finally:event.remove(env.engine,'before_cursor_execute',record)

def test_guard_refuses_default_configuration(monkeypatch):
    from app.services.parte6_database import check_configuration
    from fastapi import HTTPException
    monkeypatch.delenv('PARTE6_ALLOW_DEV_DB',raising=False)
    with pytest.raises(HTTPException) as e:check_configuration()
    assert e.value.status_code==503

def test_demo_cookie_cannot_read_system(env):
    assert env.client.post('/api/parte6/demo/session').status_code==200
    assert env.client.get('/api/parte6/report').status_code==200
    assert env.client.get('/api/parte6/system/courses').status_code==401

def test_production_connection_is_refused(monkeypatch):
    from app.services import parte6_database as database
    from fastapi import HTTPException
    monkeypatch.setenv('PARTE6_ALLOW_DEV_DB','1')
    class ForbiddenEngine:
        url=SimpleNamespace(host='production.example.invalid',database='monitor_asistencia')
        def connect(self):raise AssertionError('Must not connect to a production host')
    monkeypatch.setattr(database,'engine',ForbiddenEngine())
    with pytest.raises(HTTPException) as error:database.check_configuration()
    assert error.value.status_code==503

def test_invalid_and_expired_jwt(env):
    assert env.client.get('/api/parte6/system/courses',headers={'Authorization':'Bearer invalid'}).status_code==401
    expired=create_access_token(1,'profesor',expires_minutes=-1)
    assert env.client.get('/api/parte6/system/courses',headers={'Authorization':'Bearer '+expired}).status_code==401

def test_default_app_is_pending_without_database():
    app=create_app();client=TestClient(app)
    response=client.get('/api/parte6/system/status')
    assert response.status_code==200 and response.json()['configured'] is False
    assert response.json()['state']=='pending_integration'
    assert 'Pendiente de integración' in response.json()['message']
