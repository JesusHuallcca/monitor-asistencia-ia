from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin_users, auth, cursos, face_auth, users
from app.api.attendance import router as attendance_router
from app.db.database import engine


app = FastAPI(
    title="Monitor Inteligente de Asistencia con IA",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Asistencia facial
app.include_router(attendance_router)

# AutenticaciÃ³n y usuarios
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_users.router)
app.include_router(cursos.router)
app.include_router(face_auth.router)


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
