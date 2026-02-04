from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# koneksi engine ke PostgreSQL
# Optimization: Added connection pooling settings
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_size=20,           # Keep 20 connections open
    max_overflow=10,        # Allow 10 extra temporary connections
    pool_pre_ping=True      # Check connection validity before using
)

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