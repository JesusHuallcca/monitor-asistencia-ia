"""Adaptación de observaciones académicas, sin modificar el pipeline entrenado."""
import numpy as np
import pandas as pd
from .prepare import FEATURES,features

def system_features(history,grades,target,cutoff):
    target=pd.Timestamp(target);cutoff=pd.Timestamp(cutoff)
    if cutoff>=target:raise ValueError('Solo se permite predecir una sesión todavía futura.')
    if len(history)<5:raise ValueError('Se necesitan al menos cinco sesiones anteriores con estado explícito.')
    if len({h['session_at'] for h in history})!=len(history):raise ValueError('Hay sesiones duplicadas.')
    if any(pd.Timestamp(h['session_at'])>=cutoff for h in history):raise ValueError('El historial incluye sesiones no disponibles en el corte.')
    # Los eventos de nota se agregan una sola vez por evaluación; nunca se repiten en un join.
    empty=[dict(h,nota=None,nota_disponible_at=h['session_at']) for h in history]
    row=features(empty,target)
    known=[]
    for g in grades:
        if g['available_at'] is None:raise ValueError('Una nota no tiene fecha fiable de disponibilidad.')
        if pd.Timestamp(g['available_at'])>=cutoff:continue
        value=float(g['nota'])
        if not np.isfinite(value) or not 0<=value<=20:raise ValueError('Nota fuera de la escala 0–20.')
        known.append(value)
    row['promedio_previo']=float(np.mean(known)) if known else 0.
    row['sin_notas']=int(not known)
    if list(row)!=FEATURES or not np.isfinite(list(row.values())).all():raise ValueError('Esquema de entradas incompatible.')
    return row
