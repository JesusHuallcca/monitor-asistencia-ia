from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings, _FALLBACK_DB_PASS

db_pass = settings.DB_PASSWORD if settings.DB_PASSWORD else _FALLBACK_DB_PASS

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{quote_plus(db_pass)}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"
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