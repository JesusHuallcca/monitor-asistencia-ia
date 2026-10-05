import pytest
from sqlalchemy import select
from app.db.models import ChatHistorial

def ask(client,headers,account_role,question,**kwargs):
    return client.post('/api/chatbot/message',headers=headers(account_role),json={'message':question,**kwargs})

def test_auth_required(client):
    assert client.post('/api/chatbot/message',json={'message':'Mis cursos'}).status_code==401
    assert client.post('/api/auth/login',json={'correo':'estudiante@demo.local','password':'incorrecta'}).status_code==401

def test_scope_context(client,headers):
    for role,course_count,student_count in [('estudiante',2,1),('profesor',2,2),('admin',3,3)]:
        r=client.get('/api/chatbot/context',headers=headers(role))
        assert r.status_code==200
        assert len(r.json()['courses'])==course_count
        assert len(r.json()['students'])==student_count

@pytest.mark.parametrize('role,target',[('estudiante',2),('profesor',3)])
def test_forbidden_student(client,headers,role,target):
    r=ask(client,headers,role,'Ver historial',student_id=target)
    assert r.status_code==403

@pytest.mark.parametrize('role,name',[('estudiante','Luis'),('estudiante','María'),('profesor','María')])
def test_forbidden_name(client,headers,role,name):
    r=ask(client,headers,role,'Dame la asistencia de '+name)
    assert r.status_code==403

def test_forbidden_course_and_forged_role(client,headers):
    assert ask(client,headers,'estudiante','Asistencia',course_id=3).status_code==403
    assert ask(client,headers,'estudiante','Mis cursos',role='ADMIN').status_code==422

def test_student_data_only(client,headers):
    data=ask(client,headers,'estudiante','Mi historial').json()
    assert len(data['data'])==16
    assert {r['estudiante'] for r in data['data']}=={'Ana García'}

def test_tardy_intent_priority(client,headers):
    data=ask(client,headers,'profesor','Ver historial de tardanzas').json()
    assert data['intent']=='LATE_STUDENTS'
    assert data['data'] and all(row['estado']=='TARDANZA' for row in data['data'])

def test_statistics_and_filter(client,headers):
    data=ask(client,headers,'estudiante','Resumen de asistencia').json()['data']
    assert data=={'registros':16,'presentes':6,'tardanzas':5,'ausentes':5,'porcentaje_asistencia':68.75}
    assert ask(client,headers,'profesor','Resumen de asistencia',course_id=2).json()['data']['registros']==8

def test_today_and_voice(client,headers):
    data=ask(client,headers,'profesor','Cuántos faltaron hoy',source='voice').json()
    assert data['intent']=='ATTENDANCE_TODAY'
    assert len(data['data'])==3
    assert '1 ausencias' in data['reply']

def test_no_invented_predictions(client,headers):
    data=ask(client,headers,'profesor','Cuál es el riesgo de falta de Ana').json()
    assert data['data']==[] and 'No hay predicciones' in data['reply']
    assert ask(client,headers,'profesor','Métricas del modelo').status_code==403
    assert ask(client,headers,'admin','Métricas del modelo').json()['data']==[]

def test_sql_input_does_not_execute(client,headers):
    assert ask(client,headers,'admin',"DROP TABLE usuarios; SELECT * FROM usuarios").status_code==200
    assert client.post('/api/auth/login',json={'correo':'admin@demo.local','password':'Demo2026!'}).status_code==200

def test_history_isolation_and_clear(client,headers):
    ask(client,headers,'estudiante','Mis cursos')
    assert len(client.get('/api/chatbot/history',headers=headers('estudiante')).json())==1
    assert client.get('/api/chatbot/history',headers=headers('profesor')).json()==[]
    assert client.delete('/api/chatbot/history',headers=headers('profesor')).status_code==200
    assert len(client.get('/api/chatbot/history',headers=headers('estudiante')).json())==1
    client.delete('/api/chatbot/history',headers=headers('estudiante'))
    assert client.get('/api/chatbot/history',headers=headers('estudiante')).json()==[]

@pytest.mark.parametrize('question',['',' '*5,'x'*2001])
def test_invalid_question(client,headers,question):
    assert ask(client,headers,'estudiante',question).status_code==422

def test_static_pages(client):
    for page in ['login.html','admin/dashboard.html','profesor/dashboard.html','estudiante/dashboard.html','components/chatbot.js','assets/css/chatbot.css']:
        assert client.get('/frontend/'+page).status_code==200
