import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text


from app.api import (
    admin_auditoria,
    admin_users,
    auth,
    chatbot,
    cursos,
    face_auth,
    notas,
    users,
)
from app.api.analytics import router as analytics_router
from app.api.predictions import router as predictions_router
from app.api.attendance import router as attendance_router
from app.api.sesiones import router as sesiones_router
from app.api.segmentacion import router as segmentacion_router
from app.api.emoscan_personal import router as personal_router
from app.services.emoscan_personal_service import personal_service
from app.db.database import engine
from app.api.expressions import router as expressions_router
from app.services.expression_service import expression_service


@asynccontextmanager
async def lifespan(app):
    # Schema and model provisioning are explicit deployment steps, never startup actions.
    try:
        yield
    finally:
        expression_service.close()
        personal_service.close()



app = FastAPI(
    title="Monitor Inteligente de Asistencia con IA",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=([value.strip() for value in settings.CORS_ALLOWED_ORIGINS.split(",") if value.strip()] if settings.CORS_ALLOWED_ORIGINS else [
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://monitor-asistencia-frontend.vercel.app",
        "https://chic-quietude-production-7952.up.railway.app",
        "https://monitor-asistencia-frontend.onrender.com",
    ]),
    allow_origin_regex=None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    import logging
    from fastapi.responses import JSONResponse
    logging.getLogger("monitor.api").error("request_failed code=internal_error")
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})



# =========================
# Asistencia facial
# =========================

app.include_router(attendance_router)
app.include_router(expressions_router)


# =========================
# Sesiones de clase
# =========================

app.include_router(sesiones_router)
app.include_router(segmentacion_router)
app.include_router(personal_router)


# =========================
# Autenticación y usuarios
# =========================

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_users.router)
app.include_router(admin_auditoria.router)


# =========================
# Cursos
# =========================

app.include_router(cursos.router)


# =========================
# Reconocimiento facial
# =========================

app.include_router(face_auth.router)


# =========================
# Notas
# =========================

app.include_router(notas.router)

# =========================
# Chatbot IA
# =========================
from app.api.analytics import router as analytics_router
from app.api.predictions import router as predictions_router
app.include_router(chatbot.router)
# =========================
# Analytics
# =========================

app.include_router(analytics_router)

# =========================
# Predicciones ML
# =========================

app.include_router(predictions_router)

# =========================
# Estadística Básica (Parte 1)
# =========================
from app.api import estadistica
app.include_router(estadistica.router)

# =========================
# Regresión Lineal (Parte 2)
# =========================
from app.api import regresion
app.include_router(regresion.router)

# =========================
# Regresion Logistica (Parte 4)
# =========================
from app.api import logistica
app.include_router(logistica.router)

# =========================
# Indicadores ML Dashboard (Parte 5)
# =========================
from app.api import indicadores_ml
app.include_router(indicadores_ml.router)

# =========================
# Red Neuronal Artificial (Parte 6)
# =========================
from app.api.parte6_system import router as parte6_system_router
from red_neuronal.api import create_router as create_parte6_synthetic_router
from app.api.deps import get_current_user

app.include_router(parte6_system_router)
app.include_router(create_parte6_synthetic_router(get_current_user))

# =========================
# Rutas generales
# =========================

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Monitor de Asistencia IA API"
    }


@app.get("/api/health")
def health():
    """Liveness only; diagnostics never expose connection configuration."""
    return {"status": "ok", "service": "monitor-asistencia-api"}



