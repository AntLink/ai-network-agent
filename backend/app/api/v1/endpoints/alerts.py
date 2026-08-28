"""Alert aggregation endpoints."""
from datetime import datetime
from fastapi import APIRouter
from typing import Any

router = APIRouter()

_alerts: list[dict[str, Any]] = []


@router.get("")
async def list_alerts():
    return {"alerts": _alerts[-50:]}


@router.post("")
async def create_alert(payload: dict[str, Any]):
    alert_id = f"alert-{len(_alerts) % 10000:04d}"
    alert = {
        "id": alert_id,
        "type": payload.get("type", "system"),
        "severity": payload.get("severity", "info"),
        "device_id": payload.get("device_id", ""),
        "message": payload.get("message", ""),
        "created_at": datetime.utcnow().isoformat(),
        "status": "open",
    }
    _alerts.append(alert)
    return alert


@router.patch("/{alert_id}")
async def update_alert(alert_id: str, payload: dict[str, Any]):
    for alert in _alerts:
        if alert.get("id") == alert_id:
            alert.update({k: v for k, v in payload.items() if k != "id"})
            return alert
    return {"error": "not found"}


@router.delete("/{alert_id}")
async def dismiss_alert(alert_id: str):
    global _alerts
    _alerts = [a for a in _alerts if a.get("id") != alert_id]
    return {"status": "dismissed"}
