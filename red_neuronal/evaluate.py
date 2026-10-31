"""Métricas de test con umbral predefinido 0.5, sin selección usando test."""
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix,roc_auc_score,brier_score_loss,log_loss

def metrics(y,p):
    p=np.asarray(p); pred=(p>=.5).astype(int)
    return dict(accuracy=float(accuracy_score(y,pred)),precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),roc_auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,brier=float(brier_score_loss(y,p)),log_loss=float(log_loss(y,p,labels=[0,1])),confusion_matrix=confusion_matrix(y,pred,labels=[0,1]).tolist())

def main():
    from .predict import Predictor
    p=argparse.ArgumentParser(); p.add_argument('--artifacts',type=Path,default=Path(__file__).parent/'artifacts'); a=p.parse_args()
    import pandas as pd
    obj=Predictor(a.artifacts); test=pd.read_csv(a.artifacts/'test_features.csv'); x=obj.scaler.transform(test[obj.features])
    print(json.dumps({'neuronal':metrics(test.asistira,obj.model(x,training=False).numpy().ravel()),'logistica':metrics(test.asistira,obj.baseline.predict_proba(x)[:,1])},indent=2))
if __name__=='__main__': main()
