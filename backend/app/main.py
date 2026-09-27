from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.face import router as face_router
from backend.app.api.attendance import router as attendance_router


app = FastAPI(
    title="Monitor Inteligente de Asistencia con IA",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(face_router)
app.include_router(attendance_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Monitor de Asistencia IA API"
    }