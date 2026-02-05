from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.email import send_verification_email
from app.dependencies import get_current_user
from app.modules.auth_user import schemas, services, models

router = APIRouter()

# ===== Register =====
@router.post("/register", response_model=schemas.MessageResponse)
async def register(
    user: schemas.UserRegister, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = services.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    new_user = services.create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role.value
    )
    
    # Generate verification token
    verification_token = services.create_email_verification_token(db, new_user.id)
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        verification_token=verification_token,
        user_name=user.name
    )
    
    return {"message": "Registration successful! Please check your email to verify your account."}


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
    
    # Check if email is verified
    if not authenticated_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )

    token = services.create_access_token(
        data={
            "sub": str(authenticated_user.id),
            "role": authenticated_user.role
        }
    )

    return {"access_token": token}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Mendapatkan profil user yang sedang login menggunakan Token JWT.
    """
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
def update_me(data: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Update user profile.
    """
    try:
        return services.update_user(db, current_user, data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Debug Error: {str(e)}")


@router.get("/users", response_model=list[schemas.UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin only: Get list of all users/clients
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(models.User)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.User.name.ilike(search_filter)) |
            (models.User.email.ilike(search_filter))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=schemas.UserResponse)
def create_user_admin(
    user: schemas.UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin only: Create new user with profile details
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if user exists
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
        password=user.password,
        role=user.role.value if user.role else "user",
        company=user.company,
        phone=user.phone,
        website=user.website,
        bio=user.bio,
        is_active=user.is_active
    )

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user_admin(
    user_id: int,
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin only: Update specific user
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return services.update_user(db, user, data)

@router.delete("/users/{user_id}")
def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Admin only: Delete specific user
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    services.delete_user(db, user_id)
    return {"message": "User deleted successfully"}

# ===== Notifications =====
@router.get("/notifications", response_model=list[schemas.NotificationResponse])
def get_notifications(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.get_notifications(db, current_user.id)

@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.mark_notification_read(db, notification_id, current_user.id)

@router.put("/notifications/read-all")
def mark_all_read(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.mark_all_read(db, current_user.id)


# ===== Password Reset =====
from app.core.email import send_password_reset_email
from fastapi import BackgroundTasks

@router.post("/forgot-password", response_model=schemas.MessageResponse)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send password reset email to user.
    Always returns success to prevent email enumeration attacks.
    """
    user = services.get_user_by_email(db, request.email)
    
    if user:
        # Generate reset token
        reset_token = services.create_password_reset_token(db, user.id)
        
        # Send email in background (non-blocking)
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            reset_token=reset_token,
            user_name=user.name
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists with this email, you will receive password reset instructions."}


@router.post("/reset-password", response_model=schemas.MessageResponse)
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid reset token.
    """
    # Validate password length
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Reset password (raises HTTPException if token is invalid)
    services.reset_password_with_token(db, request.token, request.new_password)
    
    return {"message": "Password has been reset successfully. You can now login with your new password."}


# ===== Email Verification =====
@router.post("/verify-email", response_model=schemas.MessageResponse)
def verify_email(
    request: schemas.VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user email using a valid verification token.
    """
    services.verify_email_with_token(db, request.token)
    return {"message": "Email verified successfully! You can now login."}


@router.post("/resend-verification", response_model=schemas.MessageResponse)
async def resend_verification(
    request: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend verification email to user.
    """
    user = services.get_user_by_email(db, request.email)
    
    if user and not user.is_verified:
        # Generate new verification token
        verification_token = services.create_email_verification_token(db, user.id)
        
        # Send verification email in background
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            verification_token=verification_token,
            user_name=user.name
        )
    
    # Always return success to prevent email enumeration
    return {"message": "If an unverified account exists with this email, you will receive a verification link."}

