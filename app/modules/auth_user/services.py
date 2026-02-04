from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from app.modules.auth_user import models, schemas
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
def create_user(db: Session, name: str, email: str, password: str, role: str = "user", 
                company: str = None, phone: str = None, website: str = None, bio: str = None, is_active: bool = True):
    hashed_password = hash_password(password)
    db_user = models.User(
        name=name,
        email=email,
        password=hashed_password,
        is_active=is_active,
        role=role,
        company=company,
        phone=phone,
        website=website,
        bio=bio
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

def authenticate_user(db: Session, email: str = None, password: str = None, user_instance=None):
    if user_instance:
        user = user_instance
    else:
        user = db.query(models.User).filter(models.User.email == email).first()
        
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def update_user(db: Session, user: models.User, data: schemas.UserUpdate):
    # [FIX] Merge user into current session to prevent "Instance not persistent" error
    user = db.merge(user)
    
    if data.name:
        user.name = data.name
        
    if data.company is not None:
        user.company = data.company
    if data.phone is not None:
        user.phone = data.phone
    if data.website is not None:
        user.website = data.website
    if data.bio is not None:
        user.bio = data.bio
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role.value
        
    if data.password:
        if not data.old_password:
            raise HTTPException(status_code=400, detail="Old password required")
        if not verify_password(data.old_password, user.password):
            raise HTTPException(status_code=400, detail="Invalid old password")
        user.password = hash_password(data.password)
        
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return True

# ===== Notification Service =====
def create_notification(db: Session, user_id: int, type: str, title: str, description: str, action_url: str = None):
    notification = models.Notification(
        user_id=user_id,
        type=type,
        title=title,
        description=description,
        action_url=action_url,
        created_at=datetime.utcnow().isoformat()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_notifications(db: Session, user_id: int):
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).order_by(models.Notification.id.desc()).all()

def mark_notification_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.user_id == user_id).first()
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification

def mark_all_read(db: Session, user_id: int):
    notifications = db.query(models.Notification).filter(models.Notification.user_id == user_id, models.Notification.is_read == False).all()
    for n in notifications:
        n.is_read = True
    db.commit()
    return True
