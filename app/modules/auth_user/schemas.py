from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

# ===== Enums =====
class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"

# ===== Request =====
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.USER  # Default to 'user'

class UserCreateAdmin(UserRegister):
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    old_password: Optional[str] = None # Untuk verifikasi jika ganti password
    
    # New fields
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

# ===== Response =====
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    is_verified: bool = False
    role: str
    
    # New fields return
    company: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    description: str
    action_url: str | None = None
    created_at: str
    is_read: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ===== Password Reset =====
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class MessageResponse(BaseModel):
    message: str


# ===== Email Verification =====
class VerifyEmailRequest(BaseModel):
    token: str

