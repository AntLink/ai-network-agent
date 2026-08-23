from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]  # project root (…/ai-network-agent)

class Settings(BaseSettings):
    APP_NAME: str = "AI Network Agent API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    INVENTORY_FILE: str = str(ROOT / "inventory" / "devices.json")
    BACKUP_DIR: str = str(ROOT / "backups")
    AUDIT_LOG_FILE: str = str(ROOT / "logs" / "audit.log")

    SSH_CONNECT_TIMEOUT: int = 10
    SSH_COMMAND_TIMEOUT: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
