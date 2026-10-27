import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services.segmentacion_service import MAX_BYTES, MODEL_SLOT, process_csv
from segmentacion.segmentacion_kmeans import DEFAULT_DATA, FEATURES, fit_segments, prepare_students

HEADERS = {'Content-Type': 'text/csv', 'X-CSV-Filename': 'prueba.csv'}


def upload(client, headers, data, **extra):
    return client.post('/api/segmentacion/procesar', headers={**HEADERS, **headers, **extra}, content=data)


@pytest.mark.parametrize('method,path', [('get', '/api/segmentacion/demo'), ('post', '/api/segmentacion/procesar')])
def test_auth_and_professor_only(integration, method, path):
    client, _, _, headers = integration
    assert getattr(client, method)(path).status_code == 401
    for uid in [2, 3, 4, 5]:
        assert getattr(client, method)(path, headers=headers(uid)).status_code == 403
    assert getattr(client, method)(path, headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_demo_and_upload_match_definitive_model(integration):
    client, _, _, headers = integration
    response = client.get('/api/segmentacion/demo', headers=headers())
    assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    data = response.json()
    assert data['variables'] == FEATURES
    assert data['metricas']['perfiles'] == 150
    assert data['metricas']['clusters'] == 3
    assert data['metricas']['silueta'] == pytest.approx(.237369, abs=1e-6)
    assert [p['perfiles'] for p in data['clusters']] == [45, 60, 45]
    expected = fit_segments(prepare_students(pd.read_csv(DEFAULT_DATA)))
    points = pd.DataFrame(data['puntos'])
    np.testing.assert_allclose(points[FEATURES + ['pca_1', 'pca_2']], expected['assigned'][FEATURES + ['pca_1', 'pca_2']])
    records = list(csv.DictReader(io.StringIO(data['csv_resultados'])))
    assert len(records) == 150 and all(r['origen_expresiones'] == 'sintetico' for r in records)
    uploaded = upload(client, headers(), DEFAULT_DATA.read_bytes())
    assert uploaded.status_code == 200
    legacy = uploaded.json()
    assert legacy['expresiones_categoricas'] is None
    for key in ['variables', 'metricas', 'puntos', 'clusters', 'centroides', 'siluetas', 'evaluacion_k']:
        assert legacy[key] == data[key]
    detail = data['expresiones_categoricas']
    assert detail['general']['total_observaciones'] == 6000
    assert sum(detail['general']['conteos'].values()) == 6000
    assert [g['total_observaciones'] for g in detail['por_cluster']] == [1800, 2400, 1800]


@pytest.mark.parametrize('change', [
    {'origen_datos': 'real'}, {'origen_datos': ''}, {'estado': 'INVALIDO'},
    {'promedio_notas': 'NaN'}, {'promedio_notas': 'inf'}, {'promedio_notas': 'veinte'},
    {'promedio_notas': 21}, {'promedio_notas': -1}, {'usuario_id': ''},
    {'usuario_id': '=CMD()'}, {'usuario_id': 1.5}, {'sesion': -2},
    {'foto': 'private'}, {'expresiones_positivas_ratio': .8},
])
def test_invalid_values_rejected(integration, change):
    client, _, _, headers = integration
    raw = pd.read_csv(DEFAULT_DATA).astype(object)
    for key, value in change.items():
        raw.loc[0, key] = value
    r = upload(client, headers(), raw.to_csv(index=False).encode())
    assert r.status_code == 422 and isinstance(r.json()['detail'], str)


@pytest.mark.parametrize('content', [b'', b'bad\xff', b'\x00', b'usuario_id;estado;promedio_notas;origen_datos\n',
    b'usuario_id,estado,estado,promedio_notas,origen_datos,sesion\n',
    b'usuario_id,estado,promedio_notas,origen_datos,sesion\n1,PRESENTE,15,sintetico\n'])
def test_malformed_files(integration, content):
    client, _, _, headers = integration
    assert upload(client, headers(), content).status_code == 422


def test_size_structure_and_capacity_limits(integration):
    client, _, _, headers = integration
    assert upload(client, headers(), b'x' * (MAX_BYTES + 1)).status_code == 413
    chunks = iter([b'x' * MAX_BYTES, b'x'])
    assert upload(client, headers(), chunks).status_code == 413
    assert upload(client, headers(), b'abc', **{'Content-Type': 'image/jpeg'}).status_code == 415
    assert upload(client, headers(), b'abc', **{'X-CSV-Filename': 'datos.exe'}).status_code == 422
    raw = pd.read_csv(DEFAULT_DATA)
    for bad in [raw.drop(columns='origen_datos'), pd.concat([raw, raw.iloc[:1]]), raw[raw.usuario_id <= 3],
                raw.assign(sesion_id=raw.sesion)]:
        assert upload(client, headers(), bad.to_csv(index=False).encode()).status_code == 422
    many = raw.iloc[:1].loc[raw.index[:1].repeat(10001)].copy()
    many['sesion'] = np.arange(1, 10002)
    assert upload(client, headers(), many.to_csv(index=False).encode()).status_code == 422
    many = many.iloc[:501].copy(); many['usuario_id'] = np.arange(1, 502)
    assert upload(client, headers(), many.to_csv(index=False).encode()).status_code == 422
    MODEL_SLOT.acquire()
    try:
        r = client.get('/api/segmentacion/demo', headers=headers())
        assert r.status_code == 503 and r.headers['retry-after'] == '3'
    finally:
        MODEL_SLOT.release()


def test_new_csv_is_computed_and_does_not_write_files(integration):
    client, _, _, headers = integration
    raw = pd.read_csv(DEFAULT_DATA)
    raw = raw[raw.usuario_id <= 20]
    root = Path(__file__).resolve().parents[3]
    before = {p for p in root.rglob('*') if p.is_file()}
    data = upload(client, headers(), raw.to_csv(index=False).encode()).json()
    assert data['metricas']['perfiles'] == 20
    expected = process_csv(raw.to_csv(index=False).encode())
    assert data == expected
    assert {p for p in root.rglob('*') if p.is_file()} == before


@pytest.mark.parametrize('profiles', [150, 20, 4])
def test_visual_diagnostics_match_four_dimensional_model(profiles):
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_samples
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits

    raw = pd.read_csv(DEFAULT_DATA)
    raw = raw[raw.usuario_id <= profiles]
    data = process_csv(raw.to_csv(index=False).encode())
    students = prepare_students(raw)
    expected = fit_segments(students)
    points = pd.DataFrame(data['puntos'])
    centers = pd.DataFrame(data['centroides'])
    silhouettes = pd.DataFrame(data['siluetas'])
    with threadpool_limits(limits=1):
        scaler = StandardScaler().fit(students[FEATURES])
        x = scaler.transform(students[FEATURES])
        pca = PCA(n_components=2, svd_solver='full').fit(x)
        expected_silhouettes = silhouette_samples(x, points.segmento)
    np.testing.assert_allclose(centers.valores_estandarizados.tolist(), expected['centros_estandarizados'], atol=1e-12)
    np.testing.assert_allclose(centers[['pca_1', 'pca_2']],
                               pca.transform(np.array(expected['centros_estandarizados'])), atol=1e-12)
    np.testing.assert_allclose(centers[FEATURES],
                               scaler.inverse_transform(np.array(expected['centros_estandarizados'])), atol=1e-12)
    np.testing.assert_allclose(silhouettes.silueta, expected_silhouettes, atol=1e-12)
    np.testing.assert_array_equal(silhouettes.usuario_id, points.usuario_id)
    np.testing.assert_array_equal(silhouettes.segmento, points.segmento)
    assert silhouettes.silueta.between(-1, 1).all()
    assert silhouettes.silueta.mean() == pytest.approx(data['metricas']['silueta'], abs=1e-12)
    assert set(centers.segmento) == set(points.segmento)
    if profiles == 4:
        singleton_ids = points.groupby('segmento').size().loc[lambda s: s == 1].index
        assert silhouettes.loc[silhouettes.segmento.isin(singleton_ids), 'silueta'].eq(0).all()
