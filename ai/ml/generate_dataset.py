"""
Genera un dataset sintético realista de asistencias para entrenar el modelo.
Persona 3 — no depende de datos reales de la base.
Features se calculan SOLO con historial PREVIO (sin fuga de información).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_attendance(
    n_students: int = 150,
    n_sessions: int = 45,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simula estudiantes con distintos perfiles de asistencia.
    Las features de cada fila se calculan exclusivamente con el historial
    anterior a esa sesión (evita data leakage).
    """
    rng = np.random.default_rng(seed)

    profiles = ["alto", "medio", "irregular", "bajo"]
    profile_probs = [0.25, 0.35, 0.25, 0.15]
    base_rates = {"alto": 0.90, "medio": 0.72, "irregular": 0.50, "bajo": 0.28}

    rows = []
    student_id = 1

    for _ in range(n_students):
        profile = rng.choice(profiles, p=profile_probs)
        base = base_rates[profile]
        base = float(np.clip(base + rng.normal(0, 0.06), 0.08, 0.97))
        promedio_notas = float(np.clip(
            rng.normal(14.5 if profile in ("alto", "medio") else 11.0, 2.8), 4, 20
        ))

        historial_estados: list[str] = []

        for sesion in range(n_sessions):
            dia = sesion % 5
            hora = int(rng.choice([8, 10, 14, 16, 18]))
            semana = sesion // 5 + 1

            # --- Features SOLO con historial PREVIO ---
            if not historial_estados:
                ratio_30d = 0.5
                racha_asist = 0
                racha_aus = 0
                tard_ratio = 0.0
            else:
                ventana = historial_estados[-30:]
                presentes = sum(1 for e in ventana if e == "PRESENTE")
                tardanzas = sum(1 for e in ventana if e == "TARDANZA")
                total_v = len(ventana)
                ratio_30d = (presentes + tardanzas * 0.5) / total_v
                tard_ratio = tardanzas / total_v

                racha_asist = 0
                racha_aus = 0
                for e in reversed(ventana):
                    if e in ("PRESENTE", "TARDANZA"):
                        if racha_aus == 0:
                            racha_asist += 1
                        else:
                            break
                    else:
                        if racha_asist == 0:
                            racha_aus += 1
                        else:
                            break

            # Probabilidad real de asistir (proceso generativo)
            p = base
            if racha_aus >= 3:
                p *= 0.65
            if racha_asist >= 4:
                p = min(0.97, p * 1.08)
            if dia == 0:
                p *= 0.90
            if hora >= 16:
                p *= 0.93
            # ruido extra para que no sea determinista
            p = float(np.clip(p + rng.normal(0, 0.04), 0.05, 0.97))

            asiste = rng.random() < p
            if asiste:
                estado = "TARDANZA" if rng.random() < 0.12 else "PRESENTE"
            else:
                estado = "AUSENTE"

            target = 1 if estado in ("PRESENTE", "TARDANZA") else 0

            rows.append({
                "usuario_id": student_id,
                "curso_id": (student_id % 8) + 1,
                "sesion": sesion + 1,
                "fecha": f"2026-{(sesion // 20) + 3:02d}-{(sesion % 20) + 1:02d}",
                "estado": estado,
                "asistencia_ratio_30d": round(ratio_30d, 4),
                "asistencias_consecutivas": racha_asist,
                "ausencias_consecutivas": racha_aus,
                "dia_semana": dia,
                "hora_inicio_clase": hora,
                "es_inicio_ciclo": 1 if semana <= 2 else 0,
                "promedio_notas": round(promedio_notas, 2),
                "tardanzas_ratio": round(tard_ratio, 4),
                "asistira": target,
                "perfil": profile,
            })

            # Actualizar historial DESPUÉS de registrar features
            historial_estados.append(estado)

        student_id += 1

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--students", type=int, default=150)
    parser.add_argument("--sessions", type=int, default=45)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data/dataset_asistencias_sintetico.csv")
    args = parser.parse_args()

    df = generate_synthetic_attendance(args.students, args.sessions, args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Dataset generado: {out_path}  ({len(df)} filas, {df['usuario_id'].nunique()} estudiantes)")
    print(df["asistira"].value_counts(normalize=True).round(3))
    print("Correlación features vs target (debe ser < 1):")
    from features import FEATURE_COLUMNS, TARGET_COLUMN
    for c in FEATURE_COLUMNS:
        if c in df.columns:
            print(f"  {c:30s} {df[c].corr(df[TARGET_COLUMN]):+.3f}")


if __name__ == "__main__":
    main()
