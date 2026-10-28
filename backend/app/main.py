from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    try:
        from app.db.database import Base
        import app.db.models
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    try:
        import os
        import urllib.request
        # 1. EmoScan
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
        model_dir = os.path.join(root_dir, "integraciones", "emoscan")
        model_path = os.path.join(model_dir, "emotion-ferplus-8.onnx")
        if not os.path.exists(model_path):
            os.makedirs(model_dir, exist_ok=True)
            url = "https://github.com/onnx/models/raw/main/vision/classification/emotion_ferplus/model/emotion-ferplus-8.onnx"
            urllib.request.urlretrieve(url, model_path)

        # 2. Reconocimiento Facial (YuNet + SFace)
        face_dir = os.path.join(root_dir, "ai", "face", "models")
        os.makedirs(face_dir, exist_ok=True)
        face_models = [
            ("face_detection_yunet_2023mar.onnx", "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"),
            ("face_recognition_sface_2021dec.onnx", "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"),
        ]
        for fname, f_url in face_models:
            f_dest = os.path.join(face_dir, fname)
            if not os.path.exists(f_dest):
                urllib.request.urlretrieve(f_url, f_dest)
    except Exception:
        pass
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
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://monitor-asistencia-frontend.vercel.app",
        "https://chic-quietude-production-7952.up.railway.app",
        "https://monitor-asistencia-frontend.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "conectada"
    }
