"""Ejemplo aislado de categorías sintéticas: no reescribe el generador original."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend')]
import pandas as pd
from app.services.segmentacion_expresiones import generate_counts
from segmentacion.segmentacion_kmeans import DEFAULT_DATA, prepare_students

if __name__ == '__main__':
    raw = pd.read_csv(DEFAULT_DATA)
    students = prepare_students(raw, expression_seed=2026, samples=40)
    counts = generate_counts(students)
    sample = ROOT / 'frontend/ejemplos/segmentacion_sintetica_categorias.csv'
    raw.merge(counts, on='usuario_id', validate='many_to_one').to_csv(sample, index=False, lineterminator='\n')
    profiles = ROOT / 'segmentacion/ejemplos/expresiones_categorias_por_perfil.csv'
    profiles.parent.mkdir(parents=True, exist_ok=True)
    students.merge(counts, on='usuario_id', validate='one_to_one').to_csv(profiles, index=False, lineterminator='\n')
    print('Ejemplos sintéticos generados: 150 perfiles, 40 observaciones por perfil, 6000 en total.')
    print('Los conteos por perfil se repiten en las sesiones del CSV de carga; no se suman repetidos.')
