from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # App
    app_name: str = "Chat Web API"
    version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str
    database_echo: bool = False

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]

    # Redis (para cache e sessões)
    redis_url: Optional[str] = None

    # WhatsApp API
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None

    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour

    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "text/plain"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "forbid"  # Evita configurações inválidas


settings = Settings()