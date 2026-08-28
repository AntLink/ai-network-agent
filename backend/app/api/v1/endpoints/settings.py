"""Network settings endpoints."""
from fastapi import APIRouter
from typing import Any

from app.core.config import settings as app_settings

router = APIRouter()

_settings: dict[str, Any] = {
    "general": {
        "workspace_name": "AI Network Agent",
        "timezone": "UTC",
        "default_view": "dashboard",
    },
    "ai": {
        "provider": app_settings.AI_PROVIDER or "9router",
        "model": app_settings.NINEROUTER_MODEL or "opencode-cheap",
        "temperature": 0.7,
        "maximum_tokens": 4096,
        "require_approval": True,
        "automatic_backup": True,
        "post_change_validation": True,
        "automatic_rollback": False,
        "allow_destructive_commands": False,
    },
    "ssh": {
        "timeout_seconds": 30,
        "command_timeout_seconds": 60,
        "strict_host_key_checking": False,
    },
}


@router.get("")
async def get_settings():
    return _settings


@router.patch("")
async def update_settings(payload: dict[str, Any]):
    for key, value in payload.items():
        if isinstance(value, dict) and key in _settings:
            _settings[key].update(value)
        else:
            _settings[key] = value
    return _settings
