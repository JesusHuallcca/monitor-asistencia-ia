from datetime import datetime,timedelta
from pathlib import Path
import json
import pytest
from pydantic import ValidationError
from red_neuronal.api import get_predictor
from red_neuronal.inference import HistoricalInputs,AttendanceInference
from red_neuronal.prepare import features

@pytest.fixture
def values():
    ex=get_predictor().report['examples'][0]
    return features(ex['history'],ex['session_at'])

def test_internal_inference_and_provenance(values):
    predictor=get_predictor();target=datetime.fromisoformat(predictor.report['examples'][0]['session_at']);result=AttendanceInference().predict(values,source='sintetico',cutoff=target-timedelta(hours=1),session_at=target)
    assert result['probabilidad']==pytest.approx(predictor.predict_features(values)['probabilidad'])
    assert result['model_version']=='parte6-dense-9x32x16x1-v1' and len(result['model_sha256'])==64
    assert result['training_origin']=='sintetico' and result['feature_order']==list(values)

@pytest.mark.parametrize('key,value',[('asistencia_30d',1.1),('tardanzas_30d',-1),('promedio_previo',21),('hora',24),('sesiones_previas',4),('asistencia_ultimas5','NaN'),('sin_notas',2),('dia_sin',.1)])
def test_invalid_values(values,key,value):
    values[key]=value
    with pytest.raises(ValidationError):HistoricalInputs.model_validate(values)

def test_target_and_unknown_columns_rejected(values):
    with pytest.raises(ValidationError):HistoricalInputs.model_validate(dict(values,asistira=1))

def test_future_cutoff_rejected(values):
    with pytest.raises(ValidationError):AttendanceInference().predict(values,source='mysql_experimental',cutoff=datetime(2025,1,2),session_at=datetime(2025,1,1))

def test_manifest_matches_actual_files():
    import hashlib
    root=Path(__file__).resolve().parents[1]/'artifacts';manifest=json.loads((root/'model_manifest.json').read_text())
    for name,digest in manifest['files'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest

def test_calendar_must_match_target(values):
    target=datetime.fromisoformat(get_predictor().report['examples'][0]['session_at'])+timedelta(days=1)
    with pytest.raises(ValueError):AttendanceInference().predict(values,source='sintetico',cutoff=target-timedelta(hours=1),session_at=target)
