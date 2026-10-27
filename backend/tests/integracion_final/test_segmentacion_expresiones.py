"""Categorías adicionales: coherencia binaria, reproducibilidad y compatibilidad CSV."""
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services.segmentacion_expresiones import (
    CATEGORIES, COUNT_COLUMNS, TOTAL_COLUMN, ORIGIN_COLUMN,
    generate_counts, validate_optional_columns,
)
from app.services.segmentacion_service import process_csv, read_synthetic_csv
from segmentacion.segmentacion_kmeans import DEFAULT_DATA, FEATURES, prepare_students


@pytest.fixture(scope='module')
def category_source():
    raw = pd.read_csv(DEFAULT_DATA)
    students = prepare_students(raw)
    counts = generate_counts(students)
    return raw, students, counts


def test_original_binary_counts_are_preserved(category_source):
    raw, students, counts = category_source
    rng = np.random.default_rng(2026)
    expected = rng.binomial(40, rng.uniform(.05, .95, len(students)))
    np.testing.assert_array_equal(students.expresiones_positivas_conteo_simulado, expected)
    np.testing.assert_array_equal(counts.exp_sint_alegria, expected)
    np.testing.assert_array_equal(counts[list(COUNT_COLUMNS)].sum(axis=1), np.full(150, 40))
    np.testing.assert_allclose(counts.exp_sint_alegria / counts[TOTAL_COLUMN], students.expresiones_positivas_ratio)
    pd.testing.assert_frame_equal(counts, generate_counts(students))
    pd.testing.assert_frame_equal(counts.sort_values('usuario_id').reset_index(drop=True),
                                 generate_counts(students.iloc[::-1]).sort_values('usuario_id').reset_index(drop=True))


def test_zero_and_all_positive_profiles():
    students = pd.DataFrame({'usuario_id':[1, 2], 'muestras_expresiones_simuladas':[40,40],
                             'expresiones_positivas_conteo_simulado':[0,40]})
    counts = generate_counts(students)
    assert counts.exp_sint_alegria.tolist() == [0,40]
    assert counts[list(COUNT_COLUMNS)].sum(axis=1).tolist() == [40,40]
    assert counts.loc[1, list(COUNT_COLUMNS)].drop('exp_sint_alegria').eq(0).all()


def test_optional_csv_and_generated_demo_do_not_change_model(category_source):
    raw, students, counts = category_source
    base = process_csv(raw.to_csv(index=False).encode())
    demo = process_csv(raw.to_csv(index=False).encode(), generar_detalle=True)
    enriched = raw.merge(counts, on='usuario_id', validate='many_to_one')
    uploaded = process_csv(enriched.to_csv(index=False).encode())
    for key in ['variables','metricas','puntos','clusters','centroides','siluetas','evaluacion_k']:
        assert base[key] == demo[key] == uploaded[key]
    assert base['expresiones_categoricas'] is None
    assert demo['expresiones_categoricas']['por_perfil'] == uploaded['expresiones_categoricas']['por_perfil']
    detail = demo['expresiones_categoricas']
    assert detail['general']['total_observaciones'] == 6000
    assert sum(detail['general']['conteos'].values()) == 6000
    assert sum(detail['general']['porcentajes'].values()) == pytest.approx(100)
    for group in detail['por_cluster']:
        selected = [p for p in detail['por_perfil'] if p['segmento'] == group['segmento']]
        assert group['total_observaciones'] == len(selected)*40
        for category in CATEGORIES:
            assert group['conteos'][category] == sum(p['conteos'][category] for p in selected)
            assert group['porcentajes'][category] == pytest.approx(group['conteos'][category]*100/group['total_observaciones'])
    exported = pd.read_csv(io.StringIO(demo['csv_resultados']))
    assert exported[list(COUNT_COLUMNS)].sum(axis=1).eq(exported[TOTAL_COLUMN]).all()
    pd.testing.assert_frame_equal(exported[FEATURES+['segmento']], pd.read_csv(io.StringIO(base['csv_resultados']))[FEATURES+['segmento']])
    # Repeated counts in 45 sessions describe 40 independent simulated observations per profile.
    assert len(enriched) == 6750 and sum(p['total_observaciones'] for p in detail['por_perfil']) == 6000


@pytest.mark.parametrize('column,value', [
    ('exp_sint_neutral',-1), ('exp_sint_neutral',1.5), ('exp_sint_neutral',41),
    ('exp_sint_neutral','NaN'), ('exp_sint_neutral','abc'),
    ('exp_sint_total',0), ('exp_sint_total',39), ('exp_sint_origen','real'),
])
def test_invalid_optional_counts_rejected(category_source,column,value):
    raw, _, counts = category_source
    enriched = raw.merge(counts,on='usuario_id').astype(object)
    enriched.loc[0,column] = value
    with pytest.raises(ValueError):
        read_synthetic_csv(enriched.to_csv(index=False).encode())


def test_partial_and_inconsistent_profile_data_rejected(category_source):
    raw, _, counts = category_source
    with pytest.raises(ValueError, match='incompleto'):
        read_synthetic_csv(raw.assign(exp_sint_neutral=1).to_csv(index=False).encode())
    enriched = raw.merge(counts,on='usuario_id')
    inconsistent = enriched.copy()
    inconsistent.loc[0,'exp_sint_neutral'] += 1
    inconsistent.loc[0,'exp_sint_sorpresa'] -= 1
    with pytest.raises(ValueError, match='idénticos'):
        read_synthetic_csv(inconsistent.to_csv(index=False).encode())
    enriched['exp_sint_alegria'] += 1
    enriched['exp_sint_neutral'] -= 1
    # Use four complete profiles with enough neutral observations and unchanged sums.
    enriched = enriched[enriched.usuario_id <= 4]
    with pytest.raises(ValueError, match='conteo positivo'):
        process_csv(enriched.to_csv(index=False).encode())


def test_checked_in_example_is_reproducible(category_source):
    raw, students, counts = category_source
    root = Path(__file__).resolve().parents[3]
    sample = pd.read_csv(root/'frontend/ejemplos/segmentacion_sintetica_categorias.csv')
    pd.testing.assert_frame_equal(sample, raw.merge(counts,on='usuario_id'))
    profiles = pd.read_csv(root/'segmentacion/ejemplos/expresiones_categorias_por_perfil.csv')
    pd.testing.assert_frame_equal(profiles, students.merge(counts,on='usuario_id'))
