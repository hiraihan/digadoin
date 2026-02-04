from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Digadoin"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_SERVER: str | None = None
    DB_PORT: str | None = None
    DB_NAME: str | None = None

    # [cite_start]Security & Auth [cite: 35]
    SECRET_KEY: str  # Generate openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30



    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()