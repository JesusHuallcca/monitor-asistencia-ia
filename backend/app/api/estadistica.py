import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import Usuario

router = APIRouter(prefix="/api/estadistica", tags=["Estadística Básica"])

# Rutas canónicas absolutas
BASE_BACKEND_DIR = Path(__file__).resolve().parents[2]  # .../backend
STATS_DIR = BASE_BACKEND_DIR / "estadistica"
JSON_PATH = STATS_DIR / "reporte_kpis.json"
IMG_PATH = STATS_DIR / "graficos_estadisticos.png"
SCRIPT_PATH = STATS_DIR / "stats_empresa.py"

profesor_o_admin = require_roles("profesor", "admin", "superadmin")


@router.get("/kpis")
def obtener_kpis(user: Usuario = Depends(get_current_user)):
    """Devuelve los KPIs y probabilidades normalizadas de la Parte 1."""
    if not JSON_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aún no se ha generado el reporte estadístico. Utiliza POST /api/estadistica/actualizar para crearlo."
        )

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer el archivo de estadísticas: {str(e)}"
        )

    fuentes = raw.get("fuentes", {})
    asist_raw = fuentes.get("asistencia", {})
    emoc_raw = fuentes.get("emociones", {})
    stats_bin = asist_raw.get("estadisticas_asistencia_binaria", {})
    stats_emoc = emoc_raw.get("estadisticas_puntajes_solo_suma_positiva", {})
    prob_estado = asist_raw.get("probabilidad_empirica_estado", {})

    mtime = datetime.fromtimestamp(os.path.getmtime(JSON_PATH)).isoformat()

    return {
        "asistencia": {
            "probabilidad_asistencia": asist_raw.get("probabilidad_empirica_asistencia", 0.0),
            "probabilidad_inasistencia": asist_raw.get("probabilidad_empirica_inasistencia", 0.0),
            "probabilidad_presente": prob_estado.get("PRESENTE", 0.0),
            "probabilidad_tardanza": prob_estado.get("TARDANZA", 0.0),
            "probabilidad_ausente": prob_estado.get("AUSENTE", 0.0),
            "media": stats_bin.get("media", 0.0),
            "desviacion_estandar": stats_bin.get("desviacion_estandar_muestral", 0.0),
            "total_registros": asist_raw.get("registros_analizados", 0),
            "total_estudiantes": asist_raw.get("estudiantes", 0)
        },
        "emociones": {
            k: {
                "media": v.get("media", 0.0),
                "desviacion": v.get("desviacion_estandar_muestral", 0.0),
                "n": v.get("n", 0)
            }
            for k, v in stats_emoc.items()
        },
        "calidad_datos": {
            "archivos_analizados": emoc_raw.get("archivos_validos", 0),
            "registros_asistencia": asist_raw.get("registros_analizados", 0),
            "registros_emociones": emoc_raw.get("registros_analizados", 0),
            "duplicados_eliminados": emoc_raw.get("duplicados_exactos_eliminados", 0)
        },
        "ultima_actualizacion": mtime,
        "grafico_disponible": IMG_PATH.exists()
    }


@router.get("/grafico")
def obtener_grafico(user: Usuario = Depends(get_current_user)):
    """Sirve la imagen con los 4 gráficos estadísticos generados."""
    if not IMG_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El gráfico estadístico no está disponible todavía."
        )
    return FileResponse(IMG_PATH, media_type="image/png")


def _ejecutar_script_sync():
    """Ejecuta el script stats_empresa.py en un subproceso con timeout."""
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"No se encontró el script en {SCRIPT_PATH}")

    mtime_inicial = os.path.getmtime(JSON_PATH) if JSON_PATH.exists() else 0

    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(STATS_DIR),
        capture_output=True,
        text=True,
        timeout=25
    )

    if proc.returncode != 0:
        raise RuntimeError(f"El script falló (código {proc.returncode}): {proc.stderr or proc.stdout}")

    if not JSON_PATH.exists():
        raise RuntimeError("El archivo reporte_kpis.json no se generó tras la ejecución.")

    mtime_final = os.path.getmtime(JSON_PATH)
    if mtime_final <= mtime_inicial and mtime_inicial != 0:
        # Aún si el timestamp coincide en el mismo segundo, verificar lectura válida
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            json.load(f)

    return datetime.fromtimestamp(mtime_final).isoformat()


@router.post("/actualizar")
async def actualizar_estadisticas(user: Usuario = Depends(profesor_o_admin)):
    """Ejecuta el script de estadística de forma asíncrona sin bloquear el servidor."""
    try:
        nueva_mtime = await asyncio.to_thread(_ejecutar_script_sync)
        return {
            "status": "ok",
            "mensaje": "Estadísticas recalculadas y actualizadas exitosamente",
            "ultima_actualizacion": nueva_mtime
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="La generación de estadísticas excedió el tiempo límite permitido (25s)."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron actualizar las estadísticas: {str(e)}"
        )

