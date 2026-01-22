from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from app.modules.auth_user import models
from app.core.config import settings
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== Password =====
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# ===== JWT =====
def create_access_token(data: dict, expires_delta: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

# ===== User Service =====
def create_user(db: Session, name: str, email: str, password: str):
    hashed_password = hash_password(password)
    db_user = models.User(
        name=name,
        email=email,
        password=hashed_password,
        is_active=True
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback() # Wajib rollback jika error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists" # Pesan ini yang dicari oleh Test
        )
        
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
