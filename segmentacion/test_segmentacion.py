"""Pruebas sin backend, cámara ni base de datos. Temporales dentro de esta modalidad."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import numpy as np
import pandas as pd

from segmentacion.segmentacion_kmeans import DEFAULT_DATA, FEATURES, HERE, elbow_hint, fit_segments, prepare_students, plot_results, run


class PrincipalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(DEFAULT_DATA)
        cls.students = prepare_students(cls.raw)

    def test_preserves_academic_aggregates_and_does_not_mutate_input(self):
        before = self.raw.copy(deep=True)
        actual = prepare_students(self.raw).set_index('usuario_id')
        expected = self.raw.assign(
            asistencia_ratio=self.raw.estado.isin(['PRESENTE', 'TARDANZA']).astype(float),
            tardanzas_ratio=self.raw.estado.eq('TARDANZA').astype(float),
        ).groupby('usuario_id')[FEATURES[:3]].mean()
        np.testing.assert_allclose(actual[FEATURES[:3]], expected.loc[actual.index], atol=1e-12)
        pd.testing.assert_frame_equal(before, self.raw)
        self.assertEqual(len(actual), 150)

    def test_synthetic_counts_reproducible_even_after_row_shuffle(self):
        again = prepare_students(self.raw.sample(frac=1, random_state=8))
        pd.testing.assert_frame_equal(again, self.students)
        np.testing.assert_allclose(self.students.expresiones_positivas_ratio,
                                   self.students.expresiones_positivas_conteo_simulado / 40)
        self.assertTrue(self.students.origen_expresiones.eq('sintetico').all())
        self.assertTrue(self.students.expresiones_positivas_ratio.between(0, 1).all())
        other = prepare_students(self.raw, expression_seed=1)
        self.assertFalse(other.expresiones_positivas_ratio.equals(self.students.expresiones_positivas_ratio))

    def test_simulation_does_not_depend_on_grades_attendance_or_targets(self):
        changed = self.raw.copy()
        changed['promedio_notas'] = 1.
        changed['estado'] = 'AUSENTE'
        changed['perfil'] = 'ignored'
        changed['asistira'] = 999
        actual = prepare_students(changed)
        np.testing.assert_array_equal(actual.expresiones_positivas_ratio, self.students.expresiones_positivas_ratio)

    def test_invalid_or_non_synthetic_sources_rejected(self):
        for name, value in [('origen_datos', 'real'), ('origen_datos', 'no_verificado'),
                            ('estado', 'INVALIDO'), ('promedio_notas', np.inf),
                            ('promedio_notas', 21), ('usuario_id', None)]:
            bad = self.raw.copy()
            bad.loc[0, name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare_students(bad)
        for bad in (self.raw.assign(expresiones_positivas_ratio=.5),
                    pd.concat([self.raw, self.raw.iloc[:1]]), self.raw.iloc[:0],
                    self.raw.drop(columns='origen_datos')):
            with self.assertRaises(ValueError):
                prepare_students(bad)
        with self.assertRaises(ValueError):
            prepare_students(self.raw, samples=0)

    def test_four_features_used_scaling_and_k_selection(self):
        first = fit_segments(self.students)
        self.assertEqual(len(first['scaler_mean']), 4)
        np.testing.assert_allclose(first['scaler_mean'], self.students[FEATURES].mean())
        np.testing.assert_allclose(first['scaler_scale'], self.students[FEATURES].std(ddof=0))
        self.assertTrue(first['evaluation'].silueta.between(-1, 1).all())
        self.assertTrue((np.diff(first['evaluation'].inercia) <= 1e-8).all())
        candidates = first['evaluation'].query('k>=3').sort_values(['silueta','k'], ascending=[False,True])
        self.assertEqual(first['k'], int(candidates.iloc[0].k))
        self.assertEqual(first['assigned'].segmento.nunique(), first['k'])
        self.assertEqual(len(first['pca_variance']), 2)
        self.assertTrue(np.isfinite(first['assigned'][['pca_1','pca_2']]).all().all())
        changed = self.students.copy()
        changed['expresiones_positivas_ratio'] = 0.
        second = fit_segments(changed)
        self.assertFalse(np.allclose(first['evaluation'].inercia, second['evaluation'].inercia))

    def test_elbow_is_a_separate_heuristic(self):
        evaluation = pd.DataFrame({'k':[2,3,4,5], 'inercia':[100,40,30,25]})
        self.assertEqual(elbow_hint(evaluation), 3)
        self.assertIsNone(elbow_hint(evaluation.iloc[:2]))

    def test_fit_rejects_invalid_features_and_insufficient_profiles(self):
        for change in ({'origen_expresiones':'real'}, {'expresiones_positivas_ratio':1.1},
                       {'promedio_notas':np.nan}, dict.fromkeys(FEATURES, 0.)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                fit_segments(self.students.assign(**change))
        with self.assertRaises(ValueError):
            fit_segments(self.students, max_k=2)

    def test_outputs_are_complete_and_reproducible(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp, contextlib.redirect_stdout(io.StringIO()):
            out = Path(temp)
            first = run(output=out)
            expected = ['datos_perfiles_sinteticos.csv','segmentos_asignados.csv',
                        'resumen_segmentos.csv','evaluacion_k.csv','metricas_segmentacion.json',
                        'visualizacion_clusters.png','descripcion_segmentos.md']
            for name in expected:
                self.assertGreater((out/name).stat().st_size, 0)
            assigned = pd.read_csv(out/'segmentos_asignados.csv')
            self.assertEqual(len(assigned), 150)
            self.assertEqual(FEATURES, ['asistencia_ratio', 'tardanzas_ratio', 'promedio_notas', 'expresiones_positivas_ratio'])
            self.assertTrue(assigned.usuario_id.is_unique)
            self.assertTrue(assigned.origen_expresiones.eq('sintetico').all())
            self.assertFalse(assigned.isna().any().any())
            self.assertEqual((out/'visualizacion_clusters.png').read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(json.loads((out/'metricas_segmentacion.json').read_text(encoding='utf-8'))['k_elegido'], first['k'])
            before = (out/'segmentos_asignados.csv').read_bytes()
            run(output=out)
            self.assertEqual(before, (out/'segmentos_asignados.csv').read_bytes())
        with self.assertRaises(ValueError):
            run(output=HERE.parent/'fuera_segmentacion')
        with self.assertRaises(ValueError):
            run(dataset=HERE.parent/'otro.csv')

    def test_cli_default_dataset_and_module_entrypoint(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            for entrypoint in ([str(HERE/'segmentacion_kmeans.py')],
                               ['-m', 'segmentacion.segmentacion_kmeans']):
                executed = subprocess.run([sys.executable, '-B', *entrypoint,
                                           '--output-dir', temp], cwd=HERE.parent,
                                          capture_output=True, text=True, timeout=120)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertIn('150 perfiles', executed.stdout)
                metadata = json.loads((Path(temp)/'metricas_segmentacion.json').read_text(encoding='utf-8'))
                self.assertEqual(metadata['variables'], FEATURES)
                self.assertEqual(metadata['fuente'], DEFAULT_DATA.name)
                self.assertEqual(metadata['modalidad'], 'principal_4_variables')
            executed = subprocess.run([sys.executable, '-B', str(HERE/'segmentacion_kmeans.py'),
                                       '--muestras-expresiones', '0', '--output-dir', temp],
                                      capture_output=True, text=True, timeout=120)
            self.assertEqual(executed.returncode, 2)
            self.assertIn('entero positivo', executed.stderr)

    def test_charts_use_four_dimensional_model_results(self):
        result = fit_segments(self.students)
        scaled = StandardScaler().fit_transform(self.students[FEATURES])
        pca = PCA(n_components=2, svd_solver='full').fit(scaled)
        np.testing.assert_allclose(result['pca_variance'], pca.explained_variance_ratio_)
        np.testing.assert_allclose(result['assigned'][['pca_1', 'pca_2']], pca.transform(scaled), atol=1e-12)
        centers = ((result['summary'][FEATURES] - np.array(result['scaler_mean'])) /
                   np.array(result['scaler_scale']))
        np.testing.assert_allclose(result['centros_estandarizados'], centers, atol=1e-12)
        with tempfile.TemporaryDirectory(dir=HERE) as temp, patch(
                'segmentacion.segmentacion_kmeans.plt.close'):
            try:
                plot_results(result, Path(temp))
                fig = plt.gcf()
                scatter, heatmap, silhouette, elbow = fig.axes[:4]
                for points, (_, group) in zip(scatter.collections, result['assigned'].groupby('segmento')):
                    np.testing.assert_allclose(points.get_offsets(), group[['pca_1', 'pca_2']])
                np.testing.assert_allclose(heatmap.images[0].get_array(), centers)
                self.assertEqual(len(heatmap.get_xticklabels()), 4)
                self.assertIn('SINTÉTICAS', heatmap.get_xticklabels()[3].get_text())
                for axis, column in ((silhouette, 'silueta'), (elbow, 'inercia')):
                    np.testing.assert_array_equal(axis.lines[0].get_xdata(), result['evaluation'].k)
                    np.testing.assert_allclose(axis.lines[0].get_ydata(), result['evaluation'][column])
                self.assertEqual(list(silhouette.lines[1].get_xdata()), [result['k']] * 2)
                self.assertEqual(list(elbow.lines[1].get_xdata()), [result['k_codo']] * 2)
            finally:
                fig.clear()
        plt.close(fig)


if __name__ == '__main__':
    unittest.main(verbosity=2)
