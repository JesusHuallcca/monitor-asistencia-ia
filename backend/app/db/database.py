from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Explicit environment only. URL prevents accidental password interpolation.
DATABASE_URL = URL.create(
    "mysql+pymysql", username=settings.DB_USER, password=settings.DB_PASSWORD,
    host=settings.DB_HOST, port=settings.DB_PORT, database=settings.DB_NAME,
    query={"charset": "utf8mb4"},
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
