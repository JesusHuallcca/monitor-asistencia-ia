"""Compatibility contract; all numerical work stays in the existing model."""
from segmentacion.experimental_expresiones.segmentacion_expresiones import (
    DEFAULT_DATA, FEATURES, fit_segments, prepare_students as _prepare_students,
)

def prepare_students(raw, expression_seed=2026, samples=40):
    return _prepare_students(raw, expression_seed=expression_seed, samples=samples).assign(modalidad="principal_4_variables")
