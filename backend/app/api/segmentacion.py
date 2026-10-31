"""Carga acotada y endpoints oficiales de K-Means (Parte 3)."""
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_current_user, require_roles
from app.db.models import Usuario
from app.services.segmentacion_service import MAX_BYTES, SegmentationBusy, process_csv

router = APIRouter(prefix="/api/segmentacion", tags=["Segmentación IA (Parte 3)"])

# Rutas canónicas absolutas
BASE_DIR = Path(__file__).resolve().parents[3]
SEG_DIR = BASE_DIR / "segmentacion"
METRICAS_JSON = SEG_DIR / "metricas_segmentacion.json"
IMG_CLUSTERS = SEG_DIR / "visualizacion_clusters.png"
CSV_ASIGNADOS = SEG_DIR / "segmentos_asignados.csv"
CSV_EVALUACION_K = SEG_DIR / "evaluacion_k.csv"
CSV_SINTETICO = SEG_DIR / "datos_asistencia_sinteticos.csv"

GRAFICOS_PERMITIDOS = {
    "visualizacion_clusters.png"
}

profesor_o_admin = require_roles("profesor", "admin", "superadmin")


@router.get("/metricas")
def obtener_metricas_oficiales(user: Usuario = Depends(get_current_user)):
    """Retorna las métricas oficiales de la segmentación K-Means precalculada."""
    if not METRICAS_JSON.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el archivo de métricas metricas_segmentacion.json."
        )

    try:
        with open(METRICAS_JSON, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer metricas_segmentacion.json: {str(e)}"
        )

    # Extraer y estructurar datos
    k_elegido = datos.get("k_elegido", 3)
    eval_list = datos.get("evaluacion", [])
    silueta_elegida = 0.0
    inercia_elegida = 0.0
    for item in eval_list:
        if item.get("k") == k_elegido:
            silueta_elegida = round(item.get("silueta", 0.0), 4)
            inercia_elegida = round(item.get("inercia", 0.0), 2)
            break

    pca_var = datos.get("varianza_pca", [0.636, 0.247])
    pca_total_pct = round(sum(pca_var) * 100, 1)

    return {
        "k_elegido": k_elegido,
        "k_mejor_global": datos.get("k_mejor_global", 2),
        "silueta": silueta_elegida,
        "inercia": inercia_elegida,
        "estudiantes_analizados": datos.get("estudiantes", 150),
        "filas_analizadas": datos.get("filas_entrada", 6750),
        "origen_datos": datos.get("origen_datos", "sintetico"),
        "varianza_pca": {
            "pc1_pct": round(pca_var[0] * 100, 1) if len(pca_var) > 0 else 0,
            "pc2_pct": round(pca_var[1] * 100, 1) if len(pca_var) > 1 else 0,
            "total_explicada_pct": pca_total_pct
        },
        "variables": datos.get("variables", ["asistencia_ratio", "tardanzas_ratio", "promedio_notas"]),
        "evaluacion_k": [
            {
                "k": item.get("k"),
                "silueta": round(item.get("silueta", 0.0), 4),
                "inercia": round(item.get("inercia", 0.0), 2),
                "es_seleccionado": item.get("k") == k_elegido
            }
            for item in eval_list
        ],
        "grafico_disponible": IMG_CLUSTERS.exists(),
        "csv_descargable": CSV_ASIGNADOS.exists()
    }


@router.get("/clusters")
def obtener_resumen_clusters(user: Usuario = Depends(get_current_user)):
    """Retorna los 3 perfiles de estudiantes identificados con K-Means y sus acciones pedagógicas."""
    return {
        "metodo": "K-Means (k=3)",
        "total_estudiantes": 150,
        "segmentos": [
            {
                "id": "S1",
                "nombre": "Asistencia Relativa Baja (Riesgo)",
                "n_estudiantes": 45,
                "porcentaje": 30.0,
                "asistencia_media_pct": 34.7,
                "tardanzas_media_pct": 3.9,
                "nota_media": 10.88,
                "color": "#dc2626",
                "nivel_riesgo": "Alto",
                "perfil_resumen": "Alumnos con baja concurrencia y calificaciones cercanas al límite aprobatorio.",
                "recomendacion": "Acompañamiento individual, tutoría académica y seguimiento preventivo de deserción."
            },
            {
                "id": "S2",
                "nombre": "Asistencia Intermedia (Regular)",
                "n_estudiantes": 70,
                "porcentaje": 46.7,
                "asistencia_media_pct": 68.2,
                "tardanzas_media_pct": 7.0,
                "nota_media": 14.93,
                "color": "#d97706",
                "nivel_riesgo": "Medio",
                "perfil_resumen": "Grupo mayoritario con rendimiento académico favorable y asistencia intermedia.",
                "recomendacion": "Seguimiento preventivo de puntualidad y refuerzo en hábitos de estudio."
            },
            {
                "id": "S3",
                "nombre": "Asistencia Alta (Continuidad)",
                "n_estudiantes": 35,
                "porcentaje": 23.3,
                "asistencia_media_pct": 85.0,
                "tardanzas_media_pct": 13.8,
                "nota_media": 15.31,
                "color": "#16a34a",
                "nivel_riesgo": "Bajo",
                "perfil_resumen": "Excelente asistencia y promedio alto, pero con la mayor concentración de tardanzas.",
                "recomendacion": "Reconocimiento a la constancia académica y concientización sobre puntualidad al ingreso."
            }
        ]
    }


@router.get("/grafico")
@router.get("/grafico/{nombre}")
def obtener_grafico(nombre: str = "visualizacion_clusters.png", user: Usuario = Depends(get_current_user)):
    """Sirve de forma segura el gráfico de validación multicuadrante si está en la whitelist."""
    if nombre not in GRAFICOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El gráfico '{nombre}' no está en la lista de imágenes permitidas."
        )

    img_path = SEG_DIR / nombre
    if not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El archivo gráfico '{nombre}' no se encuentra en el directorio."
        )

    return FileResponse(img_path, media_type="image/png")


@router.get("/descargar-csv")
def descargar_segmentos_csv(user: Usuario = Depends(profesor_o_admin)):
    """Descarga el archivo CSV con los segmentos y coordenadas PCA asignadas."""
    if not CSV_ASIGNADOS.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el archivo de segmentos asignados."
        )

    return FileResponse(
        CSV_ASIGNADOS,
        media_type="text/csv",
        filename="segmentos_asignados_kmeans.csv"
    )


# --- Endpoints existentes preservados intactos para compatibilidad ---

@router.get("/demo")
async def demostracion(profesor=Depends(require_roles("profesor"))):
    if not CSV_SINTETICO.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró el CSV sintético de prueba.")
    try:
        result = await run_in_threadpool(process_csv, CSV_SINTETICO.read_bytes(), generar_detalle=True)
    except SegmentationBusy as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error), headers={"Retry-After": "3"}) from error
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


@router.post("/procesar")
async def procesar(request: Request, profesor=Depends(require_roles("profesor"))):
    if request.headers.get("content-type", "").split(";")[0].lower() != "text/csv":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Envía el archivo CSV con Content-Type: text/csv.")
    filename = request.headers.get("x-csv-filename", "")
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Selecciona un archivo con extensión .csv.")
    length = request.headers.get("content-length")
    if length:
        try:
            size = int(length)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tamaño de petición inválido.")
        if size < 0 or size > MAX_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El CSV no debe superar 2 MiB.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El CSV no debe superar 2 MiB.")
        content.extend(chunk)
    try:
        result = await run_in_threadpool(process_csv, bytes(content))
    except SegmentationBusy as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error), headers={"Retry-After": "3"}) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    return JSONResponse(result, headers={"Cache-Control": "no-store"})
