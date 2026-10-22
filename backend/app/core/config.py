import os
import logging

logger = logging.getLogger("helpdesk.config")

def _load_env_file():
    """Automatically load .env into os.environ if present, avoiding manual export requirements."""
    possible_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    ]
    for env_path in possible_paths:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key not in os.environ:
                            os.environ[key] = val
                break
            except Exception as e:
                logger.warning(f"Failed to read .env file at {env_path}: {e}")

_load_env_file()

class Settings:
    PROJECT_NAME: str = "CIHEUL Omnichannel Helpdesk API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    _DEFAULT_SECRET: str = "ciheul-secret-key-3489274982374982374"

    def __init__(self):
        raw_env = os.getenv("ENVIRONMENT", "development").strip().lower()
        self.ENVIRONMENT: str = raw_env
        self.IS_PROTECTED_ENV: bool = raw_env in ["production", "prod", "staging"]
        self.IS_PRODUCTION: bool = raw_env in ["production", "prod"]

        self.SECRET_KEY: str = os.getenv("SECRET_KEY", self._DEFAULT_SECRET)
        self.ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@ciheul.com")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
        self.CS_EMAIL: str = os.getenv("CS_EMAIL", "cs@ciheul.com")
        self.CS_PASSWORD: str = os.getenv("CS_PASSWORD", "cs123")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")

        # Strict safeguards for production and staging environments
        if self.IS_PROTECTED_ENV:
            if self.SECRET_KEY == self._DEFAULT_SECRET or len(self.SECRET_KEY) < 32:
                raise RuntimeError(f"FATAL SECURITY ERROR: {raw_env.upper()} environment MUST set a strong SECRET_KEY via environment variable (minimum 32 characters).")
            if self.ADMIN_PASSWORD == "admin123" or self.CS_PASSWORD == "cs123":
                raise RuntimeError(f"FATAL SECURITY ERROR: {raw_env.upper()} environment MUST set non-default ADMIN_PASSWORD and CS_PASSWORD via environment variables.")

        cors_env = os.getenv("BACKEND_CORS_ORIGINS")
        if cors_env:
            self.BACKEND_CORS_ORIGINS: list = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
        elif self.IS_PRODUCTION:
            self.BACKEND_CORS_ORIGINS: list = ["https://ciheul.com", "https://helpdesk.ciheul.com"]
        else:
            self.BACKEND_CORS_ORIGINS: list = ["*"]

settings = Settings()
