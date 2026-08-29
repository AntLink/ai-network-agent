from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]  # project root (…/ai-network-agent)

# Inject .env ke os.environ sehingga semua helper kredensial (os.getenv)
# dan Settings memakai nilai yang sama. pydantic-settings tidak otomatis
# mengisi os.environ, dan driver memakai os.getenv per-nama-device.
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

class Settings(BaseSettings):
    APP_NAME: str = "AI Network Agent API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    INVENTORY_FILE: str = str(ROOT / "inventory" / "devices.json")
    BACKUP_DIR: str = str(ROOT / "backups")
    AUDIT_LOG_FILE: str = str(ROOT / "logs" / "audit.log")
    CONFIG_PLAN_FILE: str = str(ROOT / "logs" / "config-plans.json")

    # Base URL yang dipakai untuk membuat link download backup yang absolut.
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    SSH_CONNECT_TIMEOUT: int = 15
    SSH_COMMAND_TIMEOUT: int = 45
    ALLOW_DIRECT_WRITE: bool = True

    NINEROUTER_URL: str = "http://127.0.0.1:20128"
    NINEROUTER_KEY: str = ""
    NINEROUTER_MODEL: str = "opencode-cheap"
    AI_PROVIDER: str = "9router"

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
