"""
Evaluación del modelo en un conjunto de prueba separado.
Persona 3 — Machine Learning
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from features import FEATURE_COLUMNS, TARGET_COLUMN, build_features


def evaluate(
    model_path: str | Path,
    dataset_path: str | Path,
    report_path: str | Path | None = None,
) -> dict:
    model_path = Path(model_path)
    dataset_path = Path(dataset_path)

    pipeline = joblib.load(model_path)
    df = pd.read_csv(dataset_path)

    X = build_features(df)
    y = df[TARGET_COLUMN].astype(int)

    y_pred = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y, y_pred)), 4),
        "precision": round(float(precision_score(y, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y, y_proba)), 4),
        "n_samples": int(len(y)),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }

    print("=== Evaluación completa del dataset ===")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("\nClassification report:")
    print(classification_report(y, y_pred, target_names=["No asistirá", "Asistirá"]))
    print("Matriz de confusión:")
    print(confusion_matrix(y, y_pred))

    if report_path:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\nReporte guardado en: {report_path}")

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/asistencia_logreg.joblib")
    parser.add_argument("--dataset", default="data/dataset_asistencias_sintetico.csv")
    parser.add_argument("--report", default="docs/informe_metricas.json")
    args = parser.parse_args()
    evaluate(args.model, args.dataset, args.report)


if __name__ == "__main__":
    main()
