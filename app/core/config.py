from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Digadoin"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_SERVER: str | None = None
    DB_PORT: str | None = None
    DB_NAME: str | None = None

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP Email Configuration
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_FROM: Optional[str] = None
    MAIL_PORT: int = 587
    MAIL_SERVER: Optional[str] = None
    MAIL_FROM_NAME: str = "Digadoin"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    
    # Resend Configuration (Alternative to SMTP - works on Railway)
    RESEND_API_KEY: Optional[str] = None
    EMAIL_PROVIDER: str = "smtp"  # Options: "smtp" or "resend"
    
    # Frontend URL for password reset links
    FRONTEND_URL: str = "https://digadoin.vercel.app"
    
    # Password Reset Token Expiration (in minutes)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
