"""Adaptador en memoria del K-Means definitivo de Parte 3. Sin acceso a BD."""
from __future__ import annotations

import csv
import io
import threading

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_samples
from threadpoolctl import threadpool_limits

from segmentacion.segmentacion_kmeans import FEATURES, fit_segments, prepare_students

from app.services.segmentacion_expresiones import (OPTIONAL_COLUMNS, validate_optional_columns,
    generate_counts, counts_from_csv, summarize_counts)

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10_000
MAX_PROFILES = 500
REQUIRED = {'usuario_id', 'estado', 'promedio_notas', 'origen_datos'}
ALLOWED = REQUIRED | {
    'sesion', 'sesion_id', 'curso_id', 'fecha', 'asistencia_ratio_30d',
    'asistencias_consecutivas', 'ausencias_consecutivas', 'dia_semana',
    'hora_inicio_clase', 'es_inicio_ciclo', 'tardanzas_ratio', 'asistira', 'perfil',
}
ALLOWED |= set(OPTIONAL_COLUMNS)
MODEL_SLOT = threading.BoundedSemaphore(1)


class SegmentationBusy(Exception):
    pass


def read_synthetic_csv(content: bytes) -> pd.DataFrame:
    if not content or len(content) > MAX_BYTES:
        raise ValueError('El CSV debe contener datos y no superar 2 MiB.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise ValueError('Guarda el CSV en UTF-8, separado por comas.') from error
    if '\x00' in text:
        raise ValueError('El archivo contiene bytes nulos; selecciona un CSV de texto.')
    try:
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        columns = next(reader, [])
        if not columns or len(columns) != len(set(columns)):
            raise ValueError('La cabecera está vacía o contiene columnas duplicadas.')
        missing = REQUIRED - set(columns)
        if missing:
            raise ValueError('Faltan columnas obligatorias: ' + ', '.join(sorted(missing)) + '.')
        sessions = set(columns) & {'sesion', 'sesion_id'}
        if len(sessions) != 1:
            raise ValueError('Incluye exactamente una columna de sesión: sesion o sesion_id.')
        unknown = set(columns) - ALLOWED
        if unknown:
            raise ValueError('Columnas no admitidas: ' + ', '.join(sorted(unknown)) +
                             '. Solo se admiten conteos categóricos sintéticos documentados; no ratios externos, imágenes ni datos faciales.')
        rows = []
        for line, row in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                raise ValueError('El límite es de 10000 filas de sesiones.')
            if len(row) != len(columns):
                raise ValueError(f'Fila {line}: el número de campos no coincide con la cabecera.')
            if any(len(value) > 128 for value in row):
                raise ValueError(f'Fila {line}: un campo supera los 128 caracteres.')
            rows.append(row)
    except csv.Error as error:
        raise ValueError('CSV mal formado: revisa las comillas y los separadores.') from error
    if not rows:
        raise ValueError('El CSV no contiene sesiones.')
    frame = pd.DataFrame(rows, columns=columns)
    if not frame.origen_datos.eq('sintetico').all():
        raise ValueError('Cada fila debe declarar origen_datos=sintetico. Solo se admite la demostración sintética.')
    for name in ['usuario_id', *sorted(sessions), *(['curso_id'] if 'curso_id' in frame else [])]:
        if not frame[name].str.fullmatch(r'[1-9][0-9]{0,14}').all():
            raise ValueError(f'{name}: usa identificadores enteros positivos de hasta 15 dígitos.')
        frame[name] = frame[name].astype('int64')
    try:
        frame['promedio_notas'] = pd.to_numeric(frame.promedio_notas, errors='raise')
    except (ValueError, TypeError) as error:
        raise ValueError('promedio_notas debe contener números entre 0 y 20; usa punto decimal.') from error
    if not np.isfinite(frame.promedio_notas).all() or not frame.promedio_notas.between(0, 20).all():
        raise ValueError('promedio_notas debe contener valores finitos entre 0 y 20.')
    profiles = frame.usuario_id.nunique()
    if not 4 <= profiles <= MAX_PROFILES:
        raise ValueError('Se requieren entre 4 y 500 perfiles sintéticos distintos.')
    validate_optional_columns(frame)
    return frame


def process_csv(content: bytes, *, generar_detalle: bool = False) -> dict:
    if not MODEL_SLOT.acquire(blocking=False):
        raise SegmentationBusy('Hay otra segmentación en curso. Inténtalo de nuevo en unos segundos.')
    try:
        raw = read_synthetic_csv(content)
        students = prepare_students(raw.drop(columns=list(OPTIONAL_COLUMNS), errors='ignore'), expression_seed=2026, samples=40)
        result = fit_segments(students, seed=42, max_k=8)
        # Visualization-only diagnostics from the same four standardized attributes.
        # Do not fit another K-Means or alter its labels, metrics or selection of K.
        x = (students[FEATURES].to_numpy(dtype=float) - np.asarray(result['scaler_mean'])) / np.asarray(result['scaler_scale'])
        assigned = result['assigned']
        with threadpool_limits(limits=1):
            individual = silhouette_samples(x, assigned.segmento.to_numpy(), metric='euclidean')
            # Reproduce the model's full-SVD PCA basis to project its actual centers.
            projection = PCA(n_components=2, svd_solver='full').fit(x)
            projected_centers = projection.transform(np.asarray(result['centros_estandarizados']))
        if not np.allclose(projection.transform(x), assigned[['pca_1', 'pca_2']].to_numpy(), atol=1e-10):
            raise ValueError('No se pudo verificar la proyección de los centroides.')
        centroids = [
            {'segmento': int(segment), 'pca_1': float(pc[0]), 'pca_2': float(pc[1]),
             'valores_estandarizados': values,
             **{name: float(value) for name, value in zip(
                 FEATURES, np.asarray(values) * np.asarray(result['scaler_scale']) + np.asarray(result['scaler_mean']))}}
            for segment, pc, values in zip(result['summary'].index, projected_centers, result['centros_estandarizados'])
        ]
        silhouettes = [
            {'usuario_id': int(uid), 'segmento': int(segment), 'silueta': float(value)}
            for uid, segment, value in zip(assigned.usuario_id, assigned.segmento, individual)
        ]
        counts = counts_from_csv(raw, students)
        method = 'csv_sintetico_validado'
        if counts is None and generar_detalle:
            counts = generate_counts(students)
            method = 'generado_determinista_adicional'
        detail = summarize_counts(assigned, counts, method) if counts is not None else None
        exported = assigned.merge(counts, on='usuario_id', validate='one_to_one') if counts is not None else assigned
        score = float(result['evaluation'].loc[result['evaluation'].k == result['k'], 'silueta'].iloc[0])
        return {
            'modalidad': 'principal_4_variables',
            'origen_datos': 'sintetico',
            'origen_expresiones': 'sintetico',
            'variables': FEATURES,
            'metricas': {'perfiles': len(students), 'sesiones': len(raw),
                         'clusters': result['k'], 'silueta': score,
                         'k_mejor_global': result['k_global'], 'k_codo': result['k_codo'],
                         'varianza_pca': result['pca_variance']},
            'puntos': result['assigned'].to_dict(orient='records'),
            'clusters': result['summary'].reset_index().to_dict(orient='records'),
            'centroides': centroids,
            'siluetas': silhouettes,
            'evaluacion_k': result['evaluation'].to_dict(orient='records'),
            'expresiones_categoricas': detail,
            'csv_resultados': exported.to_csv(index=False, lineterminator='\n'),
        }
    finally:
        MODEL_SLOT.release()
