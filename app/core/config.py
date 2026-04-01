import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure we load the .env file from the backend directory precisely
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "Resume2Interview API")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./resume2interview.db")
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost,http://10.0.2.2")
        self.secret_key = os.getenv("SECRET_KEY", "changeme-super-secret-key")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "jwt-changeme-secret-key")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        raw_nvidia = os.getenv("NVIDIA_API_KEYS", "")
        self.nvidia_api_keys: list[str] = [
            k.strip() for k in raw_nvidia.split(",") if k.strip()
        ]
        
        # Email Configuration — SMTP Mailer
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", getattr(self, "smtp_user", ""))
        self.smtp_tls = os.getenv("SMTP_TLS", "True").lower() == "true"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

settings = Settings()

def get_settings() -> Settings:
    return settings
