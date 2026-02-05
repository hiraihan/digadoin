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
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
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


# ===== Password Reset Service =====
import secrets
from app.core.config import settings

def get_user_by_email(db: Session, email: str):
    """Get user by email address"""
    return db.query(models.User).filter(models.User.email == email).first()


def create_password_reset_token(db: Session, user_id: int) -> str:
    """
    Generate and store a password reset token.
    Invalidates any existing unused tokens for the user.
    
    Returns:
        The generated token string
    """
    # Invalidate existing unused tokens for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user_id,
        models.PasswordResetToken.is_used == False
    ).update({"is_used": True})
    
    # Generate new secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    db_token = models.PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    return token


def verify_reset_token(db: Session, token: str):
    """
    Verify a password reset token.
    
    Returns:
        The PasswordResetToken object if valid, None otherwise
    """
    db_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.is_used == False
    ).first()
    
    if not db_token:
        return None
    
    # Check if token is expired
    if datetime.utcnow() > db_token.expires_at:
        return None
    
    return db_token


def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    """
    Reset user password using a valid token.
    
    Returns:
        True if successful, raises HTTPException otherwise
    """
    db_token = verify_reset_token(db, token)
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password = hash_password(new_password)
    
    # Mark token as used
    db_token.is_used = True
    
    db.commit()
    
    return True


# ===== Email Verification Service =====
def create_email_verification_token(db: Session, user_id: int) -> str:
    """
    Generate and store an email verification token.
    Token expires in 24 hours.
    
    Returns:
        The generated token string
    """
    # Invalidate existing unused tokens for this user
    db.query(models.EmailVerificationToken).filter(
        models.EmailVerificationToken.user_id == user_id,
        models.EmailVerificationToken.is_used == False
    ).update({"is_used": True})
    
    # Generate new secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours for email verification
    
    db_token = models.EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    return token


def verify_email_with_token(db: Session, token: str) -> bool:
    """
    Verify user email using a valid token.
    
    Returns:
        True if successful, raises HTTPException otherwise
    """
    db_token = db.query(models.EmailVerificationToken).filter(
        models.EmailVerificationToken.token == token,
        models.EmailVerificationToken.is_used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Check if token is expired
    if datetime.utcnow() > db_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one."
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark user as verified
    user.is_verified = True
    
    # Mark token as used
    db_token.is_used = True
    
    db.commit()
    
    return True


