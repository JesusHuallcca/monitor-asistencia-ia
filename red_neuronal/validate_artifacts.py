"""Comprueba artefactos confiables del repositorio; nunca accede a una base."""
import json
from .predict import Predictor
if __name__=='__main__':print(json.dumps(Predictor().model_info(),indent=2))
