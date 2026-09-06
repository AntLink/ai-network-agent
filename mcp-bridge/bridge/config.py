"""Bridge configuration, loaded from environment / .env file.

The bridge never stores device credentials. It only talks to the
ai-network-agent FastAPI backend, which owns all SSH secrets.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (no external dependency)."""
    path = path or Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


BACKEND_URL = _env("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
API_V1_PREFIX = ("/" + _env("API_V1_PREFIX", "/api/v1").strip("/")).replace("//", "/")
API_TOKEN = _env("API_TOKEN", "")
REQUEST_TIMEOUT = float(_env("REQUEST_TIMEOUT", "300"))

# Transport MCP: stdio (default) | sse | http
MCP_TRANSPORT = _env("MCP_TRANSPORT", "stdio")
MCP_HOST = _env("MCP_HOST", "127.0.0.1")
MCP_PORT = int(_env("MCP_PORT", "8911"))

DEFAULT_APPROVED_BY = _env("DEFAULT_APPROVED_BY", "mcp-bridge")

# GNS3 controller — overridable via .env (GNS3_CONTROLLER_URL)
GNS3_CONTROLLER_URL = _env("GNS3_CONTROLLER_URL", "http://172.21.0.2/v2")
GNS3_USERNAME = _env("GNS3_USERNAME", "admin")
GNS3_PASSWORD = _env("GNS3_PASSWORD", "")