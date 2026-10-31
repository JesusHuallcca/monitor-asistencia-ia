from pathlib import Path
import json
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI,HTTPException
from fastapi.testclient import TestClient
from red_neuronal.api import create_router,get_predictor
from red_neuronal.prepare import prepare,split,FEATURES
from red_neuronal.evaluate import metrics
from red_neuronal.app import create_demo_app

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture(scope='module')
def model(): return get_predictor()
@pytest.fixture
def payload(model):
    ex=deepcopy(model.report['examples'][0]);return dict(origen='sintetico',session_at=ex['session_at'],history=ex['history'])

def client(role):
    def user():
        if role is None:raise HTTPException(401,'No autenticado')
        return SimpleNamespace(rol=role)
    app=FastAPI();app.include_router(create_router(user));return TestClient(app)

@pytest.mark.parametrize('role,status',[(None,401),('estudiante',403),('admin',403),('profesor',200)])
def test_authorization(role,status): assert client(role).get('/api/parte6/report').status_code==status

def test_scaler_train_only(model):
    raw=pd.read_csv(ROOT/'datasets/sesiones_sinteticas.csv');tr,_,_=split(prepare(raw))
    np.testing.assert_allclose(model.scaler.mean_,tr[FEATURES].mean().to_numpy(),atol=1e-10)
    assert model.scaler.n_samples_seen_==len(tr)

def test_real_metrics_recompute(model):
    test=pd.read_csv(ROOT/'artifacts/test_features.csv');x=model.scaler.transform(test[FEATURES]).astype('float32')
    for name,p in [('neuronal',model.model(x,training=False).numpy().ravel()),('logistica',model.baseline.predict_proba(x)[:,1])]:
        actual=metrics(test.asistira,p)
        for key in ['accuracy','precision','recall','f1','roc_auc','brier','log_loss']:assert actual[key]==pytest.approx(model.report['metrics'][name][key],abs=1e-6)
        assert actual['confusion_matrix']==model.report['metrics'][name]['confusion_matrix']

def test_prediction_format_and_repeat(payload):
    c=client('profesor');a=c.post('/api/parte6/predict',json=payload);b=c.post('/api/parte6/predict',json=payload)
    assert a.status_code==200 and a.json()==b.json()
    p=a.json();assert 0<=p['probabilidad']<=1 and len(p['features'])==9 and p['origen']=='sintetico'

@pytest.mark.parametrize('mutation',['target','future','duplicate','real','nan','large','unknown'])
def test_reject_invalid(payload,mutation):
    if mutation=='target':payload['asistira']=1
    if mutation=='future':payload['history'][0]['session_at']=payload['session_at']
    if mutation=='duplicate':payload['history'].append(payload['history'][0])
    if mutation=='real':payload['origen']='real'
    if mutation=='nan':payload['history'][0]['nota']='NaN'
    if mutation=='large':payload['history']=payload['history']*1001
    if mutation=='unknown':payload['history'][0]['estado']='OTRO'
    assert client('profesor').post('/api/parte6/predict',json=payload).status_code==422

def test_demo_session_is_explicit(payload):
    c=TestClient(create_demo_app());assert c.get('/api/parte6/report').status_code==401
    assert c.post('/api/parte6/demo/session',headers={'Origin':'https://otra-web.example'}).status_code==403
    r=c.post('/api/parte6/demo/session');assert r.status_code==200 and 'HttpOnly' in r.headers['set-cookie']
    assert c.post('/api/parte6/predict',json=payload).status_code==200

def test_frontend_assets():
    c=TestClient(create_demo_app());assert c.get('/profesor/red-neuronal.html').status_code==200
    for path in ['/js/red-neuronal.js','/css/red-neuronal.css','/vendor/plotly-cartesian-2.35.2.min.js']: assert c.get(path).status_code==200

@pytest.mark.parametrize('role,status',[(None,401),('estudiante',403),('admin',403),('profesor',200)])
def test_prediction_authorization(role,status,payload):
    assert client(role).post('/api/parte6/predict',json=payload).status_code==status

def test_missing_model_is_clear(monkeypatch):
    import red_neuronal.api as api
    def missing(): raise FileNotFoundError('local artifact missing')
    monkeypatch.setattr(api,'get_predictor',missing)
    response=client('profesor').get('/api/parte6/report')
    assert response.status_code==503 and 'red_neuronal.train' in response.json()['detail']
