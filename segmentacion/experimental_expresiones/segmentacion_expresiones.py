"""Segunda modalidad de Parte 3: cuatro variables, exclusivamente sintéticas."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(HERE / '.cache' / 'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ACADEMIC = HERE.parent
DEFAULT_DATA = ACADEMIC / 'datos_asistencia_sinteticos.csv'
FEATURES = ['asistencia_ratio', 'tardanzas_ratio', 'promedio_notas', 'expresiones_positivas_ratio']
ACADEMIC_FEATURES = FEATURES[:3]


def prepare_students(raw: pd.DataFrame, expression_seed=2026, samples=40):
    """No lee expresiones externas: genera la cuarta variable después de agregar."""
    if not isinstance(samples, int) or samples < 1:
        raise ValueError('Las muestras simuladas deben ser un entero positivo.')
    required = {'usuario_id', 'estado', 'promedio_notas', 'origen_datos'}
    if not required.issubset(raw.columns) or raw.empty:
        raise ValueError('Faltan columnas académicas obligatorias o el CSV está vacío.')
    if any('expresion' in str(name).lower() for name in raw.columns):
        raise ValueError('No se admiten expresiones de entrada; se generan exclusivamente datos sintéticos.')
    df = raw.copy(deep=True)
    if df[list(required)].isna().any().any() or not df.origen_datos.eq('sintetico').all():
        raise ValueError('Esta modalidad solo admite origen_datos=sintetico, sin faltantes.')
    key = next((name for name in ('sesion_id', 'sesion') if name in df), None)
    if key is None:
        raise ValueError('Se requiere sesion_id o sesion.')
    keys = ['usuario_id'] + (['curso_id'] if 'curso_id' in df else []) + [key]
    if df[keys].isna().any().any() or df.duplicated(keys).any():
        raise ValueError('Identificadores incompletos o sesiones duplicadas.')
    df['estado'] = df.estado.astype(str).str.strip().str.upper()
    if not set(df.estado).issubset({'PRESENTE', 'TARDANZA', 'AUSENTE'}):
        raise ValueError('Estados de asistencia no válidos.')
    df['promedio_notas'] = pd.to_numeric(df.promedio_notas, errors='raise')
    if not np.isfinite(df.promedio_notas).all() or not df.promedio_notas.between(0, 20).all():
        raise ValueError('Las notas deben ser finitas y estar entre 0 y 20.')
    df['asistencia_ratio'] = df.estado.isin(['PRESENTE', 'TARDANZA']).astype(float)
    df['tardanzas_ratio'] = df.estado.eq('TARDANZA').astype(float)
    students = df.groupby('usuario_id', sort=True).agg(
        sesiones_observadas=('estado', 'size'),
        asistencia_ratio=('asistencia_ratio', 'mean'),
        tardanzas_ratio=('tardanzas_ratio', 'mean'),
        promedio_notas=('promedio_notas', 'mean'),
    ).reset_index()
    if len(students) < 4:
        raise ValueError('Se requieren al menos cuatro perfiles ficticios.')
    # No usa asistencia, tardanzas, notas ni perfiles del generador para simular expresiones.
    rng = np.random.default_rng(expression_seed)
    probabilities = rng.uniform(.05, .95, len(students))
    counts = rng.binomial(samples, probabilities)
    students['expresiones_positivas_conteo_simulado'] = counts
    students['muestras_expresiones_simuladas'] = samples
    students['expresiones_positivas_ratio'] = counts / samples
    students['origen_datos'] = 'sintetico'
    students['origen_expresiones'] = 'sintetico'
    students['modalidad'] = 'experimental_4_variables'
    return students


def elbow_hint(evaluation):
    """Mayor distancia bajo la cuerda de la curva normalizada: solo una heurística."""
    k = evaluation.k.to_numpy(float)
    inertia = evaluation.inercia.to_numpy(float)
    if len(k) < 3 or inertia[0] <= inertia[-1]:
        return None
    x = (k - k[0]) / (k[-1] - k[0])
    y = (inertia - inertia[-1]) / (inertia[0] - inertia[-1])
    distances = 1 - x - y
    return int(k[np.argmax(distances)]) if distances.max() > 1e-10 else None


def fit_segments(students, seed=42, max_k=8):
    if max_k < 3:
        raise ValueError('max_k debe ser >=3, para comparar con la entrega original.')
    if not all(name in students for name in FEATURES) or len(students) < 4:
        raise ValueError('Se necesitan cuatro variables y al menos cuatro perfiles.')
    for name in ('origen_datos', 'origen_expresiones'):
        if name not in students or not students[name].eq('sintetico').all():
            raise ValueError('Ambos orígenes deben ser sintéticos.')
    values = students[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Variables no finitas.')
    for name in (FEATURES[0], FEATURES[1], FEATURES[3]):
        if not students[name].between(0, 1).all():
            raise ValueError('Las proporciones deben estar entre 0 y 1.')
    if not students.promedio_notas.between(0, 20).all():
        raise ValueError('Notas fuera del rango 0–20.')
    scaler = StandardScaler()
    x = scaler.fit_transform(values)
    upper = min(max_k, len(x)-1, len(np.unique(x, axis=0)))
    if upper < 3:
        raise ValueError('No hay al menos tres perfiles numéricos distintos.')
    records, models = [], {}
    with threadpool_limits(limits=1):
        for k in range(2, upper+1):
            model = KMeans(n_clusters=k, random_state=seed, n_init=30, max_iter=500)
            labels = model.fit_predict(x)
            if len(np.unique(labels)) != k:
                continue
            score = silhouette_score(x, labels, sample_size=min(5000, len(x)), random_state=seed)
            records.append({'k': k, 'inercia': float(model.inertia_), 'silueta': float(score)})
            models[k] = model
    evaluation = pd.DataFrame(records)
    if evaluation.empty or evaluation[evaluation.k >= 3].empty:
        raise ValueError('No se pudieron evaluar al menos tres segmentos distintos.')
    ranked = evaluation.sort_values(['silueta', 'k'], ascending=[False, True])
    chosen = int(ranked[ranked.k >= 3].iloc[0].k)
    model = models[chosen]
    centers = scaler.inverse_transform(model.cluster_centers_)
    order = np.argsort(centers[:, 0], kind='stable')
    mapping = {int(old): new+1 for new, old in enumerate(order)}
    assigned = students.copy(deep=True)
    assigned['segmento'] = [mapping[int(label)] for label in model.labels_]
    assigned['nombre_segmento'] = assigned.segmento.map(lambda label: f'E{label}')
    with threadpool_limits(limits=1):
        pca = PCA(n_components=2, svd_solver='full')
        coordinates = pca.fit_transform(x)
    assigned['pca_1'], assigned['pca_2'] = coordinates[:, 0], coordinates[:, 1]
    summary = assigned.groupby('segmento')[FEATURES].mean()
    summary.insert(0, 'perfiles', assigned.groupby('segmento').size())
    return {'assigned': assigned, 'summary': summary, 'evaluation': evaluation,
            'k': chosen, 'k_global': int(ranked.iloc[0].k), 'k_codo': elbow_hint(evaluation),
            'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist(),
            'centros_estandarizados': model.cluster_centers_[order].tolist(),
            'pca_variance': pca.explained_variance_ratio_.tolist()}


def plot_results(result, output):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    for segment, group in result['assigned'].groupby('segmento'):
        axes[0, 0].scatter(group.pca_1, group.pca_2, s=35, alpha=.8, label=f'E{segment}')
    variance = result['pca_variance']
    axes[0, 0].set(title='PCA 2D: proyección de las cuatro variables',
                   xlabel=f'PC1 ({variance[0]:.1%})', ylabel=f'PC2 ({variance[1]:.1%})')
    axes[0, 0].legend()
    matrix = np.array(result['centros_estandarizados'])
    limit = max(1., float(np.abs(matrix).max()))
    heat = axes[0, 1].imshow(matrix, cmap='RdBu_r', vmin=-limit, vmax=limit, aspect='auto')
    axes[0, 1].set_xticks(range(4), ['Asistencia', 'Tardanzas', 'Notas', 'Expresiones\nSINTÉTICAS'])
    axes[0, 1].set_yticks(range(result['k']), [f'E{i+1}' for i in range(result['k'])])
    axes[0, 1].set_title('Centroides estandarizados (z); no son diagnósticos')
    fig.colorbar(heat, ax=axes[0, 1], label='Desviaciones estándar respecto a la media')
    ev = result['evaluation']
    axes[1, 0].plot(ev.k, ev.silueta, 'o-')
    axes[1, 0].axvline(result['k'], ls='--', color='tab:red', label=f"Elegido k={result['k']} (k≥3)")
    axes[1, 0].set(title='Silueta: separación interna, no exactitud', xlabel='k', ylabel='Silueta media')
    axes[1, 0].legend()
    axes[1, 1].plot(ev.k, ev.inercia, 'o-')
    if result['k_codo'] is not None:
        axes[1, 1].axvline(result['k_codo'], ls=':', color='tab:orange',
                           label=f"Codo orientativo: {result['k_codo']}")
        axes[1, 1].legend()
    axes[1, 1].set(title='Método del codo: revisar visualmente', xlabel='k', ylabel='Inercia (cuatro variables z)')
    for ax in (axes[0, 0], axes[1, 0], axes[1, 1]):
        ax.grid(alpha=.2)
    fig.suptitle('Parte 3 experimental · DATOS 100 % SINTÉTICOS · Sin captura facial real', fontsize=15)
    fig.savefig(output / 'visualizacion_experimental.png', dpi=160)
    plt.close(fig)


def write_report(result, metadata, output):
    score = float(result['evaluation'].loc[result['evaluation'].k == result['k'], 'silueta'].iloc[0])
    lines = ['# Resultados experimentales: cuatro variables sintéticas', '',
             '**No son estudiantes reales ni resultados obtenidos por EmoScan.**', '',
             f"Se agregaron {metadata['filas_entrada']} sesiones en {len(result['assigned'])} perfiles ficticios.", '',
             f"K elegido: **{result['k']}**, silueta **{score:.4f}** entre k≥3. "
             f"Mejor k global: **{result['k_global']}**. Codo orientativo: **{result['k_codo']}**.", '',
             'Se conserva k≥3 para comparar el procedimiento con la entrega académica. '
             'No demuestra un número natural de grupos. Si silueta y codo difieren, se informa la discrepancia; '
             'la elección usa silueta y el codo es apoyo exploratorio.', '',
             f"PCA conserva **{sum(result['pca_variance']):.1%}** de la varianza estandarizada en dos dimensiones. "
             'K-Means se ajustó en cuatro dimensiones, antes de PCA.', '',
             '## Características observadas en esta simulación', '',
             '| Grupo | Perfiles | Asistencia | Tardanzas/sesiones | Nota media | Ratio de expresiones SINTÉTICO |',
             '|---|---:|---:|---:|---:|---:|']
    for segment, row in result['summary'].iterrows():
        lines.append(f'| E{segment} | {int(row.perfiles)} | {row.asistencia_ratio:.1%} | '
                     f'{row.tardanzas_ratio:.1%} | {row.promedio_notas:.2f} | {row.expresiones_positivas_ratio:.1%} |')
    lines += ['', 'Los grupos E1…Ek se numeran por asistencia media ascendente. '
              'No se emparejan automáticamente con S1…Sk de la modalidad original.', '']
    for segment, row in result['summary'].iterrows():
        lines.append(f'- E{segment}: {int(row.perfiles)} perfiles; asistencia {row.asistencia_ratio:.1%}, '
                     f'tardanzas {row.tardanzas_ratio:.1%}, nota media {row.promedio_notas:.2f} y '
                     f'ratio simulado {row.expresiones_positivas_ratio:.1%}. Son medias descriptivas de esta muestra ficticia.')
    lines += ['', '## Procedencia e interpretación', '',
              f"La cuarta variable es conteo binomial simulado / {metadata['muestras_expresiones']} muestras ficticias "
              'por perfil. Se sorteó una probabilidad uniforme entre 0.05 y 0.95 por perfil y después un conteo binomial. '
              'No se derivó de fotografías, notas ni asistencia. No se importó ni invocó EmoScan.', '',
              '«Positivas» es exclusivamente el nombre de una categoría ficticia de esta demostración. '
              'No afirma que una persona tenga emociones positivas ni permite interpretar atención, '
              'rendimiento futuro o riesgo de deserción.', '',
              'La independencia del mecanismo generador no impide correlaciones accidentales en una muestra finita. '
              'StandardScaler da escala comparable a todas las variables: incluso una variable sintética puede '
              'cambiar la geometría y los grupos. Un cambio de silueta no demuestra utilidad de expresiones reales. '
              'Las inercias de tres y cuatro dimensiones no son directamente comparables.', '',
              'El CSV académico debe declarar origen_datos=sintetico. Esa declaración no certifica por sí sola '
              'una fuente desconocida; usar solamente el archivo sintético distribuido o simulaciones propias.', '',
              '## Reproducibilidad', '',
              f"Semilla K-Means: {metadata['semilla_kmeans']}; semilla expresiones: {metadata['semilla_expresiones']}. "
              'n_init=30; max_iter=500; un hilo de cálculo; versiones y hash de entrada en metricas_experimentales.json.', '']
    (output / 'descripcion_experimental.md').write_text('\n'.join(lines), encoding='utf-8')


def run(dataset=DEFAULT_DATA, output=HERE/'resultados', seed=42, expression_seed=2026, max_k=8, samples=40):
    dataset, output = Path(dataset).resolve(), Path(output).resolve()
    if not dataset.is_relative_to(ACADEMIC):
        raise ValueError('La entrada debe estar dentro de segmentacion; no se consultan fuentes externas.')
    if not output.is_relative_to(HERE):
        raise ValueError('La salida debe estar dentro de experimental_expresiones, nunca sobre los resultados originales.')
    raw = pd.read_csv(dataset)
    students = prepare_students(raw, expression_seed, samples)
    result = fit_segments(students, seed, max_k)
    metadata = {'modalidad': 'experimental_4_variables', 'origen_datos': 'sintetico',
                'origen_expresiones': 'sintetico', 'fuente': dataset.relative_to(ACADEMIC).as_posix(),
                'sha256_entrada': hashlib.sha256(dataset.read_bytes()).hexdigest(),
                'filas_entrada': len(raw), 'perfiles': len(students), 'variables': FEATURES,
                'semilla_kmeans': seed, 'semilla_expresiones': expression_seed,
                'muestras_expresiones': samples, 'n_init': 30, 'max_iter': 500,
                'k_elegido': result['k'], 'k_mejor_global': result['k_global'], 'k_codo_orientativo': result['k_codo'],
                'regla_k': 'Mayor silueta entre k>=3; k global y codo se informan por separado',
                'evaluacion': result['evaluation'].to_dict(orient='records'),
                'scaler_media': result['scaler_mean'], 'scaler_escala': result['scaler_scale'],
                'varianza_pca': result['pca_variance'],
                'correlaciones_muestrales': students[FEATURES].corr().to_dict(),
                'versiones': {'numpy': np.__version__, 'pandas': pd.__version__,
                             'scikit-learn': sklearn.__version__, 'matplotlib': matplotlib.__version__}}
    output.mkdir(parents=True, exist_ok=True)
    students.to_csv(output/'datos_experimentales_sinteticos.csv', index=False, encoding='utf-8-sig')
    result['assigned'].to_csv(output/'segmentos_experimentales.csv', index=False, encoding='utf-8-sig')
    result['summary'].to_csv(output/'resumen_segmentos.csv', encoding='utf-8-sig')
    result['evaluation'].to_csv(output/'evaluacion_k_experimental.csv', index=False)
    (output/'metricas_experimentales.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    plot_results(result, output)
    write_report(result, metadata, output)
    print(f"DATOS SINTÉTICOS | {len(students)} perfiles | k={result['k']} | global={result['k_global']} | codo={result['k_codo']}")
    print(result['evaluation'].to_string(index=False))
    print(result['summary'].to_string())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--output-dir', type=Path, default=HERE/'resultados')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--seed-expresiones', type=int, default=2026)
    parser.add_argument('--max-k', type=int, default=8)
    parser.add_argument('--muestras-expresiones', type=int, default=40)
    args = parser.parse_args()
    try:
        run(args.dataset, args.output_dir, args.seed, args.seed_expresiones, args.max_k, args.muestras_expresiones)
    except (ValueError, OSError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    main()
