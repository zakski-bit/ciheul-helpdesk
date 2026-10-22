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

ALLOWED_ENVIRONMENTS = {"development", "dev", "test", "testing", "staging", "production", "prod"}
WEAK_PASSWORDS = {"admin123", "cs123", "password", "password123", "12345678", "admin", "adminadmin", "root", "secret", "ciheul123"}

class Settings:
    PROJECT_NAME: str = "CIHEUL Omnichannel Helpdesk API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    _DEFAULT_SECRET: str = "ciheul-secret-key-3489274982374982374"

    def __init__(self):
        env_input = os.getenv("ENVIRONMENT")
        if env_input is not None and not env_input.strip():
            raise RuntimeError("FATAL CONFIG ERROR: ENVIRONMENT variable is set but empty. Must be explicitly declared (e.g., 'development', 'staging', 'production').")
        
        raw_env = (env_input or "development").strip().lower()
        if raw_env not in ALLOWED_ENVIRONMENTS:
            raise RuntimeError(f"FATAL CONFIG ERROR: Unknown ENVIRONMENT '{raw_env}'. Allowed values: {', '.join(sorted(ALLOWED_ENVIRONMENTS))}.")

        self.ENVIRONMENT: str = raw_env
        self.IS_PROTECTED_ENV: bool = raw_env in ["production", "prod", "staging"]
        self.IS_PRODUCTION: bool = raw_env in ["production", "prod"]

        self.SECRET_KEY: str = os.getenv("SECRET_KEY", self._DEFAULT_SECRET)
        self.ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@ciheul.com")
        self.ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
        self.CS_EMAIL: str = os.getenv("CS_EMAIL", "cs@ciheul.com")
        self.CS_PASSWORD: str = os.getenv("CS_PASSWORD", "cs123")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")

        # Global sanity check: passwords must never be empty or whitespace
        if not self.ADMIN_PASSWORD or not self.ADMIN_PASSWORD.strip():
            raise RuntimeError("FATAL SECURITY ERROR: ADMIN_PASSWORD cannot be empty or whitespace.")
        if not self.CS_PASSWORD or not self.CS_PASSWORD.strip():
            raise RuntimeError("FATAL SECURITY ERROR: CS_PASSWORD cannot be empty or whitespace.")

        # Strict safeguards for production and staging environments
        if self.IS_PROTECTED_ENV:
            if self.SECRET_KEY == self._DEFAULT_SECRET or len(self.SECRET_KEY) < 32:
                raise RuntimeError(f"FATAL SECURITY ERROR: {raw_env.upper()} environment MUST set a strong SECRET_KEY via environment variable (minimum 32 characters).")
            
            def _validate_pwd(pwd: str, name: str):
                cleaned = (pwd or "").strip()
                if len(cleaned) < 8:
                    raise RuntimeError(f"FATAL SECURITY ERROR: {raw_env.upper()} environment MUST set {name} with minimum 8 characters.")
                if cleaned.lower() in WEAK_PASSWORDS:
                    raise RuntimeError(f"FATAL SECURITY ERROR: {raw_env.upper()} environment rejected weak or default {name} ('{cleaned}').")

            _validate_pwd(self.ADMIN_PASSWORD, "ADMIN_PASSWORD")
            _validate_pwd(self.CS_PASSWORD, "CS_PASSWORD")

        cors_env = os.getenv("BACKEND_CORS_ORIGINS")
        if cors_env:
            self.BACKEND_CORS_ORIGINS: list = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
        elif self.IS_PRODUCTION:
            self.BACKEND_CORS_ORIGINS: list = [
                "https://ciheul.com",
                "https://helpdesk.ciheul.com"
            ]
        elif raw_env == "staging":
            self.BACKEND_CORS_ORIGINS: list = [
                "https://ciheul.com",
                "https://helpdesk.ciheul.com",
                "https://staging.ciheul.com",
                "https://staging-helpdesk.ciheul.com"
            ]
        else:
            # Development / testing: explicit local origins to safely support allow_credentials=True
            self.BACKEND_CORS_ORIGINS: list = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:5500",
                "http://127.0.0.1:5500"
            ]

settings = Settings()
