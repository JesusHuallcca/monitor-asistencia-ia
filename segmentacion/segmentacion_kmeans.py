"""Parte 3: segmentación descriptiva por estudiante, sin etiquetas de entrenamiento."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FEATURES = ["asistencia_ratio", "tardanzas_ratio", "promedio_notas"]
STATES = {"PRESENTE", "TARDANZA", "AUSENTE"}


def load_data(dataset: Path | None, seed: int, origin: str) -> tuple[pd.DataFrame, str]:
    """Reutiliza un CSV conocido o el generador existente, nunca conecta a la BD."""
    if dataset is None:
        candidates = [ROOT / "data/dataset_asistencias.csv",
                      ROOT / "data/dataset_asistencias_sintetico.csv"]
        dataset = next((p for p in candidates if p.is_file()), None)
    if dataset is not None:
        data = pd.read_csv(dataset)
        # Un nombre de archivo nunca acredita que los datos sean reales.
        if "sintetico" in dataset.stem.lower():
            origin = "sintetico"
        if "origen_datos" not in data:
            data["origen_datos"] = origin
        return data, f"CSV: {dataset.name}"
    generator = ROOT / "ai/ml/generate_dataset.py"
    spec = importlib.util.spec_from_file_location("attendance_generator", generator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module.generate_synthetic_attendance(n_students=150, n_sessions=45, seed=seed)
    data["origen_datos"] = "sintetico"
    return data, "Generador existente ai/ml/generate_dataset.py (150 estudiantes x 45 sesiones)"


def prepare_students(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Agrega registros históricos completos; no imputa ausencias ni notas."""
    required = {"usuario_id", "estado", "promedio_notas", "origen_datos"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")
    if raw.empty or raw[list(required)].isna().any().any():
        raise ValueError("Dataset vacío o valores faltantes en columnas obligatorias.")
    df = raw.copy()
    df["estado"] = df["estado"].astype(str).str.strip().str.upper()
    if not set(df["estado"]).issubset(STATES):
        raise ValueError("estado solo admite PRESENTE, TARDANZA y AUSENTE.")
    if not set(df["origen_datos"]).issubset({"real", "sintetico", "no_verificado"}):
        raise ValueError("origen_datos debe ser real, sintetico o no_verificado.")
    if df["origen_datos"].nunique() != 1:
        raise ValueError("No se mezclan fuentes reales, sintéticas o no verificadas.")
    df["promedio_notas"] = pd.to_numeric(df["promedio_notas"], errors="raise")
    if not np.isfinite(df["promedio_notas"]).all() or not df["promedio_notas"].between(0, 20).all():
        raise ValueError("promedio_notas debe ser finito y estar entre 0 y 20.")
    # Una asistencia por estudiante y sesión; la fecha sola no identifica una clase.
    session_key = next((c for c in ("sesion_id", "sesion") if c in df), None)
    if session_key is None:
        raise ValueError("Se requiere sesion_id o sesion para detectar registros duplicados.")
    key = ["usuario_id"] + (["curso_id"] if "curso_id" in df else []) + [session_key]
    if df[key].isna().any().any():
        raise ValueError("Identificadores de sesión/curso incompletos.")
    duplicates = df.duplicated(key, keep=False)
    if duplicates.any():
        raise ValueError("Registros duplicados por estudiante y sesión; resolver antes de agrupar.")
    df["asistencia_ratio"] = df["estado"].isin(["PRESENTE", "TARDANZA"]).astype(float)
    df["tardanzas_ratio"] = df["estado"].eq("TARDANZA").astype(float)
    students = df.groupby("usuario_id", sort=True).agg(
        sesiones_observadas=("estado", "size"),
        asistencia_ratio=("asistencia_ratio", "mean"),
        tardanzas_ratio=("tardanzas_ratio", "mean"),
        promedio_notas=("promedio_notas", "mean"),
        origen_datos=("origen_datos", "first"),
    ).reset_index()
    if len(students) < 4:
        raise ValueError("Se requieren al menos 4 estudiantes para evaluar k >= 3 con silueta.")
    return students, {"filas_entrada": len(raw), "estudiantes": len(students),
                      "origen_datos": students["origen_datos"].iloc[0]}


def fit_segments(students: pd.DataFrame, seed: int = 42, max_k: int = 8) -> dict:
    if max_k < 3:
        raise ValueError("max_k debe ser al menos 3.")
    scaler = StandardScaler()
    x = scaler.fit_transform(students[FEATURES])
    unique = len(np.unique(x, axis=0))
    if unique < 3:
        raise ValueError("Se necesitan al menos 3 perfiles numéricos distintos.")
    upper = min(max_k, len(x) - 1, unique)
    models, records = {}, []
    # Limita hilos para resultados estables y evita sobrecarga en Windows.
    with threadpool_limits(limits=1):
        for k in range(2, upper + 1):
            model = KMeans(n_clusters=k, random_state=seed, n_init=30, max_iter=500)
            labels = model.fit_predict(x)
            if len(np.unique(labels)) != k:
                continue
            score = silhouette_score(x, labels, sample_size=min(len(x), 5000), random_state=seed)
            records.append({"k": k, "inercia": float(model.inertia_), "silueta": float(score)})
            models[k] = model
    evaluation = pd.DataFrame(records)
    candidates = evaluation[evaluation.k >= 3]
    if candidates.empty:
        raise ValueError("No fue posible formar al menos tres grupos distintos.")
    best_k = int(candidates.sort_values(["silueta", "k"], ascending=[False, True]).iloc[0].k)
    global_k = int(evaluation.sort_values(["silueta", "k"], ascending=[False, True]).iloc[0].k)
    model = models[best_k]
    centers = scaler.inverse_transform(model.cluster_centers_)
    # Números estables y legibles, ordenados por asistencia del centroide.
    order = np.argsort(centers[:, 0], kind="stable")
    mapping = {int(old): new + 1 for new, old in enumerate(order)}
    assigned = students.copy()
    assigned["segmento"] = [mapping[int(v)] for v in model.labels_]
    names = {i: f"S{i}: asistencia relativa " + ("baja" if i == 1 else "alta" if i == best_k else "intermedia")
             for i in range(1, best_k + 1)}
    assigned["nombre_segmento"] = assigned["segmento"].map(names)
    pca = PCA(n_components=2)
    coordinates = pca.fit_transform(x)
    assigned["pca_1"], assigned["pca_2"] = coordinates[:, 0], coordinates[:, 1]
    summary = assigned.groupby("segmento").agg(
        estudiantes=("usuario_id", "size"), asistencia_ratio=("asistencia_ratio", "mean"),
        tardanzas_ratio=("tardanzas_ratio", "mean"), promedio_notas=("promedio_notas", "mean"))
    return {"assigned": assigned, "summary": summary, "evaluation": evaluation,
            "k": best_k, "k_global": global_k, "names": names,
            "pca_variance": pca.explained_variance_ratio_.tolist()}


def plot_results(result: dict, output: Path, origin: str) -> None:
    assigned, evaluation = result["assigned"], result["evaluation"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    for segment, group in assigned.groupby("segmento"):
        color = plt.get_cmap("tab10")((int(segment) - 1) % 10)
        axes[0, 0].scatter(group.asistencia_ratio * 100, group.promedio_notas,
                           color=color, alpha=.8, s=32, label=result["names"][segment])
        axes[0, 1].scatter(group.pca_1, group.pca_2, color=color, alpha=.8, s=32)
    axes[0, 0].set(xlabel="Asistencia observada (%)", ylabel="Promedio de notas (0–20)",
                   title="Perfiles por estudiante (2 de las 3 variables)")
    axes[0, 0].legend(fontsize=8)
    variance = result["pca_variance"]
    axes[0, 1].set(xlabel=f"PC1 ({variance[0]:.1%} de varianza)",
                   ylabel=f"PC2 ({variance[1]:.1%} de varianza)",
                   title="PCA: proyección; K-Means usa las 3 variables")
    axes[1, 0].plot(evaluation.k, evaluation.silueta, "o-")
    axes[1, 0].axvline(result["k"], color="tab:red", linestyle="--", label=f"Elegido k={result['k']}")
    axes[1, 0].set(xlabel="k", ylabel="Silueta media", title="Mayor silueta es mejor; elección entre k ≥ 3")
    axes[1, 0].legend()
    axes[1, 1].plot(evaluation.k, evaluation.inercia, "o-")
    axes[1, 1].set(xlabel="k", ylabel="Inercia (datos estandarizados)", title="Curva del codo: apoyo visual")
    for ax in axes.flat:
        ax.grid(alpha=.2)
    fig.suptitle(f"Parte 3 · K-Means · Origen: {origin.upper()} · {len(assigned)} estudiantes", fontsize=15)
    fig.savefig(output / "visualizacion_clusters.png", dpi=160)
    plt.close(fig)


def write_description(result: dict, metadata: dict, output: Path) -> None:
    ev = result["evaluation"]
    selected = float(ev.loc[ev.k == result["k"], "silueta"].iloc[0])
    lines = ["# Parte 3: descripción de segmentos", "",
             f"**Origen: {metadata['origen_datos'].upper()}.** {metadata['fuente']}.", "",
             f"Se analizaron {metadata['filas_entrada']} registros y {metadata['estudiantes']} estudiantes. "
             "Cada estudiante participa una sola vez en K-Means.", "",
             "## Método y elección de k", "",
             "Se agregaron asistencia (PRESENTE o TARDANZA / sesiones observadas), "
             "tardanzas (TARDANZA / sesiones observadas) y promedio de notas (0–20). "
             "StandardScaler lleva cada variable a media 0 y desviación estándar 1. "
             "No se utilizan usuario_id, curso_id, perfil ni asistira para entrenar. "
             "Las notas repetidas por sesión se promedian: el CSV debe contener un promedio "
             "académico comparable, no notas individuales por evaluación.", "",
             f"Se evaluó k de {int(ev.k.min())} a {int(ev.k.max())}. "
             f"Mejor k global por silueta: **{result['k_global']}**. "
             f"Mejor k entre los admisibles (k ≥ 3): **{result['k']}**, silueta **{selected:.4f}**. "
             "El mínimo de tres grupos es una restricción de la entrega; no prueba que existan "
             "tres clases naturales. La inercia se reporta como apoyo visual y no determina automáticamente el codo.", "",
             "| k | Silueta | Inercia |", "|---|---:|---:|"]
    lines.extend(f"| {int(r.k)} | {r.silueta:.4f} | {r.inercia:.2f} |" for r in ev.itertuples())
    lines += ["", "## Segmentos encontrados", "",
              "Los nombres son relativos a esta muestra y se asignan después del agrupamiento; "
              "no son umbrales institucionales ni diagnósticos.", "",
              "| Segmento | Estudiantes | Asistencia media | Tardanzas / sesiones | Nota media |",
              "|---|---:|---:|---:|---:|"]
    for segment, row in result["summary"].iterrows():
        lines.append(f"| {result['names'][segment]} | {int(row.estudiantes)} "
                     f"| {row.asistencia_ratio:.1%} | {row.tardanzas_ratio:.1%} | {row.promedio_notas:.2f} |")
    lines += ["", "### Interpretación y acciones propuestas", ""]
    for segment, row in result["summary"].iterrows():
        action = ("Revisar barreras de asistencia y ofrecer acompañamiento individual."
                  if segment == 1 else "Mantener seguimiento y reconocer la continuidad."
                  if segment == result["k"] else "Realizar seguimiento preventivo y conversar sobre puntualidad y hábitos.")
        if segment == result["summary"].tardanzas_ratio.idxmax():
            action += " Este grupo tiene la mayor proporción de tardanzas por sesión; revisar también la puntualidad."
        lines.append(f"- **{result['names'][segment]}**: asistencia media {row.asistencia_ratio:.1%}, "
                     f"tardanzas {row.tardanzas_ratio:.1%} y notas {row.promedio_notas:.2f}. {action}")
    lines += ["", "## Guion para la exposición (2 minutos)", "",
              '1. «Mi objetivo es descubrir grupos de estudiantes con comportamientos similares, sin una etiqueta objetivo.»',
              f'2. «La fuente es {metadata["origen_datos"]}; usamos {metadata["estudiantes"]} estudiantes. '
              'Agrupamos las sesiones para evitar que un estudiante con más registros pese más.»',
              '3. «Usamos asistencia, tardanzas y notas. Estandarizamos porque las notas van de 0 a 20 y las proporciones de 0 a 1.»',
              f'4. «Comparamos varios k con silueta. Elegimos {result["k"]} entre los valores de al menos tres; '
              f'la silueta fue {selected:.4f}. El mejor k sin esa restricción fue {result["k_global"]}.»',
              '5. «En la tabla explico tamaño y promedios de cada segmento y propongo acompañamiento según el patrón observado.»',
              '6. «El gráfico PCA solo resume el espacio en dos dimensiones; el agrupamiento usa las tres variables originales estandarizadas.»',
              "", "## Alcances y límites", "",
              "- La silueta mide separación interna (−1 a 1); no es exactitud, probabilidad ni porcentaje de aciertos.",
              "- Revisar valores de silueta cercanos entre distintos k: una diferencia pequeña "
              "no demuestra una superioridad robusta. Hay solapamiento entre perfiles.",
              "- Si el origen es sintético, estos resultados demuestran el procedimiento y no describen alumnos reales. "
              "El generador ya introduce patrones y correlaciones entre asistencia y notas.",
              "- No se predice la próxima asistencia ni se reutiliza la regresión logística de ai/ml/train.py.",
              "- Las tasas usan solo sesiones registradas. No inferimos ausencias de registros inexistentes; "
              "un CSV real debe incluir explícitamente todas las sesiones esperadas y sus ausencias.",
              "- Se combinan cursos y periodos del CSV. Para comparar estudiantes reales, filtrar un periodo "
              "y poblaciones con oportunidades de asistencia comparables antes de ejecutar.",
              "- No se imputan notas ni se mezclan datos reales con sintéticos: entradas incompletas se rechazan.",
              "- K-Means favorece grupos compactos y es sensible a escalas, atípicos y semilla. "
              "La estabilidad con otras muestras debe validarse antes de uso institucional.",
              f"- Semilla {metadata['semilla']}; n_init=30; max_iter=500. Versiones en metricas_segmentacion.json.", ""]
    (output / "descripcion_segmentos.md").write_text("\n".join(lines), encoding="utf-8")


def run(dataset: Path | None = None, output: Path = HERE, seed: int = 42,
        max_k: int = 8, origin: str = "no_verificado") -> dict:
    raw, source = load_data(dataset, seed, origin)
    students, metadata = prepare_students(raw)
    result = fit_segments(students, seed, max_k)
    import sklearn
    metadata.update({"fuente": source, "semilla": seed, "variables": FEATURES,
                     "k_elegido": result["k"], "k_mejor_global": result["k_global"],
                     "evaluacion": result["evaluation"].to_dict(orient="records"),
                     "varianza_pca": result["pca_variance"],
                     "versiones": {"numpy": np.__version__, "pandas": pd.__version__,
                                   "scikit-learn": sklearn.__version__, "matplotlib": matplotlib.__version__}})
    output = Path(output).resolve()
    # Mantiene todos los resultados dentro de esta entrega independiente.
    if not output.is_relative_to(HERE):
        raise ValueError("La salida debe estar dentro de la carpeta segmentacion.")
    output.mkdir(parents=True, exist_ok=True)
    if metadata["origen_datos"] == "sintetico":
        raw.to_csv(output / "datos_asistencia_sinteticos.csv", index=False, encoding="utf-8-sig")
    result["assigned"].to_csv(output / "segmentos_asignados.csv", index=False, encoding="utf-8-sig")
    result["evaluation"].to_csv(output / "evaluacion_k.csv", index=False)
    (output / "metricas_segmentacion.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    plot_results(result, output, metadata["origen_datos"])
    write_description(result, metadata, output)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(result["summary"].to_string())
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, help="CSV de sesiones; si se indica, no hay fallback sintético.")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--origen", choices=["real", "sintetico", "no_verificado"], default="no_verificado",
                        help="Procedencia declarada para CSV sin origen_datos; nunca se presume real.")
    args = parser.parse_args()
    try:
        run(args.dataset, args.output_dir, args.seed, args.max_k, args.origen)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f"Error de datos/configuración: {exc}\n")


if __name__ == "__main__":
    main()
