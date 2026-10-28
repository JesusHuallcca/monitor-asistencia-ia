from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ASISTENCIA_CSV = BASE / "dataset_asistencia_sintetico.csv"

LOGS_DIR = BASE / "logs"
if not LOGS_DIR.exists() or not list(LOGS_DIR.glob("*.csv")):
    for alt in [
        BASE.parents[2] / "EmoScan - copia (2)" / "logs",
        BASE.parents[1] / "integraciones" / "emoscan" / "logs",
        ROOT / "EmoScan - copia (2)" / "logs",
    ]:
        if alt.exists() and list(alt.glob("*.csv")):
            LOGS_DIR = alt
            break


SALIDA_DATASET = BASE / "dataset_ejemplo.csv"
SALIDA_JSON = BASE / "reporte_kpis.json"
SALIDA_GRAFICO = BASE / "graficos_estadisticos.png"
SALIDA_README = BASE / "README_Parte1.md"

EMOCIONES = [
    "happy", "sad", "angry", "neutral",
    "surprise", "fear", "disgust"
]
ESTADOS_VALIDOS = ["PRESENTE", "TARDANZA", "AUSENTE"]
COLUMNAS_EMOCION = ["timestamp", "dominant_emotion", *EMOCIONES]


def estadisticas(serie):
    s = pd.to_numeric(serie, errors="coerce").dropna()
    valores = s.to_numpy(dtype=float)
    return {
        "n": int(len(valores)),
        "media": round(float(np.mean(valores)), 6) if len(valores) else None,
        "mediana": round(float(np.median(valores)), 6) if len(valores) else None,
        "varianza_muestral": round(float(np.var(valores, ddof=1)), 6)
            if len(valores) > 1 else None,
        "desviacion_estandar_muestral": round(float(np.std(valores, ddof=1)), 6)
            if len(valores) > 1 else None,
        "minimo": round(float(np.min(valores)), 6) if len(valores) else None,
        "maximo": round(float(np.max(valores)), 6) if len(valores) else None,
    }


def cargar_emociones():
    archivos = sorted(LOGS_DIR.glob("*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No se encontraron CSV en {LOGS_DIR}")

    partes = []
    archivos_validos = []
    filas_leidas = 0
    archivos_omitidos = []

    for archivo in archivos:
        try:
            df = pd.read_csv(archivo)
            requeridas = set(COLUMNAS_EMOCION)

            if not requeridas.issubset(df.columns):
                archivos_omitidos.append(archivo.name)
                print(f"[AVISO] CSV omitido por columnas incompletas: {archivo.name}")
                continue

            df = df[COLUMNAS_EMOCION].copy()
            filas_leidas += len(df)
            df["archivo_origen"] = archivo.name
            partes.append(df)
            archivos_validos.append(archivo.name)

        except Exception as exc:
            archivos_omitidos.append(archivo.name)
            print(f"[AVISO] No se pudo leer {archivo.name}: {exc}")

    if not partes:
        raise ValueError("No se encontraron CSV de EmoScan válidos.")

    df = pd.concat(partes, ignore_index=True)
    filas_entrada = len(df)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["dominant_emotion"] = (
        df["dominant_emotion"].astype("string").str.strip().str.lower()
    )

    for columna in EMOCIONES:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    mascara_valida = (
        df["timestamp"].notna()
        & df["dominant_emotion"].notna()
        & df["dominant_emotion"].ne("")
        & df[EMOCIONES].notna().all(axis=1)
    )
    invalidos = int((~mascara_valida).sum())
    df = df.loc[mascara_valida].copy()

    filas_antes_duplicados = len(df)
    df = df.drop_duplicates(subset=COLUMNAS_EMOCION, keep="first").copy()
    duplicados = filas_antes_duplicados - len(df)

    # No se descartan los puntajes cero: se contabilizan y reportan aparte.
    suma_puntajes = df[EMOCIONES].sum(axis=1)
    df["puntajes_todos_cero"] = df[EMOCIONES].eq(0).all(axis=1)
    df["suma_puntajes"] = suma_puntajes
    df["puntajes_suma_positiva"] = suma_puntajes > 0

    return {
        "datos": df,
        "archivos_encontrados": len(archivos),
        "archivos_validos": archivos_validos,
        "archivos_omitidos": archivos_omitidos,
        "filas_leidas": filas_leidas,
        "filas_entrada": filas_entrada,
        "invalidos_eliminados": invalidos,
        "duplicados_eliminados": duplicados,
    }


def main():
    if not ASISTENCIA_CSV.exists():
        raise FileNotFoundError(
            f"No existe {ASISTENCIA_CSV}. Revisa el dataset de asistencia."
        )
    if not LOGS_DIR.exists():
        raise FileNotFoundError(f"No existe la carpeta de logs: {LOGS_DIR}")

    asistencia_original = pd.read_csv(ASISTENCIA_CSV)
    requeridas = {
        "usuario_id", "sesion", "estado", "asistencia_ratio_30d"
    }
    if not requeridas.issubset(asistencia_original.columns):
        raise ValueError(
            "El dataset de asistencia no tiene todas las columnas esperadas."
        )

    filas_asistencia_entrada = len(asistencia_original)
    asistencia_original["estado"] = (
        asistencia_original["estado"].astype("string").str.strip().str.upper()
    )
    mascara_estado = asistencia_original["estado"].isin(ESTADOS_VALIDOS)
    asistencia = asistencia_original.loc[mascara_estado].copy()
    estados_invalidos = int((~mascara_estado).sum())

    if asistencia.empty:
        raise ValueError("No quedan registros válidos de asistencia.")

    asistencia["asistencia_ratio_30d"] = pd.to_numeric(
        asistencia["asistencia_ratio_30d"], errors="coerce"
    )
    asistencia["asistencia_binaria"] = (
        asistencia["estado"].isin(["PRESENTE", "TARDANZA"]).astype(int)
    )

    emociones_info = cargar_emociones()
    emociones = emociones_info["datos"]

    if emociones.empty:
        raise ValueError("No quedan observaciones emocionales válidas.")

    total_asistencias = len(asistencia)
    conteo_estados = asistencia["estado"].value_counts()
    distribucion_estados = {
        estado: round(float(conteo_estados.get(estado, 0) / total_asistencias), 6)
        for estado in ESTADOS_VALIDOS
    }

    conteo_emociones = emociones["dominant_emotion"].value_counts()
    distribucion_emociones = (
        conteo_emociones / len(emociones)
    ).to_dict()

    puntajes_validos = emociones.loc[
        emociones["puntajes_suma_positiva"], EMOCIONES
    ]
    stats_puntajes = {
        emocion: estadisticas(puntajes_validos[emocion])
        for emocion in EMOCIONES
    }

    reporte = {
        "proyecto": "Fusion Monitor de Asistencia + EmoScan",
        "modulo": "Parte 1 - Datos y Estadistica Basica",
        "generado_por": "stats_empresa.py",
        "fuentes": {
            "asistencia": {
                "tipo": "sintetico",
                "archivo": ASISTENCIA_CSV.name,
                "registros_entrada": filas_asistencia_entrada,
                "registros_analizados": total_asistencias,
                "estados_invalidos_eliminados": estados_invalidos,
                "estudiantes": int(asistencia["usuario_id"].nunique()),
                "sesiones_por_estudiante_observadas": int(
                    asistencia.groupby("usuario_id")["sesion"].nunique().median()
                ),
                "estadisticas_asistencia_binaria": estadisticas(
                    asistencia["asistencia_binaria"]
                ),
                "estadisticas_ratio_historico_30d": estadisticas(
                    asistencia["asistencia_ratio_30d"]
                ),
                "probabilidad_empirica_estado": distribucion_estados,
                "conteo_estado": {
                    str(k): int(v) for k, v in conteo_estados.items()
                },
                "probabilidad_empirica_asistencia": round(
                    float(asistencia["asistencia_binaria"].mean()), 6
                ),
                "probabilidad_empirica_inasistencia": round(
                    float(1 - asistencia["asistencia_binaria"].mean()), 6
                ),
                "definicion_asistencia": (
                    "PRESENTE y TARDANZA cuentan como asistencia; "
                    "AUSENTE cuenta como inasistencia."
                ),
            },
            "emociones": {
                "tipo": "observaciones_csv_de_EmoScan",
                "archivos_encontrados": emociones_info["archivos_encontrados"],
                "archivos_validos": len(emociones_info["archivos_validos"]),
                "archivos_omitidos": emociones_info["archivos_omitidos"],
                "registros_antes_limpieza": emociones_info["filas_entrada"],
                "registros_invalidos_eliminados": emociones_info["invalidos_eliminados"],
                "duplicados_exactos_eliminados": emociones_info["duplicados_eliminados"],
                "registros_analizados": int(len(emociones)),
                "observaciones_con_puntajes_todos_cero": int(
                    emociones["puntajes_todos_cero"].sum()
                ),
                "observaciones_con_suma_positiva": int(
                    emociones["puntajes_suma_positiva"].sum()
                ),
                "estadisticas_puntajes_solo_suma_positiva": stats_puntajes,
                "probabilidad_empirica_emocion_dominante": {
                    str(k): round(float(v), 6)
                    for k, v in distribucion_emociones.items()
                },
                "conteo_emocion_dominante": {
                    str(k): int(v) for k, v in conteo_emociones.items()
                },
                "advertencia_puntajes_cero": (
                    "Los registros con todos los puntajes en cero se conservan "
                    "en el conteo de etiquetas, pero no se incluyen en las "
                    "estadisticas numericas de puntajes. Su significado debe "
                    "validarse contra la implementacion del detector."
                ),
            },
        },
        "limitaciones": [
            "La asistencia es sintetica y no representa registros reales.",
            "Las observaciones emocionales no son diagnosticos clinicos.",
            "No se vinculan emociones a estudiantes porque no existe una clave comun validada.",
            "Las probabilidades son frecuencias empiricas de estos archivos, no predicciones futuras.",
            "Las etiquetas dominantes de observaciones con puntajes todos cero requieren validacion.",
            "No se normalizan los puntajes emocionales porque su escala no esta confirmada.",
        ],
    }

    asistencia_export = asistencia.copy()
    asistencia_export["tipo_registro"] = "asistencia_sintetica"
    asistencia_export["archivo_origen"] = ASISTENCIA_CSV.name
    asistencia_export["timestamp"] = pd.NaT
    asistencia_export["dominant_emotion"] = pd.NA
    for emocion in EMOCIONES:
        asistencia_export[emocion] = np.nan

    emocion_export = emociones.copy()
    emocion_export["tipo_registro"] = "emocion"
    emocion_export["usuario_id"] = pd.NA
    emocion_export["curso_id"] = pd.NA
    emocion_export["sesion"] = pd.NA
    emocion_export["estado"] = pd.NA
    emocion_export["asistencia_ratio_30d"] = np.nan
    emocion_export["asistencia_binaria"] = np.nan

    combinado = pd.concat(
        [asistencia_export, emocion_export],
        ignore_index=True,
        sort=False
    )
    combinado.to_csv(SALIDA_DATASET, index=False, encoding="utf-8-sig")

    with SALIDA_JSON.open("w", encoding="utf-8") as archivo:
        json.dump(reporte, archivo, ensure_ascii=False, indent=4)

    fig, ejes = plt.subplots(2, 2, figsize=(14, 10))

    conteo_estados.reindex(ESTADOS_VALIDOS, fill_value=0).plot(
        kind="bar", ax=ejes[0, 0], title="Distribucion de asistencia"
    )
    ejes[0, 0].set_xlabel("Estado")
    ejes[0, 0].set_ylabel("Numero de sesiones")
    ejes[0, 0].tick_params(axis="x", rotation=0)

    conteo_emociones.sort_values(ascending=False).plot(
        kind="bar", ax=ejes[0, 1], title="Emocion dominante (etiquetas registradas)"
    )
    ejes[0, 1].set_xlabel("Emocion")
    ejes[0, 1].set_ylabel("Observaciones")
    ejes[0, 1].tick_params(axis="x", rotation=35)

    ratio = asistencia["asistencia_ratio_30d"].dropna()
    if not ratio.empty:
        ejes[1, 0].hist(ratio, bins=15)
    ejes[1, 0].set_title("Distribucion del ratio historico (30 dias)")
    ejes[1, 0].set_xlabel("Ratio de asistencia")
    ejes[1, 0].set_ylabel("Frecuencia")

    sumas = emociones.loc[
        emociones["puntajes_suma_positiva"], "suma_puntajes"
    ]
    if not sumas.empty:
        ejes[1, 1].hist(sumas, bins=15)
    ejes[1, 1].set_title("Suma de puntajes emocionales positivos")
    ejes[1, 1].set_xlabel("Suma de puntajes")
    ejes[1, 1].set_ylabel("Frecuencia")

    fig.tight_layout()
    fig.savefig(SALIDA_GRAFICO, dpi=160)
    plt.close(fig)

    readme = """# Parte 1 — Datos + Estadística Básica

## Ejecución
Desde esta carpeta, ejecutar:

```powershell
py -3.12 stats_empresa_v2.py
```

## Fuentes de datos
- `dataset_asistencia_sintetico.csv`: datos de asistencia sintéticos.
- CSV de EmoScan encontrados en `EmoScan - copia (2)/logs`.

## Métodos estadísticos
Se calculan media, mediana, varianza muestral y desviación estándar muestral.
Las probabilidades son frecuencias empíricas observadas en los datos disponibles.
Se utilizan Pandas para limpiar y resumir datos, NumPy para estadística numérica
y Matplotlib para generar gráficos.

## Definiciones
PRESENTE y TARDANZA se consideran asistencia; AUSENTE, inasistencia.
El ratio histórico de 30 días se analiza por separado.
Los registros emocionales con puntajes todos cero se contabilizan y se señalan
como observaciones que requieren interpretación técnica.

## Entregables
- `dataset_ejemplo.csv`: fuentes reunidas en un archivo, diferenciadas por `tipo_registro`.
- `reporte_kpis.json`: estadísticas, probabilidades, calidad de datos y limitaciones.
- `graficos_estadisticos.png`: cuatro gráficos descriptivos.

## Limitaciones
La asistencia es sintética, no un registro real del centro educativo.
Las observaciones emocionales no son diagnósticos clínicos. No se vinculan
emociones con estudiantes porque no existe una clave común validada.
Las frecuencias observadas no predicen resultados futuros.
Los puntajes emocionales no se normalizan porque su escala no está confirmada.
"""

    SALIDA_README.write_text(readme, encoding="utf-8")

    print("\n=== PARTE 1 V2 COMPLETADA ===")
    print(f"Asistencia: {total_asistencias} registros")
    print(f"Estudiantes: {asistencia['usuario_id'].nunique()}")
    print(f"Estados inválidos eliminados: {estados_invalidos}")
    print(f"EmoScan: {len(emociones)} registros analizados")
    print(f"Inválidos emocionales eliminados: {emociones_info['invalidos_eliminados']}")
    print(f"Duplicados emocionales eliminados: {emociones_info['duplicados_eliminados']}")
    print(
        "Puntajes emocionales todos cero: "
        f"{int(emociones['puntajes_todos_cero'].sum())}"
    )
    print(f"Tasa de asistencia sintética: {asistencia['asistencia_binaria'].mean():.2%}")
    print(f"CSV combinado: {len(combinado)} filas")
    print("\nEntregables:")
    for ruta in [SALIDA_DATASET, SALIDA_JSON, SALIDA_GRAFICO, SALIDA_README]:
        print(f" - {ruta}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

