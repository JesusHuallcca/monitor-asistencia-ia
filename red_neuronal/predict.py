from pathlib import Path
import json,joblib
import pandas as pd
from .prepare import FEATURES,features

class Predictor:
    def __init__(self,artifacts=Path(__file__).parent/'artifacts'):
        import hashlib
        path=Path(artifacts)
        self.manifest=json.loads((path/'model_manifest.json').read_text(encoding='utf-8'))
        if set(self.manifest['files'])!={'best.keras','scaler.joblib','logistic.joblib'}:raise ValueError('Manifiesto incompleto.')
        for name,digest in self.manifest['files'].items():
            if name not in {'best.keras','scaler.joblib','logistic.joblib'} or hashlib.sha256((path/name).read_bytes()).hexdigest()!=digest:raise ValueError('Artefacto incompatible con el manifiesto.')
        import tensorflow as tf
        self.report=json.loads((path/'report.json').read_text(encoding='utf-8'))
        canonical=json.dumps(self.report,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
        if hashlib.sha256(canonical).hexdigest()!=self.manifest['report_canonical_sha256']:raise ValueError('Reporte incompatible con el manifiesto.')
        self.features=FEATURES
        if self.report['features']!=FEATURES: raise ValueError('Esquema del modelo incompatible.')
        self.scaler=joblib.load(path/'scaler.joblib'); self.baseline=joblib.load(path/'logistic.joblib')
        self.model=tf.keras.models.load_model(path/'best.keras')
        actual=[dict(name=l.name,units=l.units,activation=l.activation.__name__,parameters=l.count_params()) for l in self.model.layers]
        if actual!=self.report['architecture'] or self.model.count_params()!=self.report['parameters']:raise ValueError('La arquitectura guardada no coincide con el reporte.')
        if list(self.scaler.feature_names_in_)!=FEATURES or self.model.input_shape[-1]!=len(FEATURES):raise ValueError('Escalador o entradas incompatibles.')
        self.report=dict(self.report,architecture=actual,parameters=self.model.count_params(),model_info=self.model_info())


    def predict(self,history,session_at):
        row=features(history,session_at); x=self.scaler.transform(pd.DataFrame([row])[FEATURES]).astype('float32')
        p=float(self.model(x,training=False).numpy()[0,0]); b=float(self.baseline.predict_proba(x)[0,1])
        return dict(probabilidad=p,prediccion=int(p>=.5),umbral=.5,logistica_probabilidad=b,features=row,origen='sintetico',advertencia='Demostración con datos sintéticos; no es una certeza ni una evaluación individual real.')

    def predict_features(self,row):
        import numpy as np
        if list(row)!=FEATURES or not np.isfinite(list(row.values())).all():raise ValueError('Orden o valores de las nueve entradas incompatible.')
        x=self.scaler.transform(pd.DataFrame([row])[FEATURES]).astype('float32')
        probability=float(self.model(x,training=False).numpy()[0,0])
        baseline=float(self.baseline.predict_proba(x)[0,1])
        return dict(probabilidad=probability,logistica_probabilidad=baseline,umbral=.5)

    def model_info(self):
        return dict(model_version=self.manifest['version'],model_sha256=self.manifest['files']['best.keras'],scaler_sha256=self.manifest['files']['scaler.joblib'],training_origin='sintetico',feature_order=FEATURES.copy())
