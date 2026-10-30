import numpy as np
import pandas as pd
import pytest
from red_neuronal.generate import generate
from red_neuronal.prepare import FEATURES,prepare,split,features

@pytest.fixture(scope='module')
def raw(): return generate()

def test_reproducible(raw): pd.testing.assert_frame_equal(raw,generate())
def test_seed_changes(raw): assert not raw.equals(generate(63))
def test_temporal_and_students(raw):
    tr,va,te=split(prepare(raw))
    assert len(tr)==2520 and len(va)==840 and len(te)==840
    assert set(tr.student_id).isdisjoint(te.student_id)
    assert set(tr.student_id).isdisjoint(va.student_id)
    assert max(tr.session_at)<min(va.session_at)<min(te.session_at)
    assert all(p.asistira.nunique()==2 for p in [tr,va,te])

def test_current_and_future_targets_cannot_change_features(raw):
    a=prepare(raw.iloc[:40]);changed=raw.iloc[:40].copy();changed.loc[changed.index[20:],'estado']='AUSENTE';changed.loc[changed.index[20:],'nota']=0
    b=prepare(changed)
    np.testing.assert_allclose(a.iloc[15][FEATURES].astype(float),b.iloc[15][FEATURES].astype(float))

def test_future_grade_is_not_used():
    h=[dict(session_at='2025-01-01',estado='PRESENTE',nota=20,nota_disponible_at='2025-01-10')]
    f=features(h,'2025-01-05');assert f['sin_notas']==1 and f['promedio_previo']==0
    with pytest.raises(ValueError):features(h,'2025-01-01')

def test_target_and_identity_not_inputs(): assert not {'asistira','student_id','estado','session_at'}&set(FEATURES)
def test_origin_validation(raw):
    raw=raw.copy();raw.loc[0,'origen']='real'
    with pytest.raises(ValueError):prepare(raw)
def test_duplicate_validation(raw):
    with pytest.raises(ValueError):prepare(pd.concat([raw,raw.iloc[:1]]))
def test_shared_student_rejected(raw):
    frame=prepare(raw);frame.loc[frame.student_id=='SIN-073','student_id']='SIN-001'
    with pytest.raises(ValueError):split(frame)
