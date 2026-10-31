"""Demostración reproducible, SQLite RAM, reloj acelerado y APScheduler REAL.
No navegador, MySQL ni comunicaciones externas. No modifica el servidor en 8017.
"""
from pathlib import Path
from datetime import datetime,date,time,timedelta
from threading import Event
import json
from io import BytesIO
from fastapi.testclient import TestClient
from apscheduler.events import EVENT_JOB_EXECUTED
from openpyxl import load_workbook
from pypdf import PdfReader
from docx import Document
from parte7_demo import app,sessions,demo_db_guard,ROOT
from app.db.models import SesionClase,Asistencia
from app.services import chatbot_proactive as service

def main():
    clock=[datetime(2026,11,2,13)] # lunes, 08:00 Lima; reloj lógico de prueba explícito
    original=service.utcnow;service.utcnow=lambda:clock[0]
    target=ROOT/"docs"/"parte7"/"ejemplos";target.mkdir(parents=True,exist_ok=True)
    try:
        with TestClient(app) as client:
            token=client.post("/api/parte7-demo/session/profesor").json()["access_token"]
            headers={"Authorization":"Bearer "+token}
            with demo_db_guard:
                with sessions() as db:
                    db.get(SesionClase,500).fecha=date(2026,11,3)
                    for sid,day,state in [(900,27,"PRESENTE"),(901,28,"AUSENTE")]:
                        db.add(SesionClase(id=sid,curso_id=1,fecha=date(2026,10,day),hora_inicio=time(9),hora_fin=time(10)))
                        db.flush()
                        db.add(Asistencia(id=sid,usuario_id=2,sesion_id=sid,fecha=date(2026,10,day),hora=time(9),confianza=0,liveness_score=0,estado=state))
                    db.commit()
            def plan(spec):
                r=client.post("/api/chatbot/proactive/actions",headers=headers,json=spec);assert r.status_code==200,r.text
                action=r.json()
                active=client.post("/api/chatbot/proactive/actions/"+action["id"]+"/transition",headers=headers,json={"version":action["version"],"operation":"activate","confirmed":True})
                assert active.status_code==200,active.text
                return active.json()
            reminder=plan({"kind":"next_class","course_id":1,"source_id":500,"timezone":"America/Lima","frequency":"once","reminder_minutes":30})
            report=plan({"kind":"scheduled_report","course_id":1,"timezone":"America/Lima","frequency":"weekly","weekday":0,"local_time":"08:01"})
            executed=Event()
            app.state.proactive_scheduler.add_listener(lambda event:executed.set(),EVENT_JOB_EXECUTED)
            def advance(action):
                executed.clear()
                clock[0]=datetime.fromisoformat(action["next_run"]).replace(tzinfo=None)+timedelta(seconds=1)
                # No petición a la API durante esta espera: el scheduler servidor ejecuta.
                assert executed.wait(8),"El planificador no ejecutó a tiempo."
            advance(report)
            notifications=client.get("/api/chatbot/proactive/notifications",headers=headers).json()
            notification=next(n for n in notifications if n["has_report"])
            preview=client.post("/api/chatbot/proactive/notifications/"+notification["id"]+"/report",headers=headers)
            assert preview.status_code==200,preview.text
            value=preview.json()
            assert value["report_rows"]==2 and value["metrics"]["asistencia_pct"]==50
            files={}
            for fmt in ("xlsx","pdf","docx"):
                result=client.post("/api/chatbot/reports/"+value["id"]+"/exports/"+fmt,headers=headers)
                assert result.status_code==200,result.text
                response=client.get(result.json()["url"],headers=headers);assert response.status_code==200
                path=target/("fase5-reporte-semanal."+fmt);path.write_bytes(response.content)
                if fmt=="xlsx":
                    book=load_workbook(BytesIO(response.content));assert "Registros" in book.sheetnames
                elif fmt=="pdf":assert "2026-10-26" in " ".join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
                else:assert len(Document(BytesIO(response.content)).tables)>0
                files[fmt]={"file":path.name,"bytes":len(response.content),"sha256":result.json()["file_sha256"]}
            advance(reminder)
            notes=client.get("/api/chatbot/proactive/notifications",headers=headers).json()
            verified=next(n for n in notes if n["source"] and n["source"]["type"]=="sesiones_clase")
            data={"demo":"EXCLUSIVAMENTE SINTETICA","storage":"sqlite-memory","mysql":"blocked","external_messages":0,"background_scheduler":"APScheduler 3.11.3","browser_used":False,"accelerated_test_clock":True,
                  "recordatorio":{"source":verified["source"],"created_at":verified["created_at"],"recipient":"Cuenta sintética del profesor"},
                  "reporte_semanal":{"periods":value["periods"],"rows":value["report_rows"],"metrics":value["metrics"],"fingerprint":value["fingerprint"],"files":files}}
            (target/"FASE5_DEMOSTRACION.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print("OK: recordatorio verificado y reporte semanal ejecutados por APScheduler sin navegador. Reloj de prueba acelerado, 2 registros, 50% calculado. XLSX/PDF/DOCX comprobados; cero mensajes externos.")
    finally:service.utcnow=original

if __name__=="__main__":main()
