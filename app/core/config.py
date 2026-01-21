from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Digadoin"
    API_V1_STR: str = "/api/v1"
    
    # Database Config
    DB_USER: str
    DB_PASSWORD: str
    DB_SERVER: str 
    DB_PORT: str 
    DB_NAME: str 

    # [cite_start]Security & Auth [cite: 35]
    SECRET_KEY: str  # Generate openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 3rd Party Integrations (Dev 2 & 3)
    # Midtrans Payment Gateway (Dev 2)
    MIDTRANS_SERVER_KEY: str = ""
    MIDTRANS_CLIENT_KEY: str = ""
    MIDTRANS_PAYMENT_URL: str = "https://app.sandbox.midtrans.com/snap/v1/transactions"
    MIDTRANS_PRODUCTION: bool = False
    # CLOUDFLARE_API_TOKEN: str = ""  # Dev 3

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()