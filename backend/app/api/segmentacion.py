"""Carga acotada y en memoria de CSV sintético, solo para profesores."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.deps import require_roles
from app.services.segmentacion_service import MAX_BYTES, SegmentationBusy, process_csv
from pathlib import Path

router = APIRouter(prefix='/api/segmentacion', tags=['Segmentación IA'])


@router.get('/demo')
async def demostracion(profesor=Depends(require_roles('profesor'))):
    source = Path(__file__).resolve().parents[3] / 'segmentacion' / 'datos_asistencia_sinteticos.csv'
    try:
        result = await run_in_threadpool(process_csv, source.read_bytes(), generar_detalle=True)
    except SegmentationBusy as error:
        raise HTTPException(503, str(error), headers={'Retry-After': '3'}) from error
    return JSONResponse(result, headers={'Cache-Control': 'no-store'})


@router.post('/procesar')
async def procesar(request: Request, profesor=Depends(require_roles('profesor'))):
    if request.headers.get('content-type', '').split(';')[0].lower() != 'text/csv':
        raise HTTPException(415, 'Envía el archivo CSV con Content-Type: text/csv.')
    filename = request.headers.get('x-csv-filename', '')
    if not filename.lower().endswith('.csv'):
        raise HTTPException(422, 'Selecciona un archivo con extensión .csv.')
    length = request.headers.get('content-length')
    if length:
        try:
            size = int(length)
        except ValueError:
            raise HTTPException(400, 'Tamaño de petición inválido.')
        if size < 0 or size > MAX_BYTES:
            raise HTTPException(413, 'El CSV no debe superar 2 MiB.')
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, 'El CSV no debe superar 2 MiB.')
        content.extend(chunk)
    try:
        result = await run_in_threadpool(process_csv, bytes(content))
    except SegmentationBusy as error:
        raise HTTPException(503, str(error), headers={'Retry-After': '3'}) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return JSONResponse(result, headers={'Cache-Control': 'no-store'})
