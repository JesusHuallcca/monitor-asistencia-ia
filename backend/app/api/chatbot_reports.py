"""Generación, vista previa y descargas autenticadas del asistente existente."""
from dataclasses import replace
from datetime import date,datetime,timedelta
from enum import Enum
import calendar
import hashlib
import re
from zoneinfo import ZoneInfo
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import ValidationError
from app.api.deps import get_current_user
from app.core.config import TIMEZONE
from app.db.database import get_db
from app.schemas.chatbot_reports import ReportSpec,ReportType
from app.services import chatbot_report_store as storage
from app.services.chatbot_report_store import audit
from app.services.chatbot_reports import build_dataset,preview
from app.services.chatbot_report_documents import MIME,render
from app.services.chatbot_security import history_scope_key
from app.services.chatbot_conversation import MONTHS,normalize

router=APIRouter(prefix="/reports",tags=["Chatbot · reportes académicos"])
class Format(str,Enum):xlsx="xlsx";pdf="pdf";docx="docx"

def create_snapshot(db,user,spec):
    storage.store.limiter.check(user.id,"preview",10)
    scope=history_scope_key(db,user)
    data=build_dataset(db,user,spec)
    key,entry=storage.store.add(user.id,scope,data)
    audit("preview_created",actor=user.id)
    return preview(key,entry,storage.store.clock())

@router.post("")
def create_report(body:ReportSpec,user=Depends(get_current_user),db=Depends(get_db)):
    return create_snapshot(db,user,body)

@router.get("/{report_id}")
def report_preview(report_id:str,user=Depends(get_current_user),db=Depends(get_db)):
    storage.store.limiter.check(user.id,"read",30)
    entry=storage.store.get(report_id,user.id,history_scope_key(db,user))
    return preview(report_id,entry,storage.store.clock())

@router.post("/{report_id}/exports/{fmt}")
def export_report(report_id:str,fmt:Format,user=Depends(get_current_user),db=Depends(get_db)):
    storage.store.limiter.check(user.id,"export",6)
    entry=storage.store.get(report_id,user.id,history_scope_key(db,user))
    if fmt.value not in entry.files:
        if not storage.render_slots.acquire(blocking=False):raise HTTPException(503,"Hay dos exportaciones en curso; vuelve a intentar.",headers={"Retry-After":"3"})
        try:
            try:content=render(entry.dataset(),fmt.value,entry.fingerprint)
            except Exception:
                audit("render_failed",fmt.value,user.id)
                raise HTTPException(503,"No se pudo generar el documento. Revisa los filtros o vuelve a intentar.") from None
            # Reevaluar permisos al finalizar, antes de poner el archivo a disposición.
            db.expire_all()
            storage.store.get(report_id,user.id,history_scope_key(db,user))
            storage.store.cache(report_id,entry,fmt.value,content)
        finally:storage.render_slots.release()
    audit("export_generated",fmt.value,user.id)
    return {"url":f"/api/chatbot/reports/{report_id}/files/{fmt.value}","filename":f"reporte-{entry.dataset()['spec']['report_type']}.{fmt.value}",
            "fingerprint":entry.fingerprint,"file_sha256":hashlib.sha256(entry.files[fmt.value]).hexdigest(),"expires_in":max(0,int(entry.expires-storage.store.clock()))}

@router.get("/{report_id}/files/{fmt}")
def download_report(report_id:str,fmt:Format,user=Depends(get_current_user),db=Depends(get_db)):
    storage.store.limiter.check(user.id,"download",15)
    entry=storage.store.get(report_id,user.id,history_scope_key(db,user))
    content=entry.files.get(fmt.value)
    if content is None:raise HTTPException(404,"Primero genera este formato desde la vista previa.")
    audit("export_downloaded",fmt.value,user.id)
    return Response(content,media_type=MIME[fmt.value],headers={"Content-Disposition":f'attachment; filename="reporte-{entry.dataset()["spec"]["report_type"]}.{fmt.value}"',
        "Cache-Control":"no-store, private","Pragma":"no-cache","X-Content-Type-Options":"nosniff","X-Report-Dataset-SHA256":entry.fingerprint})


def report_message(db,user,turn,selection):
    q=normalize(turn.body.message)
    # Nunca convertir expresiones de EmoScan en informes docentes o diagnósticos.
    if re.search(r"emoscan|emocion|facial|psicolog|diagnostic",q):
        raise HTTPException(400,"Estos reportes son exclusivamente académicos; no incluyen EmoScan ni diagnósticos emocionales.")
    formats=[fmt for pattern,fmt in [(r"excel|xlsx","xlsx"),(r"pdf|imprim","pdf"),(r"word|docx","docx")] if re.search(pattern,q)]
    temporal=any(re.search(r"\b"+month+r"\b",q) for month in MONTHS) or bool(re.search(r"semana|este mes|mes pasado|hoy|ayer",q))
    changed=any(field in turn.explicit_fields for field in ("course_id","student_id","period_start","period_end"))
    explicit_type=bool(re.search(r"asistencia|tardanza|retraso|falta|ausencia|academico|compara|historial|resumen mensual",q))
    reused=turn.report_id and not re.search(r"nuevo|actualiza|refresca",q) and not temporal and not changed and not explicit_type and (formats or re.search(r"mismo|vista previa|reporte|informe|descarg",q))
    if reused:
        entry=storage.store.get(turn.report_id,user.id,history_scope_key(db,user));result=preview(turn.report_id,entry,storage.store.clock())
    else:
        kind=ReportType.ASISTENCIA
        if turn.report_id and not explicit_type:
            previous=storage.store.get(turn.report_id,user.id,history_scope_key(db,user)).dataset()
            if previous.get("kind")!="ml_evaluation":kind=ReportType(previous["spec"]["report_type"])
        if re.search(r"compara",q):kind=ReportType.COMPARACION
        elif re.search(r"academico|notas|calificacion",q):kind=ReportType.ACADEMICO
        elif re.search(r"falta|ausencia",q):kind=ReportType.AUSENCIAS
        elif re.search(r"tardanza|retraso",q):kind=ReportType.TARDANZAS
        if selection["course_id"] is None and re.search(r"\bmi curso\b",q):
            raise HTTPException(400,"Selecciona el curso en el filtro antes de generar su reporte.")
        today=datetime.now(ZoneInfo(TIMEZONE)).date()
        start=turn.start or (today-timedelta(days=365) if "historial" in q else today.replace(day=1))
        end=turn.end or today
        if turn.start and turn.end:end=turn.end
        if start>end:end=start.replace(day=calendar.monthrange(start.year,start.month)[1])
        values=dict(report_type=kind,course_id=selection["course_id"],student_id=selection["student_id"],period_start=start,period_end=end)
        if kind==ReportType.COMPARACION:
            matches=list(re.finditer(r"\b("+"|".join(MONTHS)+r")(?:\s+(?:de\s+)?(20\d{2}))?\b",q))
            if len(matches)!=2:raise HTTPException(400,"Indica exactamente dos meses para comparar, por ejemplo septiembre y octubre de 2026.")
            spans=[]
            explicit_years={m.group(2) for m in matches if m.group(2)}
            default_year=int(next(iter(explicit_years))) if len(explicit_years)==1 else today.year
            for match in matches:
                month=MONTHS.index(match.group(1))+1;year=int(match.group(2)) if match.group(2) else default_year
                spans.append((date(year,month,1),date(year,month,calendar.monthrange(year,month)[1])))
            values.update(period_start=spans[0][0],period_end=spans[0][1],compare_start=spans[1][0],compare_end=spans[1][1])
        elif sum(bool(re.search(r"\b"+m+r"\b",q)) for m in MONTHS)>1:
            raise HTTPException(400,"Para dos meses pide una comparación o indica un rango en los filtros de fechas.")
        try:spec=ReportSpec.model_validate(values)
        except ValidationError:raise HTTPException(422,"Los períodos del reporte son incompatibles o superan el rango permitido.")
        result=create_snapshot(db,user,spec)
    turn.report_id=result["id"]
    spec=result["spec"];turn.start=date.fromisoformat(spec["period_start"]);turn.end=date.fromisoformat(spec["period_end"])
    if spec.get("compare_start"):
        turn.start=min(turn.start,date.fromisoformat(spec["compare_start"]))
        turn.end=max(turn.end,date.fromisoformat(spec["compare_end"]))
    selection.update(course_id=spec["course_id"],student_id=spec["student_id"])
    reply=result["title"]+". "+result["message"]+"\nPeríodo: "+"; ".join(result["periods"])+"."
    if formats:reply+=" Seleccioné "+", ".join(fmt.upper() for fmt in formats)+"; revisa la vista previa y pulsa Descargar."
    else:reply+=" Revisa la vista previa y elige Excel, PDF o Word."
    return {"reply":reply,"intent":"REPORT","provider":"local","data":[],"report":dict(result,requested_formats=formats)}
