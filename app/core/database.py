from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# koneksi engine ke PostgreSQL
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# Membuat session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class untuk semua Model DB
Base = declarative_base()

# Dependency Injection untuk controller/router
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()