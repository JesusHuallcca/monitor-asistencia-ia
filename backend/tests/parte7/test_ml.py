"""Contratos e integración real del router; proveedores de inferencia dobles solo en pruebas."""
from datetime import datetime,timedelta,time
from io import BytesIO
import json
import shutil
import sys
from types import ModuleType
from zoneinfo import ZoneInfo
import pytest
from openpyxl import load_workbook
from docx import Document
from pypdf import PdfReader
from app.core.config import TIMEZONE
from app.db.models import Usuario,AsignacionProfesor,SesionClase,Asistencia,Nota,Evaluacion
from app.services import chatbot_ml as ml,chatbot_report_store as storage

@pytest.fixture(autouse=True)
def memory(monkeypatch):
    store=storage.ReportStore()
    monkeypatch.setattr(storage,"store",store)
    yield store
    store.close()


def ask(h,uid,message,**kw):
    client,_,headers=h
    return client.post("/api/chatbot/message",headers=headers(uid),json=dict(message=message,**kw))


def query(h,uid=2,**kw):
    client,_,headers=h
    return client.post("/api/chatbot/ml/query",headers=headers(uid),json={"model":"kmeans",**kw})


@pytest.mark.parametrize("method,path,body",[("get","/api/chatbot/ml/catalog",None),("post","/api/chatbot/ml/query",{"model":"kmeans"}),("post","/api/chatbot/ml/reports",None)])
def test_authentication(harness,method,path,body):
    client,_,_=harness
    assert client.request(method,path,json=body).status_code==401


@pytest.mark.parametrize("uid,values",[(2,{"course_id":2}),(2,{"student_id":3}),(3,{"student_id":2}),(3,{"course_id":3}),(6,{"student_id":1}),(8,{}),(1,{}),(9,{})])
def test_scope_denied(harness,uid,values):
    assert query(harness,uid,**values).status_code==403


@pytest.mark.parametrize("values",[{"features":{"asistencia_30d":1}},{"model":"other"},{"source":"mysql"},{"operation":"train"},{"course_id":0},{"student_id":-1}])
def test_closed_contract(harness,values):
    client,_,headers=harness
    assert client.post("/api/chatbot/ml/query",headers=headers(2),json={"model":"kmeans",**values}).status_code==422


@pytest.mark.parametrize("question,intent",[("Genera reporte de evaluación de los modelos","ML_REPORT"),("¿Qué representa cada grupo?","ML_EXPLAIN"),("¿Cómo se agrupan los estudiantes?","ML_EXPLAIN"),("¿Qué es K-Means?","ML_EXPLAIN"),("¿Cómo se agrupan los estudiantes con K-Means?","ML_EXPLAIN"),("Diferencias entre regresión y red neuronal","ML_EXPLAIN"),("Muestra los clusters K-Means sintéticos","ML_SEGMENTS"),("Consulta probabilidad de asistencia Parte 6","ML_NEURAL"),("Compara los modelos de regresión y red neuronal","ML_REPORT"),("¿Asistir es igual que llegar temprano?","ML_TARGET"),("Clasifica riesgo con EmoScan facial","ML_SAFETY")])
def test_spanish_intents(harness,question,intent):
    response=ask(harness,2,question)
    assert response.status_code==200,response.text
    assert response.json()["intent"]==intent
    assert response.json()["provider"]=="local"


def test_kmeans_saved_results_no_training(harness,monkeypatch):
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    def forbidden(*a,**kw):raise AssertionError("No se entrena durante consultas")
    for cls in [KMeans,StandardScaler,PCA]:monkeypatch.setattr(cls,"fit",forbidden)
    response=query(harness);assert response.status_code==200
    data=response.json()["ml"]
    assert data["status"]=="available"
    assert (data["profiles"],data["k"])==(150,3)
    assert data["metrics"]["silueta"]==pytest.approx(.2373692496101911)
    assert data["variables"]==ml.FOUR and data["origin"]=="sintetico"
    assert data["model_version"].startswith("sha256:")
    assert [g["profiles"] for g in data["groups"]]==[45,60,45]
    assert [g["description"] for g in data["groups"]]==["asistencia baja","asistencia intermedia","asistencia relativamente alta"]
    assert "usuario_id" not in json.dumps(data) and "pca_1" not in json.dumps(data)


@pytest.mark.parametrize("corruption",["missing","origin","nan","summary","count","features","input_hash"])
def test_artifact_integrity_fails_closed(tmp_path,monkeypatch,corruption):
    for name in ["metricas_segmentacion.json","segmentos_asignados.csv","resumen_segmentos.csv"]:shutil.copyfile(ml.SEGMENT_DIR/name,tmp_path/name)
    if corruption=="missing":(tmp_path/"segmentos_asignados.csv").unlink()
    elif corruption in {"origin","count","features","input_hash"}:
        p=tmp_path/"metricas_segmentacion.json";data=json.loads(p.read_text())
        if corruption=="input_hash":data["sha256_entrada"]="0"*64
        if corruption=="origin":data["origen_expresiones"]="facial"
        if corruption=="count":data["perfiles"]=149
        if corruption=="features":data["variables"]=ml.FOUR[:3]
        p.write_text(json.dumps(data))
    else:
        p=tmp_path/("segmentos_asignados.csv" if corruption=="nan" else "resumen_segmentos.csv")
        text=p.read_text();text=text.replace("0.3111111111111111","NaN",1) if corruption=="nan" else text.replace("1,45,","1,44,",1);p.write_text(text)
    monkeypatch.setattr(ml,"SEGMENT_DIR",tmp_path)
    assert ml.segmentation()["status"]=="unavailable"


def test_no_synthetic_id_matches_real_student(harness):
    response=query(harness,student_id=1)
    assert response.json()["ml"]["status"]=="pending"
    assert "groups" not in response.json()["ml"]
    assert ask(harness,3,"Mi cluster de K-Means").json()["ml"]["status"]=="pending"


def test_neural_pending_without_provider(harness, monkeypatch):
    monkeypatch.setattr(ml.importlib.util, "find_spec", lambda name: None)
    response=ask(harness,2,"Consulta probabilidad de asistencia con red neuronal",course_id=1,student_id=1).json()
    assert response["ml"]["status"]=="pending"
    assert response["ml"]["model_version"] is None
    assert "probability" not in response["ml"]
    assert "probability" not in ml.neural_status()


@pytest.mark.parametrize("uid",[3,6])
def test_neural_inference_respects_professor_contract(harness,uid):
    response=ask(harness,uid,"Predicción de red neuronal",course_id=1,student_id=1)
    assert response.status_code==403


@pytest.fixture
def neural_provider(monkeypatch):
    """Sustituye solo el servicio opcional auditado; jamás se publica como ejecución real."""
    from app import services
    calls=[]
    context=dict(ready=True,features={key:0 for key in ml.NEURAL},cutoff="2026-10-31T09:00:00",session_at="2026-11-01T09:00:00",blockers=[])
    provider=ModuleType("app.services.parte6_service")
    provider.sessions=lambda db,user,course:[{"id":40}]
    def get_context(db,user,course,student,session):
        calls.append((user.id,course,student,session));return context
    provider.context=get_context
    inference=ModuleType("red_neuronal.inference")
    class FakeInference:
        def predict(self,values,**kw):return dict(probabilidad=.61,model_version="fixture-only",model_sha256="a"*64,feature_order=ml.NEURAL,training_origin="sintetico",**kw)
    inference.AttendanceInference=FakeInference
    package=ModuleType("red_neuronal");package.__path__=[]
    monkeypatch.setitem(sys.modules,"red_neuronal",package)
    monkeypatch.setitem(sys.modules,"red_neuronal.inference",inference)
    monkeypatch.setattr(services,"parte6_service",provider,raising=False)
    original=ml.importlib.util.find_spec
    monkeypatch.setattr(ml.importlib.util,"find_spec",lambda name:object() if name=="red_neuronal" else original(name))
    return calls,context,FakeInference


def test_authorized_neural_contract_and_revocation(harness,neural_provider):
    calls,_,_=neural_provider
    response=ask(harness,2,"Predicción red neuronal",course_id=1,student_id=1)
    assert response.status_code==200
    data=response.json()["ml"]
    assert data["probability"]==.61 and data["training_origin"]=="sintetico"
    assert data["model_version"]=="fixture-only" and calls==[(2,1,1,40)]
    assert ask(harness,2,"Predicción red neuronal",course_id=2,student_id=1).status_code==403
    assert ask(harness,2,"Predicción red neuronal",course_id=1,student_id=3).status_code==403
    assert ask(harness,3,"Predicción red neuronal",course_id=1,student_id=1).status_code==403
    assert len(calls)==1
    with harness[1]() as db:
        assignment=db.query(AsignacionProfesor).first();db.delete(assignment);db.commit()
    assert ask(harness,2,"Predicción red neuronal",course_id=1,student_id=1).status_code==403
    assert len(calls)==1


@pytest.mark.parametrize("failure",["nan","version","exception","cutoff"])
def test_bad_neural_service_never_invents(harness,neural_provider,monkeypatch,failure):
    _,_,fake=neural_provider;original=fake.predict
    def predict(self,*a,**kw):
        if failure=="exception":raise OSError("Private details")
        value=original(self,*a,**kw)
        if failure=="nan":value["probabilidad"]=float("nan")
        if failure=="version":value["model_version"]=""
        if failure=="cutoff":value["cutoff"]=value["session_at"]
        return value
    monkeypatch.setattr(fake,"predict",predict)
    data=ask(harness,2,"Predicción Parte 6",course_id=1,student_id=1).json()["ml"]
    assert data["status"]=="unavailable" and "probability" not in data
    assert "Private" not in json.dumps(data)


def test_neural_blockers_no_inference(harness,neural_provider,monkeypatch):
    _,context,fake=neural_provider
    context.update(ready=False,blockers=["Cinco sesiones requeridas"])
    monkeypatch.setattr(fake,"predict",lambda *a,**kw:pytest.fail("Historial no listo"))
    data=ask(harness,2,"Predicción Parte 6",course_id=1,student_id=1).json()["ml"]
    assert data["status"]=="pending" and "probability" not in data


def test_catalog_honest_metrics_and_no_winner(harness):
    client,_,headers=harness
    response=client.get("/api/chatbot/ml/catalog",headers=headers(2))
    value=response.json();assert not value["comparable"] and value["winner"] is None
    logistic=value["models"][1]
    assert logistic["origin"]=="no_verificado" and logistic["model_version"] is None
    assert logistic["metrics"]["accuracy"]==.6748 and logistic["n_test"]==1688
    assert "temporal" in logistic["limitations"]


def test_gemini_cannot_rewrite_ml(harness,monkeypatch):
    import httpx
    monkeypatch.setenv("GEMINI_API_KEY","test-key")
    monkeypatch.setenv("GEMINI_MODEL","gemini-test")
    async def forbidden(*a,**kw):pytest.fail("ML no se envía a Gemini")
    monkeypatch.setattr(httpx.AsyncClient,"post",forbidden)
    value=ask(harness,2,"Resultados K-Means").json()
    assert value["provider"]=="local" and value["ml"]["profiles"]==150


def test_report_conversation_same_snapshot_formats_and_academic_switch(harness):
    first=ask(harness,2,"Genera reporte de evaluación de K-Means y regresión").json()
    assert first["report"]["kind"]=="ml_evaluation"
    assert first["report"]["winner"] is None
    second=ask(harness,2,"Ahora el mismo en PDF",context_token=first["context"]["token"]).json()
    assert second["report"]["id"]==first["report"]["id"]
    assert second["report"]["requested_formats"]==["pdf"]
    # La memoria de ML no convierte un pedido académico explícito en evaluación ML.
    third=ask(harness,2,"Genera reporte de asistencia de octubre",context_token=second["context"]["token"])
    assert third.status_code==200 and third.json()["intent"]=="REPORT"


@pytest.mark.parametrize("fmt",["xlsx","pdf","docx"])
def test_ml_download_real_files_and_owner(harness,fmt):
    client,_,headers=harness
    report=client.post("/api/chatbot/ml/reports",headers=headers(2)).json()
    key=report["id"]
    generated=client.post(f"/api/chatbot/reports/{key}/exports/{fmt}",headers=headers(2))
    assert generated.status_code==200,generated.text
    file=client.get(generated.json()["url"],headers=headers(2))
    assert file.status_code==200 and len(file.content)>1000
    assert client.get(generated.json()["url"],headers=headers(3)).status_code==404
    assert client.get(generated.json()["url"]).status_code==401
    if fmt=="xlsx":
        book=load_workbook(BytesIO(file.content));text=" ".join(str(c.value) for ws in book for row in ws for c in row)
    elif fmt=="pdf":text=" ".join(page.extract_text() for page in PdfReader(BytesIO(file.content)).pages)
    else:
        doc=Document(BytesIO(file.content));text=" ".join(p.text for p in doc.paragraphs)+" "+" ".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    assert "silueta" in text
    if fmt=="xlsx":assert "0.6748" in text
    assert "no_verificado" in text and "no es accuracy" in text
    assert "asistencia_pct" not in text


@pytest.fixture
def logistic_fixture(harness,tmp_path,monkeypatch):
    from app.services.prediction_service import prediction_service
    (tmp_path/"models").mkdir();(tmp_path/"models"/"asistencia_logreg.joblib").write_bytes(b"not-a-model-fixture-no-deserialization")
    monkeypatch.setattr(ml,"ROOT",tmp_path)
    calls=[]
    def predict(**kw):calls.append(kw);return {"probabilidad":.42}
    monkeypatch.setattr(prediction_service,"predict_for_student",predict)
    now=datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    with harness[1]() as db:
        for sid in (1,2):
            row=db.get(SesionClase,sid);row.fecha=(now-timedelta(days=1)).date();row.fecha_registro=now-timedelta(days=3)
        for aid in (1,2,3,4):
            row=db.get(Asistencia,aid);row.fecha=(now-timedelta(days=1)).date();row.fecha_registro=datetime.combine((now-timedelta(days=1)).date(),time(11))
        for sid in (3,4):db.get(SesionClase,sid).fecha_registro=now-timedelta(days=3)
        for nid in (1,2):
            note=db.get(Nota,nid);note.estado="calificado";note.registrada_en=now-timedelta(hours=4)
            db.get(Evaluacion,nid).creado_en=now-timedelta(days=3)
        # Una nota futura del mismo curso nunca debe influir.
        db.add(Evaluacion(id=99,curso_id=1,nombre="Nota futura",creado_en=now-timedelta(days=2)));db.flush()
        db.add(Nota(id=99,evaluacion_id=99,estudiante_id=1,nota=1,estado="calificado",registrada_en=now+timedelta(days=1)))
        db.commit()
    return calls


def test_regression_authorized_history_cutoff_and_no_future_grade(harness,logistic_fixture):
    response=ask(harness,2,"Predicción de Ana",course_id=1,student_id=1)
    assert response.status_code==200,response.text
    data=response.json()["ml"]
    assert data["status"]=="available" and data["probability"]==.42,data
    assert data["target"]=="asistencia, incluyendo tardanzas"
    assert data["training_origin"]=="no_verificado"
    assert logistic_fixture[0]["promedio_notas"]==16
    assert logistic_fixture[0]["historial"]==[{"estado":"PRESENTE"}]
    assert ask(harness,2,"Predicción",course_id=2,student_id=1).status_code==403
    assert ask(harness,2,"Predicción",course_id=1,student_id=3).status_code==403
    assert len(logistic_fixture)==1


def test_regression_missing_grades_does_not_impute(harness,logistic_fixture):
    with harness[1]() as db:
        db.get(Nota,1).estado="pendiente";db.commit()
    response=ask(harness,2,"Predicción regresión",course_id=1,student_id=1)
    assert response.json()["ml"]["status"]=="pending" and not logistic_fixture


def test_regression_missing_artifact_returns_status_not_500(harness):
    response=ask(harness,2,"Predicción de Ana",course_id=1,student_id=1)
    assert response.status_code==200 and response.json()["ml"]["status"]=="unavailable"
    assert "probability" not in response.json()["ml"]


def test_direct_results_do_not_trigger_prediction(harness):
    response=query(harness,model="regresion_logistica",operation="results",course_id=1,student_id=1)
    assert response.status_code==200
    assert "metrics" in response.json() and "probability" not in response.json()
    assert query(harness,operation="predict").status_code==422


@pytest.mark.parametrize("model,first,expected",[("red_neuronal_parte6","Explica la red neuronal Parte 6","32 y 16"),("kmeans","Muestra resultados K-Means sintéticos","centroides")])
def test_model_context_followup_is_signed(harness,model,first,expected):
    initial=ask(harness,2,first).json()
    assert initial["context"]["ml_model"]==model
    follow=ask(harness,2,"¿Y qué variables utiliza?",context_token=initial["context"]["token"]).json()
    assert follow["intent"]=="ML_EXPLAIN" and expected in follow["reply"]
    if model=="red_neuronal_parte6":
        pending=ask(harness,2,"¿Y mi probabilidad?",context_token=follow["context"]["token"]).json()
        assert pending["intent"]=="ML_NEURAL" and pending["ml"]["status"]=="pending"
