"""Pruebas aisladas: ejecutar con unittest, sin iniciar backend ni usar una BD."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from segmentacion_kmeans import HERE, FEATURES, fit_segments, load_data, prepare_students, run


class SegmentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, _ = load_data(None, 42, "no_verificado")
        cls.students, _ = prepare_students(cls.raw)

    def test_aggregation_uses_attended_and_late_sessions(self):
        raw = pd.DataFrame([
            {"usuario_id": user, "sesion": session, "estado": state,
             "promedio_notas": 14, "origen_datos": "sintetico"}
            for user in range(4)
            for session, state in enumerate(["PRESENTE", "TARDANZA", "AUSENTE"])
        ])
        students, _ = prepare_students(raw)
        np.testing.assert_allclose(students.asistencia_ratio, 2 / 3)
        np.testing.assert_allclose(students.tardanzas_ratio, 1 / 3)
        self.assertTrue(students.sesiones_observadas.eq(3).all())

    def test_invalid_data_are_rejected(self):
        cases = []
        for column, value in [("estado", "JUSTIFICADO"), ("promedio_notas", np.inf),
                              ("promedio_notas", -1), ("usuario_id", None),
                              ("origen_datos", "desconocido")]:
            bad = self.raw.copy()
            bad.loc[0, column] = value
            cases.append(bad)
        cases += [pd.concat([self.raw, self.raw.iloc[:1]], ignore_index=True),
                  self.raw.drop(columns="promedio_notas"), self.raw.iloc[:0],
                  self.raw[self.raw.usuario_id.isin(self.raw.usuario_id.unique()[:3])]]
        for bad in cases:
            with self.subTest(shape=bad.shape):
                with self.assertRaises(ValueError):
                    prepare_students(bad)

    def test_no_mixing_sources(self):
        bad = self.raw.copy()
        bad.loc[0, "origen_datos"] = "real"
        with self.assertRaises(ValueError):
            prepare_students(bad)

    def test_reproducible_and_no_target_leakage(self):
        first = fit_segments(self.students)
        changed = self.raw.copy()
        changed["perfil"] = "etiqueta_ignorada"
        changed["asistira"] = 999
        changed["usuario_id"] += 10000
        students, _ = prepare_students(changed)
        second = fit_segments(students)
        np.testing.assert_array_equal(first["assigned"].segmento, second["assigned"].segmento)
        self.assertGreaterEqual(first["k"], 3)
        self.assertEqual(first["assigned"].segmento.nunique(), first["k"])
        self.assertTrue(first["evaluation"].silueta.between(-1, 1).all())
        self.assertTrue((np.diff(first["evaluation"].inercia) <= 1e-8).all())
        means = first["summary"].asistencia_ratio.to_numpy()
        self.assertTrue((np.diff(means) >= 0).all())

    def test_insufficient_distinct_profiles(self):
        students = self.students.copy()
        students[FEATURES] = 0
        with self.assertRaises(ValueError):
            fit_segments(students)

    def test_explicit_csv_and_missing_path(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            path = Path(temp) / "entrada.csv"
            self.raw.drop(columns="origen_datos").to_csv(path, index=False)
            data, source = load_data(path, 42, "real")
            self.assertTrue(data.origen_datos.eq("real").all())
            self.assertIn("entrada.csv", source)
            with self.assertRaises(FileNotFoundError):
                load_data(Path(temp) / "no_existe.csv", 42, "real")

    def test_generated_artifacts_and_reexecution(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            output = Path(temp)
            source = output / "entrada_sintetico.csv"
            self.raw.to_csv(source, index=False)
            result = run(source, output)
            expected = ["segmentos_asignados.csv", "visualizacion_clusters.png",
                        "descripcion_segmentos.md", "metricas_segmentacion.json", "evaluacion_k.csv",
                        "datos_asistencia_sinteticos.csv"]
            for name in expected:
                self.assertTrue((output / name).stat().st_size > 0, name)
            csv = pd.read_csv(output / "segmentos_asignados.csv")
            self.assertEqual(len(csv), len(self.students))
            self.assertTrue(csv.usuario_id.is_unique)
            self.assertTrue(csv.origen_datos.eq("sintetico").all())
            self.assertFalse(csv.isna().any().any())
            self.assertEqual((output / "visualizacion_clusters.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            metadata = json.loads((output / "metricas_segmentacion.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["k_elegido"], result["k"])
            self.assertIn("SINTETICO", (output / "descripcion_segmentos.md").read_text(encoding="utf-8"))
            before = (output / "segmentos_asignados.csv").read_bytes()
            run(source, output)
            self.assertEqual(before, (output / "segmentos_asignados.csv").read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
