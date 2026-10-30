"""Entradas as-of: nunca incluyen la asistencia ni las notas de la sesión objetivo."""
import numpy as np
import pandas as pd

FEATURES = ['asistencia_30d','tardanzas_30d','asistencia_ultimas5','sesiones_previas','promedio_previo','sin_notas','dia_sin','dia_cos','hora']
STATES = {'PRESENTE','TARDANZA','AUSENTE'}
TRAIN_END = pd.Timestamp('2025-05-01')
VALID_END = pd.Timestamp('2025-09-01')

def features(history, target):
    target=pd.Timestamp(target)
    h=pd.DataFrame(history)
    if h.empty: raise ValueError('Se necesita al menos una sesión histórica.')
    dates=pd.to_datetime(h.session_at)
    if not (dates < target).all(): raise ValueError('Todas las sesiones históricas deben ser anteriores a la sesión objetivo.')
    if not h.estado.isin(STATES).all(): raise ValueError('Estado histórico desconocido.')
    h=h.assign(_date=dates).sort_values('_date')
    recent=h[h._date >= target-pd.Timedelta(days=30)]
    attended=lambda x: x.estado.isin(['PRESENTE','TARDANZA']).astype(float)
    grades=pd.to_numeric(h.nota,errors='raise')
    available=pd.to_datetime(h.nota_disponible_at)
    known=grades[(available < target) & grades.notna()]
    if ((grades.dropna()<0)|(grades.dropna()>20)).any(): raise ValueError('Las notas deben estar entre 0 y 20.')
    angle=2*np.pi*target.dayofweek/7
    return dict(zip(FEATURES,[float(attended(recent).mean()) if len(recent) else 0.,float((recent.estado=='TARDANZA').mean()) if len(recent) else 0.,float(attended(h.tail(5)).mean()),len(h),float(known.mean()) if len(known) else 0.,int(not len(known)),float(np.sin(angle)),float(np.cos(angle)),target.hour+target.minute/60]))

def prepare(raw):
    required={'student_id','session_at','estado','nota','nota_disponible_at','origen'}
    if not required.issubset(raw.columns): raise ValueError('Faltan columnas del historial sintético.')
    if not raw.origen.eq('sintetico').all(): raise ValueError('Este experimento admite únicamente datos sintéticos.')
    if raw.duplicated(['student_id','session_at']).any(): raise ValueError('Sesiones duplicadas.')
    if not raw.estado.isin(STATES).all(): raise ValueError('Estado desconocido.')
    rows=[]
    for sid,group in raw.groupby('student_id',sort=True):
        group=group.sort_values('session_at'); records=group.to_dict('records')
        for i,current in enumerate(records):
            if i<5: continue
            row=features(records[:i],current['session_at'])
            row.update(student_id=sid,session_at=current['session_at'],asistira=int(current['estado']!='AUSENTE'))
            rows.append(row)
    if not rows: raise ValueError('No hay suficientes sesiones para preparar ejemplos.')
    return pd.DataFrame(rows)

def split(frame):
    dates=pd.to_datetime(frame.session_at)
    parts=[frame[dates<TRAIN_END].copy(),frame[(dates>=TRAIN_END)&(dates<VALID_END)].copy(),frame[dates>=VALID_END].copy()]
    if any(p.empty or p.asistira.nunique()<2 for p in parts): raise ValueError('Cada partición necesita ejemplos de ambas clases.')
    for i in range(3):
        for j in range(i+1,3):
            if set(parts[i].student_id)&set(parts[j].student_id): raise ValueError('Un estudiante aparece en varias particiones; se requiere separar cohortes.')
    assert max(parts[0].session_at)<min(parts[1].session_at) and max(parts[1].session_at)<min(parts[2].session_at)
    return parts
