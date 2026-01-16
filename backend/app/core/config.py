from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_USER: str = "app"
    DB_PASSWORD: str = "app_password"
    DB_NAME: str = "teknik_servis"
    DB_PORT: int = 5432

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - string olarak alıp split ediyoruz
    CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """CORS origins'i string'den list'e çevir"""
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB

    # Backup
    BACKUP_DIR: str = "backups"
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Environment
    ENVIRONMENT: str = "production"  # development, staging, production
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Rate Limiting (opsiyonel)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
