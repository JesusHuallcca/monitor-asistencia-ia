"""Consultas académicas de Parte 6: solo lectura y siempre acotadas al profesor."""
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import select,or_,and_
from app.db.models import Usuario,Profesor,AsignacionProfesor,Curso,Matricula,Estudiante,SesionClase,Asistencia,Evaluacion,Nota
from red_neuronal.system_features import system_features

LIMITATION='Experimental: entrenado y evaluado solo con datos sintéticos. No validado académicamente con MySQL. No utilizar para decisiones académicas automatizadas.'

def now_local():return datetime.now(ZoneInfo('America/Lima')).replace(tzinfo=None)
def moment(s):return datetime.combine(s.fecha,s.hora_inicio)
def course_scope(db,user,course):
    found=db.scalar(select(Curso).join(AsignacionProfesor,AsignacionProfesor.curso_id==Curso.id).join(Profesor,Profesor.id==AsignacionProfesor.profesor_id).where(Profesor.usuario_id==user.id,Curso.id==course,Curso.activo.is_(True)))
    if found is None:raise HTTPException(404,'Curso no disponible para este profesor.')
    return found

def courses(db,user):
    rows=db.scalars(select(Curso).join(AsignacionProfesor,AsignacionProfesor.curso_id==Curso.id).join(Profesor,Profesor.id==AsignacionProfesor.profesor_id).where(Profesor.usuario_id==user.id,Curso.activo.is_(True)).distinct().order_by(Curso.nombre).limit(101)).all()
    if len(rows)>100:raise HTTPException(409,'El listado requiere paginación: hay más de 100 cursos autorizados.')
    return [dict(id=c.id,codigo=c.codigo,nombre=c.nombre) for c in rows[:100]]

def students(db,user,course):
    course_scope(db,user,course)
    rows=db.execute(select(Estudiante.id,Estudiante.codigo,Usuario.nombres,Usuario.apellidos).join(Matricula,Matricula.estudiante_id==Estudiante.id).join(Usuario,Usuario.id==Estudiante.usuario_id).where(Matricula.curso_id==course,Usuario.estado=='activo').order_by(Estudiante.codigo).limit(201)).all()
    if len(rows)>200:raise HTTPException(409,'El listado requiere paginación: hay más de 200 estudiantes en el curso.')
    return [dict(id=s.id,codigo=s.codigo,nombre=s.nombres+' '+s.apellidos) for s in rows[:200]]

def next_session(db,course,now):
    return db.scalar(select(SesionClase).where(SesionClase.curso_id==course,SesionClase.estado=='ACTIVA',or_(SesionClase.fecha>now.date(),and_(SesionClase.fecha==now.date(),SesionClase.hora_inicio>now.time()))).order_by(SesionClase.fecha,SesionClase.hora_inicio,SesionClase.id).limit(1))

def sessions(db,user,course,now=None):
    course_scope(db,user,course);s=next_session(db,course,now or now_local())
    return [] if s is None else [dict(id=s.id,session_at=moment(s).isoformat(),estado=s.estado)]

def context(db,user,course,student,session,now=None):
    now=now or now_local();course_scope(db,user,course)
    result=db.execute(select(Estudiante,Matricula).join(Matricula,Matricula.estudiante_id==Estudiante.id).join(Usuario,Usuario.id==Estudiante.usuario_id).where(Matricula.curso_id==course,Estudiante.id==student,Usuario.estado=='activo')).first()
    if result is None:raise HTTPException(404,'Estudiante no disponible en este curso autorizado.')
    est,enrollment=result
    target=next_session(db,course,now)
    if target is None or target.id!=session:raise HTTPException(409,'La sesión seleccionada ya no es la próxima sesión activa. Actualiza la selección.')
    blockers=[];warnings=[]
    if enrollment.matriculado_en is None:blockers.append('La matrícula no tiene fecha verificable.')
    if target.fecha_registro is None or target.fecha_registro>now:blockers.append('La programación no tiene fecha de disponibilidad válida.')
    # Solo sesiones concluidas y conocidas al consultar; no se infiere AUSENTE de un registro faltante.
    past=db.scalars(select(SesionClase).where(SesionClase.curso_id==course,SesionClase.estado!='CANCELADA',SesionClase.fecha<=now.date()).order_by(SesionClase.fecha,SesionClase.hora_inicio).limit(1001)).all()
    if len(past)>1000:blockers.append('El historial supera 1000 sesiones; se necesita una extracción completa auditada.')
    past=[s for s in past if datetime.combine(s.fecha,s.hora_fin)<now and (enrollment.matriculado_en is None or moment(s)>=enrollment.matriculado_en)]
    marks=db.execute(select(Asistencia.id,Asistencia.sesion_id,Asistencia.fecha,Asistencia.estado,Asistencia.fecha_registro).join(SesionClase,SesionClase.id==Asistencia.sesion_id).where(Asistencia.usuario_id==est.usuario_id,SesionClase.curso_id==course,SesionClase.fecha<=now.date())).all()
    grouped={}
    for mark in marks:grouped.setdefault(mark.sesion_id,[]).append(mark)
    history=[];rows=[]
    for s in past:
        entries=grouped.get(s.id,[]);state=None;reason=None
        if s.fecha_registro is None or s.fecha_registro>now:reason='Sesión sin fecha fiable de disponibilidad.'
        elif len(entries)!=1:reason='Falta un estado explícito.' if not entries else 'Existen registros duplicados.'
        else:
            mark=entries[0];state='TARDANZA' if mark.estado=='TARDE' else mark.estado
            if mark.fecha_registro is None or mark.fecha_registro>now:reason='Registro no disponible al corte.'
            elif state not in {'PRESENTE','TARDANZA','AUSENTE'}:reason='Estado no reconocido.'
            elif mark.fecha!=s.fecha or mark.fecha_registro<moment(s):reason='Fechas de asistencia inconsistentes.'
        rows.append(dict(sesion_id=s.id,session_at=moment(s).isoformat(),estado=state if reason is None else None,motivo=reason))
        if reason:blockers.append(f'Sesión {s.id}: {reason}')
        else:history.append(dict(session_at=moment(s).isoformat(),estado=state))
    known_notes=db.execute(select(Nota,Evaluacion).join(Evaluacion,Evaluacion.id==Nota.evaluacion_id).where(Nota.estudiante_id==est.id,Evaluacion.curso_id==course,Nota.estado=='calificado',Nota.nota.is_not(None))).all()
    grades=[]
    for note,evaluation in known_notes:
        if note.registrada_en is None or evaluation.creado_en is None:blockers.append('Hay una nota sin fecha verificable de disponibilidad.');continue
        if note.registrada_en>now or evaluation.creado_en>now:continue
        if note.registrada_en<evaluation.creado_en:blockers.append('Fechas de evaluación y nota inconsistentes.');continue
        grades.append(dict(nota=float(note.nota),available_at=note.registrada_en))
    row=None
    if len(history)<5:blockers.append('Historial insuficiente: se necesitan cinco sesiones anteriores con estado explícito.')
    if not blockers:
        try:row=system_features(history,grades,moment(target),now)
        except ValueError as exc:blockers.append(str(exc))
    warnings.append('Las notas son una media aritmética de evaluaciones calificadas del curso, sin ponderar y sin duplicarlas por asistencia. En entrenamiento son observaciones simuladas por sesión: existe cambio de dominio.')
    warnings.append('Solo se admite una consulta prospectiva al corte actual. El esquema no conserva versiones completas de notas, matrícula ni programación: no se reconstruyen predicciones históricas.')
    if row and row['sin_notas']:warnings.append('Sin notas disponibles: se utiliza el indicador sin_notas y promedio 0, como en el contrato del modelo; esta situación no aparece en el dataset de entrenamiento actual.')
    return dict(origen='mysql',experimental=True,training_origin='sintetico',ready=not blockers,curso_id=course,estudiante_id=student,sesion_id=session,session_at=moment(target).isoformat(),cutoff=now.isoformat(),history=rows,features=row,blockers=list(dict.fromkeys(blockers)),warnings=warnings,advertencia=LIMITATION,grades_count=len(grades))
