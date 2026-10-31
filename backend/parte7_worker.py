"""Worker opt-in. No migra tablas ni usa credenciales heredadas por defecto."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    required={"CHATBOT_PROACTIVE_ENABLED":"true","CHATBOT_PROACTIVE_MIGRATION_REVIEWED":"true"}
    if any(os.getenv(key,"").lower()!=value for key,value in required.items()):
        raise SystemExit("Worker desactivado: requiere habilitación y migración revisada por el operador.")
    if any(not os.getenv(key) for key in ("DB_HOST","DB_NAME","DB_USER","DB_PASSWORD")):
        raise SystemExit("Configura explícitamente la conexión autorizada. No se usan credenciales heredadas.")
    from app.db.database import SessionLocal
    from app.services.chatbot_proactive import ready
    from app.services.chatbot_proactive_scheduler import make_scheduler
    try:
        with SessionLocal() as db:ready(db)
    except Exception:raise SystemExit("Almacenamiento no disponible o migración pendiente; no se inició el worker.") from None
    # Desplegar UNA instancia dedicada supervisada, nunca por cada worker web.
    make_scheduler(SessionLocal).start()

if __name__=="__main__":main()
