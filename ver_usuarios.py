from app.db.database import SessionLocal
from app.db.models import Usuario

db = SessionLocal()

try:
    usuarios = db.query(Usuario).all()

    for u in usuarios:
        print(f"ID: {u.id}")
        print(f"Usuario: {u.username}")
        print(f"Rol: {u.rol}")
        print(f"Nombre: {u.nombres} {u.apellidos}")
        print(f"Estado: {u.estado}")
        print("-" * 40)
finally:
    db.close()
