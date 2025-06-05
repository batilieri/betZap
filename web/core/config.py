from pydantic import BaseSettings
from typing import List, Union
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "WhatsApp Atendimento"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/whatsapp_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # WhatsApp API
    WHATSAPP_API_URL: str = "https://api.whatsapp.com"
    WHATSAPP_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()