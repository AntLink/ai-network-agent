"""Credential profile management endpoints."""
from fastapi import APIRouter
from typing import Any

router = APIRouter()

_credentials: list[dict[str, Any]] = []


@router.get("")
async def list_credentials():
    safe = []
    for cred in _credentials:
        safe.append({
            "id": cred.get("id", ""),
            "name": cred.get("name", ""),
            "vendor": cred.get("vendor", "other"),
            "username": cred.get("username", ""),
            "auth_type": cred.get("auth_type", "password"),
            "secret_preview": "****",
            "last_test": cred.get("last_test", "-"),
            "status": cred.get("status", "untested"),
        })
    return {"credentials": safe}


@router.post("")
async def create_credential(payload: dict[str, Any]):
    cred_id = f"cred-{len(_credentials) % 1000:03d}"
    cred = {
        "id": cred_id,
        "name": payload.get("name", ""),
        "vendor": payload.get("vendor", "other"),
        "username": payload.get("username", ""),
        "password": payload.get("password", ""),
        "auth_type": payload.get("auth_type", "password"),
        "last_test": "-",
        "status": "untested",
    }
    _credentials.append(cred)
    return {"id": cred_id, "name": cred["name"], "status": "created"}


@router.delete("/{cred_id}")
async def delete_credential(cred_id: str):
    global _credentials
    _credentials = [c for c in _credentials if c.get("id") != cred_id]
    return {"status": "deleted"}
