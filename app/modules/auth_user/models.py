from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verification status
    role = Column(String(20), default="user", nullable=False)  # 'admin', 'editor', 'user'
    
    # New Profile Fields
    company = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(100), nullable=True)
    bio = Column(String(500), nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # ForeignKey ke User.id (kita loose relation aja biar gampang cross module)
    type = Column(String(50), nullable=False) # project, client, payment, message, alert
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=False)
    action_url = Column(String(255), nullable=True) # URL for redirection
    created_at = Column(String(50), default=datetime.utcnow().isoformat) # Simple string timestamp
    is_read = Column(Boolean, default=False)


class PasswordResetToken(Base):
    """Model for storing password reset tokens"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailVerificationToken(Base):
    """Model for storing email verification tokens"""
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


