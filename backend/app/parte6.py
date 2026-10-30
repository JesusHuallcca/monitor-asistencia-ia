"""Aplicación Parte 6 integrada, sin lifespan de main ni escrituras en MySQL."""
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,Request,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select,text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel,Field,ConfigDict
from app.api.deps import get_current_user
from app.core.security import verify_password,create_access_token,decode_access_token
from app.db.database import get_db
from app.db.models import Usuario
from app.services.parte6_database import read_only_db,check_configuration
from app.api.parte6_system import router
from red_neuronal.api import create_router

class Login(BaseModel):
    model_config=ConfigDict(extra='forbid')
    identificador:str=Field(min_length=1,max_length=120)
    password:str=Field(min_length=1,max_length=128)

def create_app(configuration_check=check_configuration,database_kind="mysql",integration_ready=False):
    import secrets
    demo_session=secrets.token_urlsafe(32)
    app=FastAPI(title='Parte 6 — integración académica experimental')
    def pending_db():
        raise HTTPException(503,'Pendiente de integración: el responsable del backend debe conectar y verificar su API académica.')
        yield
    app.dependency_overrides[get_db]=read_only_db if integration_ready else pending_db
    from fastapi.security import HTTPBearer
    from threading import Lock
    import time
    attempts={};attempt_lock=Lock()
    def required_credentials(credentials=Depends(HTTPBearer(auto_error=False))):
        if credentials is None:raise HTTPException(401,'No autenticado.')
        payload=decode_access_token(credentials.credentials)
        if payload is None or not str(payload.get('sub','')).isdigit() or int(payload['sub'])<=0:raise HTTPException(401,'Token inválido o vencido.')
        return credentials
    def safe_user(credentials=Depends(required_credentials),db=Depends(get_db)):
        try:return get_current_user(credentials,db)
        except (ValueError,TypeError):raise HTTPException(401,'Token inválido o vencido.')
    app.dependency_overrides[get_current_user]=safe_user
    app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:8001','http://localhost:8001'],allow_credentials=True,allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type'])
    @app.exception_handler(SQLAlchemyError)
    async def sql_error(request,error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503,content={'detail':'No se pudo consultar la base de desarrollo. Revisa su configuración sin compartir credenciales.'})
    @app.get('/api/parte6/mode')
    def mode():return dict(demo=True,system=True,training_origin='sintetico',database_kind=database_kind)
    @app.get('/api/parte6/system/status')
    def status():
        if not integration_ready:return dict(configured=False,state='pending_integration',message='Pendiente de integración: no hay una API MySQL verificada. La demostración sintética está disponible.')
        try:configuration_check();return dict(configured=True,state='ready',message='Adaptador académico de prueba habilitado; autentícate para consultar.')
        except HTTPException as exc:return dict(configured=False,message=exc.detail)
    @app.post('/api/parte6/auth/login')
    def login(payload:Login,request:Request,db=Depends(get_db)):
        key=request.client.host if request.client else 'unknown'
        now=__import__('time').monotonic()
        with attempt_lock:
            expired=[k for k,v in attempts.items() if now-v[0]>60]
            for k in expired:attempts.pop(k,None)
            if len(attempts)>=1000 and key not in attempts:raise HTTPException(429,'Intenta nuevamente en un minuto.')
            start,count=attempts.get(key,(now,0))
            if count>=8:raise HTTPException(429,'Demasiados intentos; espera un minuto.')
            attempts[key]=(start,count+1)
        # Reutiliza el hash y la firma JWT del proyecto. Este acceso específico es solo lectura.
        from datetime import datetime,timezone
        from sqlalchemy import or_
        user=db.scalar(select(Usuario).where(or_(Usuario.username==payload.identificador.strip(),Usuario.email==payload.identificador.strip())))
        if user is None or user.estado!='activo' or not verify_password(payload.password,user.password_hash):raise HTTPException(401,'Credenciales inválidas o cuenta no disponible.')
        if user.bloqueado_hasta and user.bloqueado_hasta>datetime.now(timezone.utc).replace(tzinfo=None):raise HTTPException(423,'Cuenta temporalmente bloqueada.')
        if user.rol!='profesor':raise HTTPException(403,'Esta sección requiere el rol profesor.')
        return dict(access_token=create_access_token(user.id,user.rol,expires_minutes=30),token_type='bearer',rol=user.rol,nombre=user.nombres)
    @app.get('/api/parte6/system/health')
    def health(user=Depends(get_current_user),db=Depends(get_db)):
        if user.rol!='profesor':raise HTTPException(403,'Solo profesores.')
        db.execute(text('SELECT 1'))
        return dict(status='ok',database='desarrollo',read_only=True)
    def synthetic_user(request:Request):
        if request.client.host in {'127.0.0.1','::1','testclient'} and secrets.compare_digest(request.cookies.get('parte6_demo_integrated',''),demo_session):return dict(rol='profesor')
        authorization=request.headers.get('authorization','')
        if authorization.startswith('Bearer ') and authorization[7:].strip():
            from fastapi.security import HTTPAuthorizationCredentials
            if not integration_ready:raise HTTPException(401,'Activa la demostración sintética. MySQL está pendiente de integración.')
            iterator=read_only_db();db=next(iterator)
            try:return get_current_user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=authorization[7:]),db)
            except (ValueError,TypeError):raise HTTPException(401,'Token inválido.')
            finally:iterator.close()
        local=request.client.host in {'127.0.0.1','::1','testclient'}
        if local and secrets.compare_digest(request.cookies.get('parte6_demo_integrated',''),demo_session):return dict(rol='profesor')
        raise HTTPException(401,'Inicia sesión como profesor o activa la demostración local.')
    @app.post('/api/parte6/demo/session')
    def demo_login(request:Request,response:Response):
        if request.client.host not in {'127.0.0.1','::1','testclient'} or request.headers.get('host','').split(':')[0] not in {'127.0.0.1','localhost','testserver'}:raise HTTPException(403,'Demostración solo en loopback.')
        if request.headers.get('origin') and request.headers['origin'] not in {str(request.base_url).rstrip('/'),'http://127.0.0.1:8001','http://localhost:8001'}:raise HTTPException(403,'Origen no permitido.')
        response.set_cookie('parte6_demo_integrated',demo_session,httponly=True,samesite='strict',max_age=3600)
        return dict(origen='sintetico',modo='Solo demostración: esta sesión no autoriza consultas MySQL.')
    app.include_router(create_router(synthetic_user));app.include_router(router)
    app.mount('/',StaticFiles(directory=Path(__file__).resolve().parents[2]/'frontend',html=True),name='frontend')
    return app

app=create_app()
