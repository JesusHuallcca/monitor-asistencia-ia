"""Generación secuencial: el resultado se sortea después de construir sus antecedentes."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

def generate(seed=62, students=120, sessions=40):
    rng = np.random.default_rng(seed)
    rows = []
    for student in range(students):
        cohort = 0 if student < students*.6 else 1 if student < students*.8 else 2
        start = pd.Timestamp(['2025-01-02','2025-05-02','2025-09-02'][cohort])
        propensity = rng.normal(.5, .8)
        past = []; grade = float(np.clip(rng.normal(13, 2), 0, 20))
        for t in range(sessions):
            when = start + pd.Timedelta(days=3*t, hours=int(rng.choice([8,10,14,18])))
            ratio = np.mean(past[-10:]) if past else .6
            logit = -.5 + propensity + 1.25*ratio + .09*(grade-12) - .45*(when.hour==8) - .35*(when.dayofweek==0)
            present = int(rng.random() < 1/(1+np.exp(-logit)))
            state = ('TARDANZA' if rng.random()<.2 else 'PRESENTE') if present else 'AUSENTE'
            grade = float(np.clip(.8*grade+.2*rng.normal(13,3),0,20))
            rows.append(dict(student_id=f'SIN-{student+1:03}',session_at=when.isoformat(),estado=state,nota=round(grade,2),nota_disponible_at=(when+pd.Timedelta(days=1)).isoformat(),origen='sintetico'))
            past.append(present)
    return pd.DataFrame(rows)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,default=62); args=p.parse_args()
    path=ROOT/'datasets/sesiones_sinteticas.csv'; path.parent.mkdir(exist_ok=True)
    generate(args.seed).to_csv(path,index=False); print(path)

if __name__=='__main__': main()
