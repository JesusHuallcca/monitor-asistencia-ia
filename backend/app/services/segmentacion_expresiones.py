"""Desglose categórico sintético adicional. No modifica el modelo de cuatro variables."""
from __future__ import annotations

import hashlib
import numpy as np
import pandas as pd

CATEGORIES = ('neutral', 'alegria', 'sorpresa', 'tristeza', 'enojo', 'disgusto', 'miedo', 'desprecio')
LABELS = ('Neutral', 'Alegría', 'Sorpresa', 'Tristeza', 'Enojo', 'Disgusto', 'Miedo', 'Desprecio')
COUNT_COLUMNS = tuple('exp_sint_' + category for category in CATEGORIES)
TOTAL_COLUMN = 'exp_sint_total'
ORIGIN_COLUMN = 'exp_sint_origen'
OPTIONAL_COLUMNS = (*COUNT_COLUMNS, TOTAL_COLUMN, ORIGIN_COLUMN)
VERSION = 'desglose_sintetico_v1_semilla_2026'
# Pesos ilustrativos, no estimados de personas ni de un modelo facial.
REMAINING_WEIGHTS = np.array([.55, .15, .10, .08, .04, .05, .03])
CONVENTION = ('Desglose sintético adicional, no reconstrucción de categorías originales. '
              'Por convención de esta demostración, alegría conserva el conteo positivo binomial; '
              'el resto se reparte entre siete categorías con pesos ilustrativos. '
              'Son observaciones simuladas, no porcentajes de estudiantes que sienten emociones.')


def generate_counts(students: pd.DataFrame) -> pd.DataFrame:
    """RNG independiente por identificador: no consume el RNG del modelo."""
    rows = []
    for p in students.itertuples(index=False):
        uid = int(p.usuario_id)
        total = int(p.muestras_expresiones_simuladas)
        positive = int(p.expresiones_positivas_conteo_simulado)
        seed = int.from_bytes(hashlib.sha256(f'{VERSION}:{uid}:{total}:{positive}'.encode()).digest()[:8], 'little')
        other = np.random.default_rng(seed).multinomial(total - positive, REMAINING_WEIGHTS)
        values = [int(other[0]), positive, *(int(v) for v in other[1:])]
        rows.append({'usuario_id': uid, **dict(zip(COUNT_COLUMNS, values)),
                     TOTAL_COLUMN: total, ORIGIN_COLUMN: 'sintetico'})
    return pd.DataFrame(rows)


def validate_optional_columns(raw: pd.DataFrame) -> bool:
    present = set(raw.columns) & set(OPTIONAL_COLUMNS)
    if not present:
        return False
    if present != set(OPTIONAL_COLUMNS):
        raise ValueError('Detalle categórico incompleto: incluye las ocho columnas exp_sint_*, exp_sint_total y exp_sint_origen.')
    if not raw[ORIGIN_COLUMN].eq('sintetico').all():
        raise ValueError('exp_sint_origen debe ser sintetico en todas las filas.')
    for column in (*COUNT_COLUMNS, TOTAL_COLUMN):
        text = raw[column].astype(str)
        if not text.str.fullmatch(r'[0-9]{1,2}').all():
            raise ValueError(f'{column}: usa conteos enteros entre 0 y 40.')
        raw[column] = text.astype('int64')
        if not raw[column].between(0, 40).all():
            raise ValueError(f'{column}: usa conteos enteros entre 0 y 40.')
    if not raw[TOTAL_COLUMN].eq(40).all():
        raise ValueError('exp_sint_total debe ser 40, las observaciones sintéticas del modelo actual.')
    if not raw[list(COUNT_COLUMNS)].sum(axis=1).eq(raw[TOTAL_COLUMN]).all():
        raise ValueError('Las ocho categorías deben sumar exp_sint_total en cada perfil.')
    # Un perfil se repite en las filas de sesiones. Nunca sumar esos duplicados.
    if raw.groupby('usuario_id')[list(OPTIONAL_COLUMNS)].nunique(dropna=False).gt(1).any().any():
        raise ValueError('Los conteos por perfil deben repetirse idénticos en todas sus sesiones.')
    return True


def counts_from_csv(raw: pd.DataFrame, students: pd.DataFrame) -> pd.DataFrame | None:
    if not set(OPTIONAL_COLUMNS).issubset(raw.columns):
        return None
    counts = raw[['usuario_id', *OPTIONAL_COLUMNS]].drop_duplicates('usuario_id').copy()
    merged = students[['usuario_id', 'expresiones_positivas_conteo_simulado']].merge(counts, on='usuario_id', validate='one_to_one')
    if len(merged) != len(students) or not merged['exp_sint_alegria'].eq(merged.expresiones_positivas_conteo_simulado).all():
        raise ValueError('exp_sint_alegria debe coincidir con el conteo positivo sintético original; no se cambia la cuarta variable.')
    return counts


def summarize_counts(assigned: pd.DataFrame, counts: pd.DataFrame, method: str) -> dict:
    merged = assigned[['usuario_id', 'segmento']].merge(counts, on='usuario_id', validate='one_to_one')
    if len(merged) != len(assigned):
        raise ValueError('Se requieren conteos categóricos para todos los perfiles.')
    def summary(frame):
        values = {category: int(frame[column].sum()) for category, column in zip(CATEGORIES, COUNT_COLUMNS)}
        total = int(frame[TOTAL_COLUMN].sum())
        return {'total_observaciones': total, 'conteos': values,
                'porcentajes': {key: value * 100 / total if total else 0 for key, value in values.items()}}
    convention = CONVENTION if method == 'generado_determinista_adicional' else (
        'Conteos categóricos sintéticos proporcionados en el CSV y validados, no registros originales recuperados. '
        'Por convención académica, alegría conserva el conteo positivo binomial; las otras categorías proceden del CSV. '
        'Son observaciones simuladas, no porcentajes de estudiantes que sienten emociones.')
    return {'origen': 'sintetico', 'version': VERSION if method == 'generado_determinista_adicional' else 'conteos_csv_sinteticos_v1', 'metodo': method,
            'convencion': convention, 'categoria_positiva_por_convencion': 'alegria',
            'categorias': [{'id': key, 'nombre': label} for key, label in zip(CATEGORIES, LABELS)],
            'por_perfil': [{'usuario_id': int(row.usuario_id), 'segmento': int(row.segmento),
                           'total_observaciones': int(getattr(row, TOTAL_COLUMN)),
                           'conteos': {key: int(getattr(row, col)) for key, col in zip(CATEGORIES, COUNT_COLUMNS)}}
                          for row in merged.itertuples(index=False)],
            'general': summary(merged),
            'por_cluster': [{'segmento': int(segment), **summary(frame)}
                            for segment, frame in merged.groupby('segmento', sort=True)]}
