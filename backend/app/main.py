from fastapi import FastAPI

from backend.app.api.face import router as face_router
from backend.app.api.attendance import router as attendance_router


app = FastAPI(
    title="Monitor Inteligente de Asistencia con IA",
    version="1.0.0"
)


app.include_router(face_router)
app.include_router(attendance_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Monitor de Asistencia IA API"
    }