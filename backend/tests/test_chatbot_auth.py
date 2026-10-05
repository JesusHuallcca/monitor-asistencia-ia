from app.db.database import get_db
from app.db.models import Usuario

def test_existing_logins_and_me(client,headers):
    for role in ['admin','profesor','estudiante']:
        r=client.get('/api/users/me',headers=headers(role))
        assert r.status_code==200 and r.json()['rol']==role
    assert client.post('/api/auth/login',json={'identificador':'admin','password':'Demo2026!'}).status_code==401

def test_superadmin(client):
    with next(client.app.dependency_overrides[get_db]()) as db:
        user=db.get(Usuario,1);user.rol='superadmin';db.commit()
    r=client.post('/api/auth/admin/login',json={'identificador':'admin','password':'Demo2026!'})
    assert r.status_code==200 and r.json()['rol']=='superadmin'
    h={'Authorization':'Bearer '+r.json()['access_token']}
    assert len(client.get('/api/chatbot/context',headers=h).json()['courses'])==3
    assert client.post('/api/chatbot/message',headers=h,json={'message':'Métricas del modelo'}).status_code==200

def test_reuses_course_permissions(client,headers):
    h=headers('profesor')
    visible={c['id'] for c in client.get('/api/cursos',headers=h).json()}
    chatbot={c['id'] for c in client.get('/api/chatbot/context',headers=h).json()['courses']}
    assert chatbot==visible=={1,2}
