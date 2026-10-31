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
tls_required = settings.DB_SSL_REQUIRED or settings.DB_HOST.endswith(".aivencloud.com")
if tls_required and not settings.DB_SSL_CA:
    raise RuntimeError("Configura DB_SSL_CA para verificar la conexión MySQL TLS.")
tls_args = {"ssl_ca": settings.DB_SSL_CA, "ssl_verify_cert": True, "ssl_verify_identity": True} if settings.DB_SSL_CA else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=tls_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
