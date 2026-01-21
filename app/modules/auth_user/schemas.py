from pydantic import BaseModel, EmailStr

# ===== Request =====
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ===== Response =====
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
