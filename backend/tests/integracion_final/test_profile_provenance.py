"""La carga de perfiles jamás convierte datos sin procedencia en sintéticos."""
import pandas as pd
import pytest
from app.services.segmentacion_service import read_synthetic_csv

def profiles():
    return pd.DataFrame({
        "usuario_id":[1,2,3,4],"asistencia_ratio":[.5,.7,.8,.9],
        "tardanzas_ratio":[.1,.2,.1,.1],"promedio_notas":[10,12,14,16],
        "expresiones_positivas_ratio":[.25,.5,.6,.7],
        "origen_datos":["sintetico"]*4,"origen_expresiones":["sintetico"]*4})

@pytest.mark.parametrize("mutation",["missing_origin","real_origin","missing_expression_origin","bad_grade","duplicate_id","facial"])
def test_profile_provenance_rejects_unverified_and_invalid(mutation):
    frame=profiles()
    if mutation=="missing_origin":frame=frame.drop(columns="origen_datos")
    elif mutation=="real_origin":frame.loc[0,"origen_datos"]="real"
    elif mutation=="missing_expression_origin":frame=frame.drop(columns="origen_expresiones")
    elif mutation=="bad_grade":frame.loc[0,"promedio_notas"]=21
    elif mutation=="duplicate_id":frame.loc[0,"usuario_id"]=2
    else:frame["foto"]="forbidden"
    with pytest.raises(ValueError):
        read_synthetic_csv(frame.to_csv(index=False).encode())

def test_verified_profile_values_are_preserved():
    frame=profiles()
    result=read_synthetic_csv(frame.to_csv(index=False).encode())
    for name in ["asistencia_ratio","tardanzas_ratio","promedio_notas","expresiones_positivas_ratio"]:
        assert result[name].tolist()==frame[name].tolist()
