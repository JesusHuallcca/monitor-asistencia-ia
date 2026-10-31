"""Adaptadores de solo lectura. Ningún fit, entrenamiento, SQL libre ni datos faciales."""
import csv
import hashlib
import importlib.util
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from app.core.config import TIMEZONE, DEMO_MODE
from app.services.chatbot_security import academic_scope, deny

ROOT = Path(__file__).resolve().parents[3]
SEGMENT_DIR = ROOT / "segmentacion" / "resultados"
FOUR = ["asistencia_ratio", "tardanzas_ratio", "promedio_notas", "expresiones_positivas_ratio"]
NEURAL = ["asistencia_30d", "tardanzas_30d", "asistencia_ultimas5", "sesiones_previas", "promedio_previo", "sin_notas", "dia_sin", "dia_cos", "hora"]
NOTICE = "La probabilidad de asistir incluye llegar tarde; no es la probabilidad de llegar temprano. Son estimaciones experimentales, no certezas ni diagnósticos. No se usan datos de EmoScan."
REFERENCE = "68430e14d481c37b4f898969f40a36bb0abadc27"


def intent_for(q, previous=None):
    """Se ejecuta antes de las reglas genéricas de reportes/modelos."""
    named = re.search(r"k[ -]?means|segmentacion|clusters?|centroides|regresion|red(?:es)? neuronal(?:es)?|parte ?6|aprendizaje (?:supervisado|no supervisado)", q)
    if re.search(r"emoscan|facial|emocion", q) and re.search(r"riesgo|predi|clasifi|segment|modelo", q):return "ML_SAFETY"
    if re.search(r"llegar (?:temprano|tarde)|puntualidad|probabilidad de (?:asistir|asistencia)", q) and re.search(r"diferencia|equival|mismo|igual|temprano|puntualidad", q):return "ML_TARGET"
    if not named and re.search(r"\bmodelos?\b",q) and re.search(r"reporte|informe|evaluacion|compara",q):return "ML_REPORT"
    if not named and re.search(r"como se agrupan|que (?:representa|significa).*grupo",q):return "ML_EXPLAIN"
    if named:
        if re.search(r"reporte|informe|evaluacion|metricas|compara|excel|pdf|word|docx|xlsx", q) and not re.search(r"diferencia|que es|explica", q):return "ML_REPORT"
        if re.search(r"que es|explica|como (?:funciona|se agrupan)|diferencia|variables|que representa|significa", q):return "ML_EXPLAIN"
        if re.search(r"red(?:es)? neuronal|parte ?6", q) and re.search(r"probabilidad|predi|consulta|asist", q):return "ML_NEURAL"
        if re.search(r"regresion", q) and re.search(r"probabilidad|predi|consulta|asist", q):return "ML_REGRESSION"
        if re.search(r"k[ -]?means|segmentacion|clusters?|centroides", q):return "ML_SEGMENTS"
        return "ML_EXPLAIN"
    if not named and re.search(r"reporte|informe",q) and re.search(r"asistencia|tardanzas|ausencias|faltas|historial|resumen academico",q):return None
    if previous and previous.startswith("ML_"):
        if re.search(r"grupo|variable|origen|version|significa|representa",q):return "ML_EXPLAIN"
        if re.search(r"reporte|informe|evaluacion|compara|excel|pdf|word|docx|xlsx|descarga|vista previa", q):return "ML_REPORT"
        if re.search(r"(?:y |ahora ).*(?:grupo|variable|origen|version)", q):return "ML_EXPLAIN"
    return None


def read_bytes(path, maximum=2_000_000):
    if path.stat().st_size > maximum:raise ValueError("Artefacto demasiado grande")
    return path.read_bytes()


def number(value, low, high):
    if isinstance(value, bool):raise ValueError("Número no válido")
    value=float(value)
    if not math.isfinite(value) or not low<=value<=high:raise ValueError("Fuera de rango")
    return value


def result(model, status, reason, *, origin="no_disponible", version=None, variables=None, **extra):
    return dict(model=model,status=status,reason=reason,origin=origin,model_version=version,variables=variables or [],**extra)


def segmentation():
    """Solo agregados de una demostración explícitamente sintética, nunca IDs académicos."""
    try:
        raw=read_bytes(SEGMENT_DIR / "metricas_segmentacion.json")
        meta=json.loads(raw)
        if meta["origen_datos"]!="sintetico" or meta["origen_expresiones"]!="sintetico" or meta["variables"]!=FOUR:raise ValueError("Proveniencia incompatible")
        if hashlib.sha256(read_bytes(ROOT / "segmentacion" / "datos_asistencia_sinteticos.csv")).hexdigest()!=meta["sha256_entrada"]:raise ValueError("Fuente incompatible")
        assigned=read_bytes(SEGMENT_DIR / "segmentos_asignados.csv").decode("utf-8-sig")
        rows=list(csv.DictReader(assigned.splitlines()))
        if not rows or len(rows)!=meta["perfiles"] or len(rows)>10000:raise ValueError("Perfiles incompatibles")
        ids=set();groups={}
        for row in rows:
            if row["origen_datos"]!="sintetico" or row["origen_expresiones"]!="sintetico":raise ValueError("Origen incompatible")
            if row["usuario_id"] in ids:raise ValueError("Perfil duplicado")
            ids.add(row["usuario_id"])
            key=int(row["segmento"])
            if key<1:raise ValueError("Grupo inválido")
            values={k:number(row[k],0,20 if k=="promedio_notas" else 1) for k in FOUR}
            groups.setdefault(key,[]).append(values)
        if len(groups)!=meta["k_elegido"]:raise ValueError("K incompatible")
        # Validar el resumen persistido frente a las asignaciones, sin recalcular el modelo.
        summaries=list(csv.DictReader(read_bytes(SEGMENT_DIR / "resumen_segmentos.csv").decode("utf-8-sig").splitlines()))
        if len(summaries)!=len(groups):raise ValueError("Resumen incompatible")
        if {int(r["segmento"]) for r in summaries}!=set(groups):raise ValueError("Grupos incompatibles")
        output=[]
        ordered=sorted(groups,key=lambda k:sum(r["asistencia_ratio"] for r in groups[k])/len(groups[k]))
        for row in summaries:
            key=int(row["segmento"]);items=groups[key]
            if len(items)!=int(row["perfiles"]):raise ValueError("Conteo incompatible")
            means={v:sum(r[v] for r in items)/len(items) for v in FOUR}
            if any(abs(means[v]-number(row[v],0,20 if v=="promedio_notas" else 1))>1e-8 for v in FOUR):raise ValueError("Medias incompatibles")
            rank=ordered.index(key)
            label="asistencia baja" if rank==0 else "asistencia relativamente alta" if rank==len(ordered)-1 else "asistencia intermedia"
            output.append(dict(group=f"E{key}",description=label,profiles=len(items),means=means))
        evaluation=next(r for r in meta["evaluacion"] if r["k"]==meta["k_elegido"])
        silhouette=number(evaluation["silueta"],-1,1)
        digest=hashlib.sha256(raw+assigned.encode()).hexdigest()
        return result("kmeans","available","Resultados guardados; no se ejecutó K-Means ni PCA.",origin="sintetico",version="sha256:"+digest,variables=FOUR,profiles=len(rows),k=len(groups),metrics={"silueta":silhouette},groups=sorted(output,key=lambda r:r["group"]),source="segmentacion/resultados",input_sha256=meta.get("sha256_entrada"),target="agrupamiento sin etiqueta objetivo",limitations="Agregados de perfiles simulados, sin correspondencia con estudiantes ni filtros académicos. Expresiones positivas sintéticas, no emociones reales.")
    except (OSError,ValueError,KeyError,TypeError,StopIteration,csv.Error,OverflowError):
        return result("kmeans","unavailable","Resultados ausentes, inconsistentes o sin origen sintético verificable. No se reentrena.",variables=FOUR)


def regression_metadata():
    from ai.ml.features import FEATURE_COLUMNS
    try:
        raw=read_bytes(ROOT / "models" / "metricas_modelo.json")
        data=json.loads(raw)
        if data["model_type"]!="LogisticRegression" or data["features"]!=FEATURE_COLUMNS:raise ValueError("Contrato incompatible")
        metrics={k:number(data[k],0,1) for k in ("accuracy","precision","recall","f1","roc_auc")}
        return result("regresion_logistica","available","Métricas archivadas; no se ha ejecutado una nueva evaluación.",origin="no_verificado",version=None,report_version="sha256:"+hashlib.sha256(raw).hexdigest(),variables=FEATURE_COLUMNS,metrics=metrics,n_test=int(data["n_test"]),source="models/metricas_modelo.json",target="asistira: PRESENTE o TARDANZA = 1; AUSENTE = 0",limitations="El reporte no vincula la huella del dataset ni del modelo. El generador predeterminado es sintético, pero este artefacto no acredita el origen. División aleatoria estratificada del script: posible fuga entre sesiones del mismo estudiante. No comparable con la prueba temporal de Parte 6.")
    except (OSError,ValueError,KeyError,TypeError,OverflowError):
        return result("regresion_logistica","unavailable","Sin métricas verificables disponibles.",variables=FEATURE_COLUMNS)


def neural_status():
    return result("red_neuronal_parte6","pending","Parte 6 no está integrada en esta rama: pendiente conectar su servicio autorizado de contexto e inferencia MySQL. No hay probabilidad real disponible.",variables=NEURAL,reference_commit=REFERENCE,target="asistencia a la siguiente sesión, incluyendo tardanzas",dependencies=["Servicio parte6_service y router /api/parte6/system", "Artefactos y manifiesto validados de Parte 6", "TensorFlow compatible y esquema histórico con fechas verificables"])


def authorized_selection(db,user,selection):
    scope=academic_scope(db,user)
    course=selection.get("course_id");student=selection.get("student_id")
    if course is not None and course not in scope.course_ids:deny("ml_course")
    ids=[course] if course is not None else list(scope.course_ids)
    if student is not None:
        allowed={s.id for s,_,_ in db.execute(scope.students_query(ids)).unique()}
        if student not in allowed:deny("ml_student")
    return scope,course,student


def neural_prediction(db,user,selection):
    """Adaptación opcional al servicio auditado, sin aceptar features ni sesiones del cliente."""
    _,course,student=authorized_selection(db,user,selection)
    if str(user.rol).lower()!="profesor":deny("ml_neural_professor_contract")
    if importlib.util.find_spec("red_neuronal") is None:return neural_status()
    if course is None or student is None:
        return result("red_neuronal_parte6","pending","Selecciona un curso y un estudiante autorizados.",variables=NEURAL)
    try:
        # Solo módulos instalados por el operador. Sin HTTP externo, tokens reenviados ni código de otras ramas.
        from app.services import parte6_service as service
        from red_neuronal.inference import AttendanceInference
        sessions=service.sessions(db,user,course)
        if not sessions:return result("red_neuronal_parte6","unavailable","Sin próxima sesión activa.",variables=NEURAL)
        context=service.context(db,user,course,student,sessions[0]["id"])
        if not context["ready"]:
            return result("red_neuronal_parte6","pending","El historial no permite inferencia al corte actual.",variables=NEURAL,blockers=context["blockers"])
        prediction=AttendanceInference().predict(context["features"],source="mysql_experimental",cutoff=context["cutoff"],session_at=context["session_at"])
        probability=number(prediction["probabilidad"],0,1)
        if prediction["cutoff"]!=context["cutoff"] or prediction["session_at"]!=context["session_at"] or prediction["source"]!="mysql_experimental":raise ValueError("Corte incompatible")
        if datetime.fromisoformat(prediction["cutoff"])>=datetime.fromisoformat(prediction["session_at"]):raise ValueError("Fuga temporal")
        if not re.fullmatch(r"[0-9a-f]{64}",prediction["model_sha256"]):raise ValueError("Huella incompatible")
        if prediction["feature_order"]!=NEURAL or not prediction["model_version"] or prediction["training_origin"]!="sintetico":raise ValueError("Contrato incompatible")
        return result("red_neuronal_parte6","available","Inferencia experimental autorizada; no validada con estudiantes reales.",origin="sintetico" if DEMO_MODE else "sistema",version=prediction["model_version"],variables=NEURAL,training_origin=prediction["training_origin"],model_sha256=prediction["model_sha256"],probability=probability,target="asistencia, incluyendo tardanzas",cutoff=prediction["cutoff"],session_at=prediction["session_at"])
    except HTTPException:raise
    except (ImportError,OSError,ValueError,KeyError,TypeError):
        return result("red_neuronal_parte6","unavailable","Servicio o artefactos incompatibles o no disponibles. No se inventó una probabilidad ni se reentrenó.",variables=NEURAL)


def regression_prediction(db,user,selection):
    """Reutiliza PredictionService con datos anteriores al corte, sin valores medios inventados."""
    from app.db.models import Asistencia, Estudiante, Evaluacion, Matricula, Nota, SesionClase
    from app.services.prediction_service import prediction_service
    from app.api.predictions import calcular_semana_ciclo
    meta=regression_metadata()
    _,course,student=authorized_selection(db,user,selection)
    if student is None or course is None:return result("regresion_logistica","pending","Selecciona curso y estudiante autorizados para la inferencia.",variables=meta["variables"])
    path=ROOT / "models" / "asistencia_logreg.joblib"
    if not path.is_file():return result("regresion_logistica","unavailable","Falta el artefacto asistencia_logreg.joblib. Las métricas archivadas no permiten reconstruir probabilidades. No se reentrena.",variables=meta["variables"])
    now=datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    upcoming=db.scalars(select(SesionClase).where(SesionClase.curso_id==course,SesionClase.estado=="ACTIVA",SesionClase.fecha>=now.date()).order_by(SesionClase.fecha,SesionClase.hora_inicio).limit(101)).all()
    target=next((s for s in upcoming if datetime.combine(s.fecha,s.hora_inicio)>now),None)
    if target is None:return result("regresion_logistica","unavailable","Sin próxima sesión activa.",variables=meta["variables"])
    est=db.get(Estudiante,student)
    marks=db.execute(select(Asistencia,SesionClase).join(SesionClase,SesionClase.id==Asistencia.sesion_id).where(Asistencia.usuario_id==est.usuario_id,SesionClase.curso_id==course,SesionClase.estado!="CANCELADA",Asistencia.fecha>=now.date()-timedelta(days=30),Asistencia.fecha<=now.date()).order_by(SesionClase.fecha,SesionClase.hora_inicio,Asistencia.id).limit(1001)).all()
    history=[];seen=set()
    for mark,session in marks:
        if datetime.combine(session.fecha,session.hora_fin)>=now:continue
        if mark.fecha_registro is None or mark.fecha_registro>now or mark.fecha_registro<datetime.combine(session.fecha,session.hora_inicio) or session.fecha_registro is None or session.fecha_registro>now or mark.fecha!=session.fecha or mark.sesion_id in seen:return result("regresion_logistica","pending","Historial duplicado o sin fecha verificable.",variables=meta["variables"])
        state="TARDANZA" if mark.estado=="TARDE" else mark.estado
        if state not in {"PRESENTE","TARDANZA","AUSENTE"}:return result("regresion_logistica","pending","Estado histórico no reconocido.",variables=meta["variables"])
        seen.add(mark.sesion_id);history.append({"estado":state})
    grades=db.scalars(select(Nota.nota).join(Evaluacion,Evaluacion.id==Nota.evaluacion_id).where(Nota.estudiante_id==student,Evaluacion.curso_id==course,Nota.estado=="calificado",Nota.nota.is_not(None),Nota.registrada_en<=now,Evaluacion.creado_en<=now)).all()
    if not history or len(marks)>1000 or not grades:return result("regresion_logistica","pending","Historial o notas anteriores al corte insuficientes. No se imputan notas ficticias.",variables=meta["variables"])
    try:
        if target.fecha_registro is None or target.fecha_registro>now:raise ValueError("Programación desconocida al corte")
        promedio=sum(number(n,0,20) for n in grades)/len(grades)
        prediction=prediction_service.predict_for_student(historial=history[-30:],dia_semana=target.fecha.weekday(),hora_inicio=target.hora_inicio.hour,semana_ciclo=calcular_semana_ciclo(db,course,target.fecha),promedio_notas=promedio)
        probability=number(prediction["probabilidad"],0,1)
        return result("regresion_logistica","available","Inferencia del servicio existente; origen del entrenamiento no acreditado por manifiesto.",origin="sintetico" if DEMO_MODE else "sistema",version="sha256:"+hashlib.sha256(read_bytes(path,20_000_000)).hexdigest(),variables=meta["variables"],training_origin="no_verificado",probability=probability,target="asistencia, incluyendo tardanzas",cutoff=now.isoformat(),session_at=datetime.combine(target.fecha,target.hora_inicio).isoformat(),limitations="Ventana de 30 días, últimos 30 registros conocidos; posible cambio de dominio respecto del entrenamiento. No es una validación clínica ni una etiqueta de riesgo.")
    except (OSError,ValueError,KeyError,TypeError,ImportError):
        return result("regresion_logistica","unavailable","Servicio de regresión no disponible o incompatible. No se reentrena.",variables=meta["variables"])


def evaluation_catalog():
    return dict(models=[segmentation(),regression_metadata(),neural_status()],comparable=False,winner=None,comparison_reason="No existe una evaluación común verificada con el mismo objetivo, población, variables y división temporal. Silueta de K-Means no es accuracy. No se puede afirmar superioridad.")


def explain(q, model=None):
    if model in {"red_neuronal_parte6","regresion_logistica"} or re.search(r"diferencia|regresion|red neuronal|parte ?6",q):
        return "La regresión logística es supervisada: transforma una combinación lineal de variables en una probabilidad. La red neuronal de Parte 6 utiliza 9 entradas, capas ocultas de 32 y 16 neuronas ReLU y salida sigmoide; aprende relaciones no lineales. Ambas estiman asistencia, no puntualidad. Una regresión lineal estima cantidades continuas; el predictor de asistencia existente es logístico. No hay una comparación común verificada que permita declarar un ganador. Parte 6 aún no está integrada en esta rama."
    return "K-Means es aprendizaje no supervisado: agrupa perfiles próximos según sus variables estandarizadas y sus centroides. No predice asistencia futura ni asigna diagnósticos. La demostración guardada utiliza asistencia_ratio, tardanzas_ratio, promedio_notas y expresiones_positivas_ratio (exclusivamente sintética). E1, E2 y E3 son etiquetas de grupos, no niveles de riesgo. Sus descripciones se calculan de las medias guardadas, sin entrenar otra vez. No se usan expresiones faciales reales de EmoScan."


def ml_message(db,user,turn,selection):
    authorized_selection(db,user,selection)
    q=turn.body.message
    from app.services.chatbot_conversation import normalize
    q=normalize(q)
    intent=turn.intent
    payload=None
    if intent=="ML_EXPLAIN":
        reply=explain(q,turn.ml_model)
        if "variable" in q and turn.ml_model in {"red_neuronal_parte6","regresion_logistica"}:
            variables=NEURAL if turn.ml_model=="red_neuronal_parte6" else regression_metadata()["variables"]
            reply+="\nVariables del contrato: "+", ".join(variables)+"."
    elif intent=="ML_TARGET":reply=NOTICE
    elif intent=="ML_SAFETY":reply="No se permite utilizar datos faciales ni inferencias emocionales de EmoScan para clasificar riesgo académico. Los módulos permanecen independientes."
    elif intent=="ML_NEURAL":payload=neural_prediction(db,user,selection)
    elif intent=="ML_REGRESSION":payload=regression_prediction(db,user,selection)
    elif intent=="ML_SEGMENTS":
        personal=selection.get("student_id") is not None or bool(re.search(r"(?:segmentacion|cluster|grupo)s? (?:de|del) [a-z]|mis estudiantes|mi (?:grupo|cluster|segmento)|(?:mi|mis) curso|del curso|datos (?:reales|del sistema)",q))
        # Un estudiante puede ver la explicación general, pero su ID nunca se busca en el CSV sintético.
        payload=result("kmeans","pending","No existe un servicio de asignaciones académicas autorizadas en esta rama. La demostración sintética no clasifica estudiantes reales.",variables=FOUR) if personal else segmentation()
    if payload:
        reply=payload["reason"]
        if payload["status"]=="available":
            reply+=f"\nOrigen: {payload['origin']}. Versión: {payload['model_version']}. Variables: {', '.join(payload['variables'])}."
            if "probability" in payload:reply+=f"\nProbabilidad experimental de asistir: {payload['probability']:.2%}.\n"+NOTICE
            if "groups" in payload:
                reply+=f"\n{payload['profiles']} perfiles simulados; K={payload['k']}; silueta={payload['metrics']['silueta']:.6f}."
                for g in payload["groups"]:
                    m=g["means"];reply+=f"\n{g['group']}: {g['description']}; {g['profiles']} perfiles; asistencia {m['asistencia_ratio']:.1%}, tardanzas {m['tardanzas_ratio']:.1%}, nota {m['promedio_notas']:.2f}/20, expresiones sintéticas {m['expresiones_positivas_ratio']:.1%}."
            if payload.get("limitations"):reply+="\n"+payload["limitations"]
    return dict(reply=reply,intent=intent,data=[],provider="local",ml=payload or {"status":"educational","notice":NOTICE})
