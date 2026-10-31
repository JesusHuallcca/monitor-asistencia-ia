"""Demo local del MISMO chatbot. SQLite RAM, Gemini desactivado y MySQL bloqueado.
Ejecutar desde la raíz: python -m uvicorn parte7_demo:app --app-dir backend --host 127.0.0.1 --port 8017
"""
import os
import secrets
import sys
from pathlib import Path
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from threading import Lock
from contextlib import asynccontextmanager

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
# Solo el proceso de demostración; no se editan .env ni configuraciones del servidor.
os.environ.update(DB_HOST="invalid.test",DB_NAME="parte7_synthetic_memory",DB_USER="demo",DB_PASSWORD="unused",
                  JWT_SECRET_KEY=secrets.token_urlsafe(48),EMOSCAN_ENABLED="false",CHATBOT_DEMO_MODE="true")
os.environ.pop("GEMINI_API_KEY",None)
os.environ.pop("GEMINI_MODEL",None)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import database

@event.listens_for(database.engine,"do_connect")
def reject_mysql(*args,**kwargs):
    raise RuntimeError("La demostración no puede conectarse a MySQL.")

from app.db.models import Usuario,Profesor,Estudiante,Curso,AsignacionProfesor,Matricula,SesionClase,Asistencia,Evaluacion
from app.db.proactive_models import ProactiveBase
from app.services.chatbot_proactive_scheduler import make_scheduler
from app.api.chatbot import router
from app.api.deps import get_current_user
from app.core.security import create_access_token

engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
sessions=sessionmaker(bind=engine,expire_on_commit=False)
demo_db_guard=Lock()

def seed():
    database.Base.metadata.create_all(engine)
    ProactiveBase.metadata.create_all(engine) # SOLO SQLite RAM sintetico, nunca MySQL.
    with sessions() as db:
        for uid,role,name in [(1,"profesor","Docente"),(2,"estudiante","Ana"),(3,"estudiante","Luis"),(4,"estudiante","Externo")]:
            db.add(Usuario(id=uid,username=f"demo{uid}",email=f"demo{uid}@example.test",password_hash="no-password-demo",nombres=name,apellidos="Sintético",rol=role,estado="activo"))
        db.add(Profesor(id=1,usuario_id=1))
        db.add_all([Estudiante(id=i,usuario_id=i+1,codigo=f"DEMO{i}") for i in (1,2,3)])
        for cid,name in [(1,"Matemática"),(2,"Programación"),(3,"Curso no asignado")]:
            db.add(Curso(id=cid,codigo=f"DEM{cid}",nombre=name,periodo="DEMO",activo=True))
        db.flush()
        db.add_all([AsignacionProfesor(profesor_id=1,curso_id=cid) for cid in (1,2)])
        db.add_all([Matricula(curso_id=c,estudiante_id=e) for c,e in [(1,1),(2,1),(2,2),(3,3)]])
        year=date.today().year
        for sid,(cid,day) in enumerate([(c,d) for c in (1,2,3) for d in (3,9,14,20)],1):
            db.add(SesionClase(id=sid,curso_id=cid,fecha=date(year,10,day),hora_inicio=time(9),hora_fin=time(10)))
            db.flush()
            state="TARDANZA" if cid==2 or day==3 else "PRESENTE"
            uid=4 if cid==3 else 2
            db.add(Asistencia(id=sid,usuario_id=uid,sesion_id=sid,fecha=date(year,10,day),hora=time(9),confianza=0,liveness_score=0,estado=state))
        # Observaciones de septiembre adicionales, siempre ficticias y reproducibles.
        for sid,(cid,day,state) in enumerate([(c,d,state) for c in (1,2) for d,state in [(3,"PRESENTE"),(9,"TARDE"),(14,"AUSENTE"),(20,"PRESENTE")]],101):
            db.add(SesionClase(id=sid,curso_id=cid,fecha=date(year,9,day),hora_inicio=time(9),hora_fin=time(10)))
            db.flush()
            db.add(Asistencia(id=sid,usuario_id=2,sesion_id=sid,fecha=date(year,9,day),hora=time(9),confianza=0,liveness_score=0,estado=state))
        tomorrow=datetime.now(ZoneInfo("America/Lima"))+timedelta(days=1)
        db.add(SesionClase(id=500,curso_id=1,fecha=tomorrow.date(),hora_inicio=time(9),hora_fin=time(10)))
        db.add(Evaluacion(id=500,curso_id=1,nombre="Evaluación sintética con fecha",fecha_vencimiento=tomorrow.date()+timedelta(days=2)))
        db.commit()

@asynccontextmanager
async def lifespan(app):
    seed()
    scheduler=make_scheduler(sessions,background=True,seconds=2,guard=demo_db_guard)
    app.state.proactive_scheduler=scheduler
    scheduler.start()
    try:yield
    finally:
        scheduler.shutdown(wait=True)
        engine.dispose()

app=FastAPI(title="Parte 7 · demostración sintética local",lifespan=lifespan)

@app.middleware("http")
async def local_only(request,call_next):
    if request.client and request.client.host not in {"127.0.0.1","::1","testclient"}:
        return JSONResponse({"detail":"Demostración disponible solo en loopback."},status_code=403)
    response=await call_next(request)
    response.headers["Cache-Control"]="no-store"
    return response

def get_db():
    with demo_db_guard:
        with sessions() as db:yield db
app.dependency_overrides[database.get_db]=get_db
app.include_router(router)

@app.get("/api/health")
def health(): return {"status":"ok","demo":True,"storage":"sqlite-memory","mysql":"blocked","gemini":"disabled"}

@app.get("/api/users/me")
def me(user=Depends(get_current_user)):
    return {"id":user.id,"rol":user.rol,"nombres":user.nombres,"apellidos":user.apellidos}

@app.post("/api/parte7-demo/session/{role}")
def demo_session(role:str):
    if role not in {"profesor","estudiante"}: raise HTTPException(404,"Rol sintético no disponible.")
    uid=1 if role=="profesor" else 2
    return {"access_token":create_access_token(uid,role),"rol":role,"nombre":"Cuenta sintética"}

@app.get("/frontend/js/config.js")
def demo_config():
    # Solo esta respuesta de la demo. El archivo de configuración original no cambia.
    return Response("const API_URL = window.location.origin; document.addEventListener('DOMContentLoaded',()=>{const label=document.querySelector('.subtitulo-pagina');if(label)label.textContent='Demostración sintética · SQLite en memoria · sin MySQL';});",media_type="text/javascript")

@app.exception_handler(FileNotFoundError)
def missing_model(request,error):
    return JSONResponse({"detail":"Modelo no disponible en esta demostración; no se entrenan modelos al consultar."},status_code=503)

@app.get("/",response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Parte 7 · Demo sintética</title>
    <style>body{font:16px system-ui;background:#edf4ff;color:#12345b;margin:0;padding:5vw}main{max-width:700px;margin:auto;background:white;padding:30px;border-radius:18px}button{background:#245dde;color:white;border:0;border-radius:9px;padding:14px;margin:8px;cursor:pointer}p{line-height:1.6}</style>
    <main><h1>Monitor IA Assistant · Parte 7</h1><p><strong>Demostración exclusivamente sintética.</strong> SQLite en memoria; MySQL bloqueado y Gemini desactivado. Las cuentas siguientes no acceden a estudiantes reales.</p>
    <button data-role="profesor">Probar como profesor</button><button data-role="estudiante">Probar como estudiante</button><p>Prueba: Hola → ¿Cuáles son mis cursos? → ¿Y cuál tiene más tardanzas? → Muéstrame los registros de octubre. También: «Genera un reporte de asistencia», «Compara septiembre y octubre», «El mismo reporte en PDF».</p><p>La voz está apagada inicialmente. Activa «Leer respuestas» para escuchar; el micrófono requiere tu confirmación y el permiso del navegador.</p><p id="status" role="status"></p></main>
    <script>document.querySelectorAll('button').forEach(button=>button.onclick=async()=>{try{const role=button.dataset.role;const response=await fetch('/api/parte7-demo/session/'+role,{method:'POST'});if(!response.ok)throw Error('No se pudo iniciar la cuenta sintética.');const data=await response.json();for(const key of ['token','rol','nombre']){localStorage.removeItem(key);sessionStorage.removeItem(key);}sessionStorage.setItem('token',data.access_token);sessionStorage.setItem('rol',data.rol);sessionStorage.setItem('nombre',data.nombre);location.href='/frontend/'+role+'/ia.html';}catch(error){document.querySelector('#status').textContent=error.message;}});</script></html>"""

app.mount("/frontend",StaticFiles(directory=ROOT/"frontend"),name="frontend")
