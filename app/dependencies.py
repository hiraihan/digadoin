from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

# 1. Setup OAuth2 Scheme (Agar tombol 'Authorize' muncul di Swagger UI)
# URL "tokenUrl" ini mengarah ke endpoint login yang nanti dibuat oleh Dev 1
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 2. Database Dependency (Reusable)
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Type Hinting Shortcut agar tidak perlu ketik "Depends(get_db)" berulang kali
db_dependency = Annotated[Session, Depends(get_db)]
token_dependency = Annotated[str, Depends(oauth2_scheme)]

# 3. Placeholder: Get Current User (Akan dilengkapi Dev 1 nanti)
# Fungsi ini nanti akan memvalidasi Token JWT dan mengembalikan data user yang login
async def get_current_user(token: token_dependency, db: db_dependency):
    # Logika decode JWT akan ada di sini
    # user = verify_token(token, db)
    # if not user: raise HTTPException(...)
    return token # Sementara return token dulu agar tidak error