"""
Entrenamiento del modelo de predicción de asistencia (Regresión Logística).
Persona 3 — Machine Learning
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from features import FEATURE_COLUMNS, TARGET_COLUMN, build_features


def train_model(
    dataset_path: str | Path,
    model_dir: str | Path = "models",
    test_size: float = 0.25,
    random_state: int = 42,
) -> dict:
    dataset_path = Path(dataset_path)
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(dataset_path)
    print(f"Dataset cargado: {len(df)} filas")

    X = build_features(df)
    y = df[TARGET_COLUMN].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Pipeline: estandarización + regresión logística
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
            solver="lbfgs",
        )),
    ])

    pipeline.fit(X_train, y_train)

    # Evaluación en test
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_features": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_type": "LogisticRegression",
    }

    # Guardar modelo y métricas
    model_path = model_dir / "asistencia_logreg.joblib"
    metrics_path = model_dir / "metricas_modelo.json"

    joblib.dump(pipeline, model_path)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\n=== Métricas reales (conjunto de prueba) ===")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["No asistirá", "Asistirá"]))

    # Coeficientes (interpretabilidad)
    clf = pipeline.named_steps["clf"]
    coefs = dict(zip(FEATURE_COLUMNS, clf.coef_[0].round(4).tolist()))
    print("\nCoeficientes del modelo (después de StandardScaler):")
    for k, v in sorted(coefs.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {k:30s} {v:+.4f}")

    coef_path = model_dir / "coeficientes.json"
    with open(coef_path, "w", encoding="utf-8") as f:
        json.dump({"intercept": float(clf.intercept_[0]), "coefficients": coefs}, f, indent=2)

    print(f"\nModelo guardado en: {model_path}")
    print(f"Métricas guardadas en: {metrics_path}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Entrena el modelo de predicción de asistencia")
    parser.add_argument("--dataset", default="data/dataset_asistencias_sintetico.csv")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train_model(args.dataset, args.model_dir, args.test_size, args.seed)


if __name__ == "__main__":
    main()
