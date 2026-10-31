"""Entrena ambas familias con el mismo escalador, variables y partición temporal."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS','0')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
from pathlib import Path
import argparse,json,hashlib,platform
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .prepare import FEATURES,prepare,split
from .evaluate import metrics

ROOT=Path(__file__).parent

def train(dataset=ROOT/'datasets/sesiones_sinteticas.csv',out=ROOT/'artifacts',epochs=80,seed=62):
    import tensorflow as tf
    tf.config.threading.set_inter_op_parallelism_threads(1); tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.keras.utils.set_random_seed(seed); tf.config.experimental.enable_op_determinism()
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(dataset); frame=prepare(raw); tr,va,te=split(frame)
    scaler=StandardScaler().fit(tr[FEATURES]); x=[scaler.transform(p[FEATURES]).astype('float32') for p in [tr,va,te]]
    y=[p.asistira.to_numpy(dtype='float32') for p in [tr,va,te]]
    model=tf.keras.Sequential([tf.keras.layers.Input((len(FEATURES),),name='historia'),tf.keras.layers.Dense(32,activation='relu',name='oculta_32'),tf.keras.layers.Dense(16,activation='relu',name='oculta_16'),tf.keras.layers.Dense(1,activation='sigmoid',name='probabilidad')])
    model.compile(optimizer=tf.keras.optimizers.Adam(.001),loss='binary_crossentropy')
    options=tf.data.Options(); options.threading.private_threadpool_size=1
    trainset=tf.data.Dataset.from_tensor_slices((x[0],y[0])).shuffle(len(tr),seed=seed,reshuffle_each_iteration=True).batch(64).with_options(options)
    valset=tf.data.Dataset.from_tensor_slices((x[1],y[1])).batch(64).with_options(options)
    history=model.fit(trainset,validation_data=valset,epochs=epochs,verbose=2,shuffle=False,callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=10,restore_best_weights=True),tf.keras.callbacks.ModelCheckpoint(str(out/'best.keras'),monitor='val_loss',save_best_only=True)])
    model=tf.keras.models.load_model(out/'best.keras')
    baseline=LogisticRegression(max_iter=2000,random_state=seed).fit(x[0],y[0])
    joblib.dump(scaler,out/'scaler.joblib'); joblib.dump(baseline,out/'logistic.joblib')
    te.to_csv(out/'test_features.csv',index=False)
    probs=model(x[2],training=False).numpy().ravel(); bp=baseline.predict_proba(x[2])[:,1]
    predictions=te[['student_id','session_at','asistira']].copy(); predictions['neuronal']=probs; predictions['logistica']=bp; predictions.to_csv(out/'test_predictions.csv',index=False)
    examples=[]
    for _,row in te.iloc[[0,len(te)//2,-1]].iterrows():
        h=raw[(raw.student_id==row.student_id)&(raw.session_at<row.session_at)]
        examples.append(dict(student_id=row.student_id,session_at=row.session_at,history=h[['session_at','estado','nota','nota_disponible_at']].to_dict('records')))
    report=dict(origen='sintetico',features=FEATURES,architecture=[dict(name=l.name,units=l.units,activation=l.activation.__name__,parameters=l.count_params()) for l in model.layers],parameters=model.count_params(),seed=seed,versions=dict(python=platform.python_version(),tensorflow=tf.__version__,keras=tf.keras.__version__),dataset_sha256=hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),history={k:[float(v) for v in values] for k,values in history.history.items()},best_epoch=int(np.argmin(history.history['val_loss'])+1),threshold=.5,splits=[dict(name=n,rows=len(p),students=int(p.student_id.nunique()),start=p.session_at.min(),end=p.session_at.max(),positive_rate=float(p.asistira.mean())) for n,p in zip(['entrenamiento','validacion','prueba'],[tr,va,te])],metrics=dict(neuronal=metrics(y[2],probs),logistica=metrics(y[2],bp)),examples=examples)
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report['metrics'],indent=2)); return report

def main():
    p=argparse.ArgumentParser(); p.add_argument('--epochs',type=int,default=80);p.add_argument('--seed',type=int,default=62);p.add_argument('--dataset',type=Path,default=ROOT/'datasets/sesiones_sinteticas.csv');p.add_argument('--out',type=Path,default=ROOT/'artifacts');a=p.parse_args()
    if a.epochs<1: p.error('--epochs debe ser positivo')
    train(a.dataset,a.out,a.epochs,a.seed)
if __name__=='__main__': main()
