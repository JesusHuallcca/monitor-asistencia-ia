"""Crear solo las tablas nuevas del chat; no ejecuta los SQL destructivos originales."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from app.db.database import engine
from app.db.models import ChatHistorial, Prediccion, Metrica
if __name__ == '__main__':
    for model in (Prediccion,Metrica,ChatHistorial):
        model.__table__.create(engine,checkfirst=True)
    print('Tablas de chatbot listas. No se modificaron las tablas existentes.')
