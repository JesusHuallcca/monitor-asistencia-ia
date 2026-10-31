"""Dataset verificado para todas las salidas. Sin Gemini, EmoScan o SQL libre."""
from collections import Counter,defaultdict
from datetime import datetime,time
from zoneinfo import ZoneInfo
import calendar
import math
import time as clock_time
import re
from fastapi import HTTPException
from sqlalchemy import and_,or_,select
from app.core.config import TIMEZONE,DEMO_MODE
from app.db.models import Asistencia,Curso,Estudiante,Evaluacion,Matricula,Nota,SesionClase,Usuario
from app.schemas.chatbot_reports import ReportSpec,ReportType
from app.services.chatbot_security import academic_scope,deny
from app.services.chatbot_conversation import MONTHS

MAX_ROWS=2000
TITLES={"asistencia":"Reporte de asistencia","tardanzas":"Reporte de tardanzas","ausencias":"Reporte de ausencias","academico":"Resumen académico del curso","comparacion":"Comparación de asistencia entre períodos"}
COLUMNS=[("fecha","Fecha"),("curso","Curso"),("estudiante","Estudiante"),("estado","Estado"),("periodo","Período")]
METHODOLOGY=("Fuente: registros académicos autorizados, sin datos de EmoScan. La asistencia se calcula como "
              "(PRESENTE + TARDANZA) / (PRESENTE + TARDANZA + AUSENTE). TARDE se normaliza a TARDANZA. "
              "No se imputan ausencias en sesiones sin registro. Estados desconocidos se muestran, pero no entran en el denominador. "
              "Los porcentajes describen observaciones registradas, no predicciones ni diagnósticos. "
              "La matrícula y los permisos se verifican al generar y descargar. Es una instantánea de los datos disponibles al generar.")

def indicators(rows):
    counts=Counter(row["estado"] for row in rows)
    known=sum(counts.get(state,0) for state in ("PRESENTE","TARDANZA","AUSENTE"))
    return {"registros":len(rows),"presentes":counts["PRESENTE"],"tardanzas":counts["TARDANZA"],"ausencias":counts["AUSENTE"],
            "sin_clasificar":len(rows)-known,"denominador_asistencia":known,
            "asistencia_pct":round(100*(counts["PRESENTE"]+counts["TARDANZA"])/known,2) if known else None}

def build_dataset(db,user,spec):
    scope=academic_scope(db,user)
    ids=list(scope.course_ids)
    if spec.course_id is not None:
        if spec.course_id not in ids:deny("report_course")
        ids=[spec.course_id]
    if len(ids)>50:raise HTTPException(413,"Selecciona un curso; el reporte no admite más de 50 cursos.")
    allowed={student.id for student,_,_ in db.execute(scope.students_query(ids)).unique()}
    if spec.student_id is not None:
        if spec.student_id not in allowed:deny("report_student")
        allowed={spec.student_id}
    if scope.own_student_id is not None:allowed&={scope.own_student_id}
    pairs=[(spec.period_start,spec.period_end)]
    if spec.compare_start:pairs.append((spec.compare_start,spec.compare_end))
    labels=[f"{start.isoformat()} a {end.isoformat()}" for start,end in pairs]
    query=(select(Asistencia.id,Estudiante.id.label("student_id"),Usuario.nombres,Usuario.apellidos,Curso.id.label("course_id"),Curso.nombre,SesionClase.fecha,Asistencia.estado)
           .join(SesionClase,Asistencia.sesion_id==SesionClase.id).join(Curso,Curso.id==SesionClase.curso_id)
           .join(Estudiante,Asistencia.usuario_id==Estudiante.usuario_id).join(Usuario,Usuario.id==Estudiante.usuario_id)
           .join(Matricula,and_(Matricula.estudiante_id==Estudiante.id,Matricula.curso_id==Curso.id))
           .where(Curso.id.in_(ids),Estudiante.id.in_(allowed),or_(*(and_(SesionClase.fecha>=start,SesionClase.fecha<=end) for start,end in pairs)))
           .distinct().order_by(SesionClase.fecha,Curso.id,Estudiante.id,Asistencia.id).limit(MAX_ROWS+1))
    raw=db.execute(query).all()
    if len(raw)>MAX_ROWS:raise HTTPException(413,"El reporte supera 2000 registros; reduce el curso o el período.")
    rows=[]
    for row in raw:
        state=str(row.estado).upper()
        if state=="TARDE":state="TARDANZA"
        label=next(label for label,(start,end) in zip(labels,pairs) if start<=row.fecha<=end)
        rows.append({"fecha":row.fecha.isoformat(),"curso":row.nombre,"estudiante":f"{row.nombres} {row.apellidos}".strip(),"estado":state,"periodo":label})
    metrics=indicators(rows)
    selected=rows
    if spec.report_type==ReportType.TARDANZAS:selected=[row for row in rows if row["estado"]=="TARDANZA"]
    if spec.report_type==ReportType.AUSENCIAS:selected=[row for row in rows if row["estado"]=="AUSENTE"]
    comparison=[dict(periodo=label,**indicators([row for row in rows if row["periodo"]==label])) for label in labels] if len(labels)>1 else []
    courses=[{"id":c.id,"nombre":c.nombre} for c in scope.courses if c.id in ids]
    grades=[]
    if spec.report_type==ReportType.ACADEMICO:
        # Promedio ponderado sobre evaluaciones ya calificadas y disponibles al cierre.
        grade_query=(select(Estudiante.id,Usuario.nombres,Usuario.apellidos,Curso.nombre,Evaluacion.curso_id,Nota.nota,Evaluacion.peso,Nota.id.label("note_id"))
            .join(Usuario,Usuario.id==Estudiante.usuario_id).join(Nota,Nota.estudiante_id==Estudiante.id)
            .join(Evaluacion,Evaluacion.id==Nota.evaluacion_id).join(Curso,Curso.id==Evaluacion.curso_id)
            .join(Matricula,and_(Matricula.estudiante_id==Estudiante.id,Matricula.curso_id==Curso.id))
            .where(Curso.id.in_(ids),Estudiante.id.in_(allowed),Nota.estado=="calificado",Nota.nota.is_not(None),Evaluacion.peso>0,
                   Nota.registrada_en<=datetime.combine(spec.period_end,time.max)).distinct().limit(MAX_ROWS+1))
        values=db.execute(grade_query).all()
        if len(values)>MAX_ROWS:raise HTTPException(413,"Demasiadas calificaciones; reduce los filtros.")
        grouped=defaultdict(list)
        for row in values:
            grade,weight=float(row.nota),float(row.peso)
            if not math.isfinite(grade) or not math.isfinite(weight) or not 0<=grade<=20:
                raise HTTPException(422,"Hay calificaciones inválidas en el ámbito; revisa los datos antes de exportar.")
            grouped[(row.id,row.curso_id,row.nombres,row.apellidos,row.nombre)].append((grade,weight))
        for (_,_,first,last,course),items in sorted(grouped.items()):
            grades.append({"curso":course,"estudiante":f"{first} {last}".strip(),"evaluaciones":len(items),"promedio_ponderado":round(sum(n*w for n,w in items)/sum(w for _,w in items),2)})
    chart=[]
    if selected:
        if comparison:chart=[{"label":r["periodo"],"value":r["asistencia_pct"],"unit":"%"} for r in comparison]
        elif spec.report_type in {ReportType.TARDANZAS,ReportType.AUSENCIAS}:
            count=Counter(row["curso"] for row in selected);chart=[{"label":k,"value":v,"unit":"registros"} for k,v in sorted(count.items())]
        else:
            count=Counter(row["estado"] for row in selected);chart=[{"label":state,"value":count[state],"unit":"registros"} for state in ("PRESENTE","TARDANZA","AUSENTE")]
    return {"schema_version":1,"title":TITLES[spec.report_type.value],"spec":spec.model_dump(mode="json"),
            "generated_at":datetime.now(ZoneInfo(TIMEZONE)).isoformat(),"source":"Base académica autorizada ("+db.get_bind().dialect.name+")",
            "synthetic":DEMO_MODE,"courses":courses,"periods":labels,"metrics":metrics,"report_rows":len(selected),
            "rows":selected,"comparison":comparison,"comparison_delta_pp":round(comparison[1]["asistencia_pct"]-comparison[0]["asistencia_pct"],2) if comparison and all(row["asistencia_pct"] is not None for row in comparison) else None,"grades":grades,"chart":chart,"methodology":METHODOLOGY,
            "grade_methodology":"Notas calificadas disponibles al cierre; promedio ponderado sobre pesos positivos. No reconstruye versiones históricas de notas modificadas. Sin calificaciones suficientes: Sin datos disponibles."}


def preview(key,entry,now=None):
    if now is None:now=clock_time.monotonic()
    data=entry.dataset()
    if data.get("kind")=="ml_evaluation":
        return dict(data,id=key,fingerprint=entry.fingerprint,rows=data["rows"][:25],expires_in=max(0,int(entry.expires-now)),formats=["xlsx","pdf","docx"],message="Métricas archivadas y disponibilidad; comparación no equivalente. Sin probabilidades inventadas.")
    return {"id":key,"fingerprint":entry.fingerprint,"title":data["title"],"generated_at":data["generated_at"],"source":data["source"],
            "synthetic":data["synthetic"],"courses":data["courses"],"periods":data["periods"],"spec":data["spec"],"metrics":data["metrics"],
            "report_rows":data["report_rows"],"columns":COLUMNS,"rows":data["rows"][:25],"grades":data["grades"][:25],
            "comparison":data["comparison"],"comparison_delta_pp":data["comparison_delta_pp"],"chart":data["chart"],"methodology":data["methodology"],"expires_in":max(0,int(entry.expires-now)),
            "message":"Sin datos disponibles" if not data["report_rows"] else f"Vista previa: {min(25,data['report_rows'])} de {data['report_rows']} registros. Los documentos incluyen todas las filas del reporte.",
            "formats":["xlsx","pdf","docx"]}
