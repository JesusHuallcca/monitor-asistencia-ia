"""Reutiliza engine/get_db del proyecto sin permitir el fallback de producción."""
import os
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.config import settings,_FALLBACK_DB_PASS
from app.db.database import engine

def check_configuration():
    if os.getenv('PARTE6_ALLOW_DEV_DB')!='1':raise HTTPException(503,'MySQL deshabilitado. Configura explícitamente la conexión local de desarrollo y PARTE6_ALLOW_DEV_DB=1.')
    if engine.url.host not in {'127.0.0.1','localhost','::1'} or engine.url.database!='monitor_asistencia_emoscan_dev':raise HTTPException(503,'Parte 6 solo permite la base local monitor_asistencia_emoscan_dev; no se conectará a producción.')
    if settings.DB_PASSWORD==_FALLBACK_DB_PASS:raise HTTPException(503,'Introduce credenciales locales explícitas; no se utilizarán valores heredados de producción.')
    if len(settings.JWT_SECRET_KEY)<32 or settings.JWT_SECRET_KEY.startswith('monitor-asistencia-default'):raise HTTPException(503,'Configura una clave JWT local segura compartida con el backend, sin publicarla.')

def read_only_db():
    check_configuration()
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql('START TRANSACTION READ ONLY')
            offset=conn.execute(text('SELECT TIMESTAMPDIFF(SECOND, UTC_TIMESTAMP(), NOW())')).scalar_one()
            if offset!=-18000:raise HTTPException(503,'La zona horaria de MySQL no coincide con las fechas locales de Lima. Se requiere revisar el origen de los timestamps; no se inferirá con fechas ambiguas.')
            db=Session(bind=conn,autoflush=False)
            try:yield db
            finally:db.close();conn.rollback()
    except SQLAlchemyError:raise HTTPException(503,'No fue posible consultar la base local. Revisa conexión, credenciales y tablas; no se muestran detalles sensibles.')
