from datetime import date,datetime,time
from io import BytesIO
import hashlib
import json
import logging
import zipfile
from xml.etree import ElementTree as ET
import pytest
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader
from sqlalchemy import delete
from app.db.models import Usuario,AsignacionProfesor,SesionClase,Asistencia,Nota,Evaluacion,Matricula
from app.services import chatbot_report_store as storage
from app.services import chatbot_reports as service


@pytest.fixture(autouse=True)
def fresh_store(monkeypatch):
    instance=storage.ReportStore()
    monkeypatch.setattr(storage,"store",instance)
    yield instance
    instance.close()


@pytest.fixture
def reports(harness):
    client,sessions,headers=harness
    with sessions() as db:
        for sid in (1,2):db.get(SesionClase,sid).fecha=date(2026,10,22)
        for aid in (1,2,3,4):db.get(Asistencia,aid).fecha=date(2026,10,22)
        for sid,day,state in [(100,3,"PRESENTE"),(101,9,"TARDE"),(102,14,"AUSENTE")]:
            db.add(SesionClase(id=sid,curso_id=1,fecha=date(2026,9,day),hora_inicio=time(9),hora_fin=time(10)));db.flush()
            db.add(Asistencia(id=sid,usuario_id=3,sesion_id=sid,fecha=date(2026,9,day),hora=time(9),confianza=0,liveness_score=0,estado=state))
        db.commit()
    return harness


def spec(**kwargs):
    return {"report_type":"asistencia","course_id":1,"period_start":"2026-09-01","period_end":"2026-09-30",**kwargs}

def create(h,uid=2,**values):
    client,_,headers=h
    return client.post("/api/chatbot/reports",headers=headers(uid),json=spec(**values))

def ask(h,uid,message,context=None,**values):
    client,_,headers=h
    payload={"message":message,**values}
    if context:payload["context_token"]=context["token"]
    return client.post("/api/chatbot/message",headers=headers(uid),json=payload)


@pytest.mark.parametrize("method,path",[("post","/api/chatbot/reports"),("get","/api/chatbot/reports/fake"),("post","/api/chatbot/reports/fake/exports/pdf"),("get","/api/chatbot/reports/fake/files/pdf")])
def test_every_endpoint_requires_auth(reports,method,path):
    client,_,_=reports
    assert getattr(client,method)(path,json=spec() if path.endswith('reports') else None).status_code==401 if method=="post" else client.get(path).status_code==401


def test_metrics_and_dataset_verified(reports):
    response=create(reports);assert response.status_code==200
    value=response.json()
    assert value["report_rows"]==3
    assert value["metrics"]["asistencia_pct"]==66.67
    assert value["metrics"]["denominador_asistencia"]==3
    assert value["metrics"]["presentes"]==1 and value["metrics"]["tardanzas"]==1 and value["metrics"]["ausencias"]==1
    assert {r["estudiante"] for r in value["rows"]}=={"Ana Perfil3"}
    assert value["expires_in"] in range(590,601)
    assert len(value["fingerprint"])==64


@pytest.mark.parametrize("kind,count,state",[("asistencia",3,None),("tardanzas",1,"TARDANZA"),("ausencias",1,"AUSENTE")])
def test_type_filters_do_not_change_denominator(reports,kind,count,state):
    value=create(reports,report_type=kind).json()
    assert value["report_rows"]==count and value["metrics"]["denominador_asistencia"]==3
    if state:assert {r["estado"] for r in value["rows"]}=={state}


@pytest.mark.parametrize("uid,values",[(3,{"student_id":2}),(2,{"student_id":3}),(2,{"course_id":2}),(6,{"student_id":1}),(1,{}),(9,{}),(8,{})])
def test_forbidden_scopes(reports,uid,values):
    assert create(reports,uid,**values).status_code==403


def test_student_only_self_and_teacher_only_assigned_course(reports):
    value=create(reports,3).json();assert {r["estudiante"] for r in value["rows"]}=={"Ana Perfil3"}
    assert all(r["curso"]=="Curso 1" for r in create(reports).json()["rows"])


def test_explicit_admin_permission(reports,monkeypatch):
    monkeypatch.setenv("CHATBOT_INSTITUTIONAL_READ_USER_IDS","1")
    assert create(reports,1).status_code==200


def test_foreign_download_and_revocation(reports):
    client,sessions,headers=reports;key=create(reports).json()["id"]
    assert client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(3)).status_code==404
    assert client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2)).status_code==200
    assert client.get(f"/api/chatbot/reports/{key}/files/pdf",headers=headers(3)).status_code==404
    with sessions() as db:db.execute(delete(AsignacionProfesor));db.commit()
    assert client.get(f"/api/chatbot/reports/{key}/files/pdf",headers=headers(2)).status_code==403


def test_empty_data_has_no_chart_or_invented_zero_percent(reports):
    value=create(reports,period_start="2020-01-01",period_end="2020-01-31").json()
    assert value["message"]=="Sin datos disponibles" and value["chart"]==[]
    assert value["metrics"]["asistencia_pct"] is None


def test_comparison_and_missing_period(reports):
    value=create(reports,report_type="comparacion",compare_start="2020-01-01",compare_end="2020-01-31")
    assert value.status_code==422 # Rango global demasiado amplio.
    value=create(reports,report_type="comparacion",compare_start="2026-10-01",compare_end="2026-10-31").json()
    assert value["comparison"][0]["asistencia_pct"]==66.67
    # Dos registros originales de octubre en el curso 1: presente y ausente.
    assert value["comparison"][1]["asistencia_pct"]==50.0
    assert value["comparison_delta_pp"]==-16.67
    missing=create(reports,report_type="comparacion",compare_start="2026-08-01",compare_end="2026-08-31").json()
    assert missing["comparison"][1]["asistencia_pct"] is None
    assert missing["comparison_delta_pp"] is None


@pytest.mark.parametrize("values",[{"period_end":"2026-08-01"},{"period_start":"2024-01-01"},{"report_type":"emociones"},{"report_type":"comparacion"},{"report_type":"comparacion","compare_start":"2026-09-05","compare_end":"2026-10-05"},{"role":"admin"},{"sql":"SELECT * FROM usuarios"}])
def test_invalid_specs(reports,values):assert create(reports,**values).status_code==422


def test_expiry_discards_and_blocks_files(reports,monkeypatch):
    clock=[1000.0];instance=storage.ReportStore(clock=lambda:clock[0],ttl=5);monkeypatch.setattr(storage,"store",instance)
    client,_,headers=reports;key=create(reports).json()["id"]
    clock[0]=1006
    assert client.get(f"/api/chatbot/reports/{key}",headers=headers(2)).status_code==410
    assert key not in instance.entries
    instance.close()


def test_rate_limits(reports):
    for _ in range(10):assert create(reports).status_code==200
    response=create(reports);assert response.status_code==429 and response.headers["retry-after"]=="60"


def test_export_frequency_and_not_generated_download(reports):
    client,_,headers=reports;key=create(reports).json()["id"]
    assert client.get(f"/api/chatbot/reports/{key}/files/docx",headers=headers(2)).status_code==404
    for _ in range(6):assert client.post(f"/api/chatbot/reports/{key}/exports/xlsx",headers=headers(2)).status_code==200
    assert client.post(f"/api/chatbot/reports/{key}/exports/xlsx",headers=headers(2)).status_code==429


def test_real_files_same_fingerprint_and_data(reports):
    client,_,headers=reports;value=create(reports).json();key=value["id"];files={}
    for fmt in ("xlsx","pdf","docx"):
        result=client.post(f"/api/chatbot/reports/{key}/exports/{fmt}",headers=headers(2))
        assert result.status_code==200,result.text
        assert result.json()["fingerprint"]==value["fingerprint"]
        download=client.get(result.json()["url"],headers=headers(2));assert download.status_code==200
        assert download.headers["x-report-dataset-sha256"]==value["fingerprint"]
        assert "no-store" in download.headers["cache-control"]
        assert hashlib.sha256(download.content).hexdigest()==result.json()["file_sha256"]
        files[fmt]=download.content
    wb=load_workbook(BytesIO(files["xlsx"]));assert wb["Registros"].max_row==4
    assert wb["Indicadores"]["B8"].value==66.67
    assert all(c.data_type!="f" for sheet in wb for row in sheet for c in row)
    assert value["fingerprint"] in str(list(wb["Resumen"].values))
    text="\n".join(page.extract_text() for page in PdfReader(BytesIO(files["pdf"])).pages)
    assert "Ana Perfil3" in text and "66,67" in text and value["fingerprint"] in text
    assert "Maria" not in text
    doc=Document(BytesIO(files["docx"]));assert len(doc.tables[1].rows)==4
    assert "66,67" in " ".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)


def test_excel_formula_injection_and_pdf_markup_are_literal(reports):
    client,sessions,headers=reports
    with sessions() as db:
        db.get(Usuario,3).nombres=" =HYPERLINK(\"https://evil.test\") <b>Nombre</b>";db.commit()
    key=create(reports).json()["id"]
    for fmt in ("xlsx","pdf","docx"):
        output=client.post(f"/api/chatbot/reports/{key}/exports/{fmt}",headers=headers(2));assert output.status_code==200,output.text
        content=client.get(output.json()["url"],headers=headers(2)).content
        if fmt=="xlsx":
            wb=load_workbook(BytesIO(content));cell=wb["Registros"]["C2"]
            assert cell.data_type=="s" and cell.value.lstrip().startswith("=HYPERLINK") and cell.quotePrefix
            assert wb._external_links==[]
        elif fmt=="pdf":
            pages=PdfReader(BytesIO(content)).pages
            assert any("<b>Nombre</b>" in page.extract_text() for page in pages)
        else:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                for name in archive.namelist():
                    if name.endswith('.rels'):
                        assert all(item.get('TargetMode')!='External' for item in ET.fromstring(archive.read(name)))


def test_academic_weighted_grades_scoped_and_cutoff(reports):
    _,sessions,_=reports
    with sessions() as db:
        db.get(Evaluacion,1).peso=20
        note=db.query(Nota).filter(Nota.evaluacion_id==1).one();note.estado="calificado";note.registrada_en=datetime(2026,9,2)
        db.add(Evaluacion(id=20,curso_id=1,nombre="Segunda",peso=80));db.flush()
        db.add(Nota(evaluacion_id=20,estudiante_id=1,nota=12,estado="calificado",registrada_en=datetime(2026,9,3)))
        db.get(Evaluacion,2).peso=100
        note=db.query(Nota).filter(Nota.evaluacion_id==2).one();note.estado="calificado";note.registrada_en=datetime(2026,9,2)
        db.commit()
    value=create(reports,report_type="academico").json()
    assert value["grades"]==[{"curso":"Curso 1","estudiante":"Ana Perfil3","evaluaciones":2,"promedio_ponderado":12.8}]


def test_conversation_report_formats_and_preview_reuse(reports):
    first=ask(reports,2,"Genera el reporte de asistencia de mi curso de septiembre de 2026").json()
    assert first["intent"]=="REPORT";key=first["report"]["id"];fingerprint=first["report"]["fingerprint"]
    for question,fmt in [("Genera el reporte en Excel","xlsx"),("Ahora quiero el mismo reporte en PDF","pdf"),("Descárgalo en Word","docx"),("Muéstrame una vista previa",None)]:
        response=ask(reports,2,question,first["context"]);assert response.status_code==200,response.text
        value=response.json();assert value["report"]["id"]==key and value["report"]["fingerprint"]==fingerprint
        if fmt:assert value["report"]["requested_formats"]==[fmt]
        first=value


@pytest.mark.parametrize("question",["Genera el reporte de asistencia de Maria","Reporte de faltas de Maria","Reporte emocional de Ana","Reporte de EmoScan"])
def test_no_foreign_names_or_emotional_reports(reports,question):
    assert ask(reports,2,question).status_code in (400,403)


def test_natural_comparison_and_weekly_reports(reports):
    value=ask(reports,2,"Compara la asistencia de septiembre y octubre de 2026").json()
    assert len(value["report"]["comparison"])==2
    weekly=ask(reports,2,"Muéstrame las tardanzas de esta semana").json()
    assert weekly["report"]["spec"]["report_type"]=="tardanzas"
    start=date.fromisoformat(weekly["report"]["spec"]["period_start"]);end=date.fromisoformat(weekly["report"]["spec"]["period_end"])
    assert start.weekday()==0 and (end-start).days==6


def test_audit_no_private_content(reports,caplog):
    caplog.set_level(logging.INFO,logger="monitor.chatbot.exports")
    client,_,headers=reports;key=create(reports).json()["id"]
    result=client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2))
    client.get(result.json()["url"],headers=headers(2))
    assert "export_generated" in caplog.text and "export_downloaded" in caplog.text
    for private in ["Ana","Perfil3",key,"Bearer"]:assert private not in caplog.text


def test_volume_limit_no_silent_truncation(reports,monkeypatch):
    monkeypatch.setattr(service,"MAX_ROWS",2)
    assert create(reports).status_code==413


def test_download_rechecks_owner_and_permissions_for_every_format(reports):
    client,sessions,headers=reports;key=create(reports).json()["id"]
    result=client.post(f"/api/chatbot/reports/{key}/exports/docx",headers=headers(2));assert result.status_code==200
    with sessions() as db:db.get(Usuario,2).estado="inactivo";db.commit()
    assert client.get(result.json()["url"],headers=headers(2)).status_code==401


def test_historical_comparison_shared_year(reports):
    value=ask(reports,2,"Compara septiembre y octubre de 2025").json()["report"]["spec"]
    assert value["period_start"]=="2025-09-01" and value["compare_start"]=="2025-10-01"


def test_new_report_requeries_and_same_report_is_immutable(reports):
    first=ask(reports,2,"Reporte de asistencia de septiembre de 2026").json()
    _,sessions,_=reports
    with sessions() as db:db.get(Asistencia,100).estado="AUSENTE";db.commit()
    same=ask(reports,2,"El mismo reporte en PDF",first["context"]).json()
    assert same["report"]["fingerprint"]==first["report"]["fingerprint"]
    assert same["report"]["metrics"]["asistencia_pct"]==66.67
    new=ask(reports,2,"Genera un nuevo reporte en PDF",same["context"]).json()
    assert new["report"]["id"]!=first["report"]["id"]
    assert new["report"]["metrics"]["asistencia_pct"]==33.33


def test_snapshot_and_file_capacity_limits(reports,monkeypatch):
    monkeypatch.setattr(storage,"MAX_ENTRIES",1)
    assert create(reports).status_code==200
    assert create(reports).status_code==503


def test_file_size_and_concurrency_limits(reports,monkeypatch):
    from app.api import chatbot_reports as api
    client,_,headers=reports;key=create(reports).json()["id"]
    monkeypatch.setattr(storage,"MAX_FILE_BYTES",8)
    assert client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2)).status_code==413
    import threading
    monkeypatch.setattr(storage,"render_slots",threading.BoundedSemaphore(0))
    assert client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2)).status_code==503


def test_render_failure_does_not_expose_private_data(reports,monkeypatch):
    from app.api import chatbot_reports as api
    def broken(*args):raise ValueError("Ana Perfil3 private-example")
    monkeypatch.setattr(api,"render",broken)
    client,_,headers=reports;key=create(reports).json()["id"]
    response=client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2))
    assert response.status_code==503 and "private-example" not in response.text


def test_download_rate_limit(reports):
    client,_,headers=reports;key=create(reports).json()["id"]
    result=client.post(f"/api/chatbot/reports/{key}/exports/pdf",headers=headers(2)).json()
    for _ in range(15):assert client.get(result["url"],headers=headers(2)).status_code==200
    assert client.get(result["url"],headers=headers(2)).status_code==429


def test_report_followup_retains_type_and_updates_period(reports):
    first=ask(reports,2,"Reporte de tardanzas de septiembre de 2026").json()
    next_report=ask(reports,2,"¿Y en octubre?",first["context"]).json()
    assert next_report["intent"]=="REPORT"
    assert next_report["report"]["spec"]["report_type"]=="tardanzas"
    assert next_report["report"]["spec"]["period_start"]=="2026-10-01"
    assert next_report["report"]["id"]!=first["report"]["id"]


@pytest.mark.parametrize("fmt",["xlsx","pdf","docx"])
def test_empty_documents_are_real_and_explicit(reports,fmt):
    client,_,headers=reports
    key=create(reports,period_start="2020-01-01",period_end="2020-01-31").json()["id"]
    result=client.post(f"/api/chatbot/reports/{key}/exports/{fmt}",headers=headers(2));assert result.status_code==200
    content=client.get(result.json()["url"],headers=headers(2)).content
    if fmt=="xlsx":
        wb=load_workbook(BytesIO(content));assert "Grafico" not in wb.sheetnames
        assert wb["Registros"]["A2"].value=="Sin datos disponibles"
    elif fmt=="pdf":assert "Sin datos disponibles" in " ".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
    else:assert any("Sin datos disponibles" in para.text for para in Document(BytesIO(content)).paragraphs)
