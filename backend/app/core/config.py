from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# SATU-SATUNYA sumber default URL controller GNS3.
# Nilai asli (172.21.0.2) diset di root .env -> GNS3_CONTROLLER_URL.
# Semua modul lain (schemas, driver, endpoints, mcp-bridge) harus mengimpor
# ini, bukan hardcode IP sendiri.
DEFAULT_GNS3_CONTROLLER_URL = "http://localhost:3080/v2"

ROOT = Path(__file__).resolve().parents[3]  # project root (…/ai-network-agent)

# Inject .env ke os.environ sehingga semua helper kredensial (os.getenv)
# dan Settings memakai nilai yang sama. pydantic-settings tidak otomatis
# mengisi os.environ, dan driver memakai os.getenv per-nama-device.
try:
    from dotenv import load_dotenv
    # override=True: pastikan nilai .env terbaru (mis. kredensial GNS3 VM)
    # selalu menimpa os.environ saat module di-load (termasuk saat uvicorn --reload).
    load_dotenv(ROOT / ".env", override=True)
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
    ALLOW_DIRECT_WRITE: bool = False

    # Comma-separated list, e.g. "http://localhost:5173,http://127.0.0.1:5173".
    # Keep the default local-only for development; production should set explicit origins.
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    NINEROUTER_URL: str = "http://127.0.0.1:20128"
    NINEROUTER_KEY: str = ""
    NINEROUTER_MODEL: str = "opencode-cheap"
    # Model khusus untuk pertanyaan berbasis web (harus punya capability search:true)
    NINEROUTER_WEB_MODEL: str = "cx/gpt-5.6-sol"
    AI_PROVIDER: str = "9router"

    # Controller GNS3 — dibaca dari env; default mengacu constant
    # DEFAULT_GNS3_CONTROLLER_URL (nilai asli di root .env -> GNS3_CONTROLLER_URL).
    GNS3_CONTROLLER_URL: str = DEFAULT_GNS3_CONTROLLER_URL

    # Optional mTLS Edge control target. Empty means Edge dispatch is fail-closed.
    EDGE_CONTROL_URL: str = ""
    EDGE_CA_FILE: str = ""
    EDGE_CERT_FILE: str = ""
    EDGE_KEY_FILE: str = ""
    EDGE_ID: str = ""
    EDGE_VERSION: str = "m1"
    EDGE_SESSION_BACKEND: str = "memory"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    EDGE_SESSION_TTL_SECONDS: int = 60
    TASK_ATTEMPT_BACKEND: str = "memory"
    POSTGRES_DSN: str = ""
    TASK_ATTEMPT_RECOVERY_INTERVAL_SECONDS: int = 30
    RETRY_APPROVAL_HMAC_SECRET: str = ""
    RETRY_APPROVAL_KEY_ID: str = "default"
    EDGE_RECONCILIATION_REQUIRE_SIGNATURE: bool = False
    EDGE_RECONCILIATION_PUBLIC_KEYS_JSON: str = "{}"
    EDGE_RECONCILIATION_REVOKED_EDGES_JSON: str = "[]"
    EDGE_LIFECYCLE_STATE_FILE: str = str(ROOT / "logs" / "edge-lifecycle-state.json")
    EDGE_CERT_REVOCATION_STATE_FILE: str = str(ROOT / "logs" / "edge-certificate-revocations.json")

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
