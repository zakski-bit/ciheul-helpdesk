import os
import logging

logger = logging.getLogger("helpdesk.config")

class Settings:
    PROJECT_NAME: str = "CIHEUL Omnichannel Helpdesk API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    _DEFAULT_SECRET = "ciheul-secret-key-3489274982374982374"
    SECRET_KEY: str = os.getenv("SECRET_KEY", _DEFAULT_SECRET)
    if ENVIRONMENT == "production" and SECRET_KEY == _DEFAULT_SECRET:
        logger.warning("CRITICAL SECURITY WARNING: Production environment is using default SECRET_KEY! Set SECRET_KEY via environment variable.")

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite default, easily switchable to PostgreSQL via env var
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")
    
    # Seed credentials
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@ciheul.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    CS_EMAIL: str = os.getenv("CS_EMAIL", "cs@ciheul.com")
    CS_PASSWORD: str = os.getenv("CS_PASSWORD", "cs123")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

settings = Settings()
