from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin_auditoria, admin_users, auth, cursos, face_auth, notas, users
from app.db.database import engine

app = FastAPI(title="Monitor Inteligente de Asistencia con IA", version="0.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # Live Server de VS Code
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_users.router)
app.include_router(admin_auditoria.router)
app.include_router(cursos.router)
app.include_router(face_auth.router)
app.include_router(notas.router)


@app.get("/api/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectada"}