from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth_user import schemas, services

router = APIRouter()

# ===== Register =====
@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = services.authenticate_user(db, user.email, user.password)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    return services.create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password
    )

# ===== Login =====
@router.post("/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    authenticated_user = services.authenticate_user(
        db, user.email, user.password
    )

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = services.create_access_token(
        data={"sub": str(authenticated_user.id)}
    )

    return {"access_token": token}
