"""Servidor local sintético, con sesión de demostración explícita y cookies HttpOnly."""
import secrets
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,Response
from fastapi.staticfiles import StaticFiles
from .api import create_router

ROOT=Path(__file__).resolve().parents[1]

def create_demo_app():
    app=FastAPI(title='Parte 6 · demostración sintética local')
    session=secrets.token_urlsafe(32)
    def local(request:Request):
        if request.client.host not in {'127.0.0.1','::1','testclient'}: raise HTTPException(403,'Demostración disponible solo en loopback.')
        if request.headers.get('host','').split(':')[0] not in {'127.0.0.1','localhost','testserver'}: raise HTTPException(403,'Host no permitido.')
    def user(request:Request):
        local(request)
        if not secrets.compare_digest(request.cookies.get('parte6_demo',''),session): raise HTTPException(401,'Activa la sesión sintética de demostración.')
        return dict(rol='profesor')
    @app.post('/api/parte6/demo/session')
    def start(request:Request,response:Response):
        local(request)
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'): raise HTTPException(403,'Origen no permitido.')
        response.set_cookie('parte6_demo',session,httponly=True,samesite='strict',max_age=3600)
        return dict(origen='sintetico',rol='profesor',modo='Demostración local; no autentica cuentas reales.')
    @app.get('/api/parte6/mode')
    def mode(): return dict(demo=True)
    app.include_router(create_router(user))
    app.mount('/',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')
    return app

app=create_demo_app()
