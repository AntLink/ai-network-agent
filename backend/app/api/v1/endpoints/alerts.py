"""Alert aggregation and evaluation endpoints."""
from datetime import datetime
from fastapi import APIRouter
from typing import Any

from app.services.monitoring_alerts import AlertRule, evaluate_metrics

router = APIRouter()

_alerts: list[dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _upsert_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Insert an open alert if it is not already present (dedupe by id)."""
    for existing in _alerts:
        if existing.get("id") == alert["id"]:
            return existing
    _alerts.append(alert)
    return alert


@router.get("")
async def list_alerts():
    return {"alerts": _alerts[-50:]}


@router.get("/evaluate")
async def get_evaluate_rules():
    """Return the default monitoring alert rules (read-only)."""
    return {"rules": [r.to_dict() for r in AlertRule.DEFAULT_RULES]}


@router.post("/evaluate")
async def evaluete_alerts(payload: dict[str, Any]):
    """Evaluate multidimensional device metrics against alert rules.

    Payload: {"device_id": "...", "metrics": {"cpu": 95, "memory": 60}} with an
    optional "rules": [{metric, operator, threshold, severity, message}].
    Returns the triggered alerts and persists open ones.
    """
    metrics: dict[str, Any] = payload.get("metrics", {})
    device_id: str = payload.get("device_id", "*")
    now = datetime.utcnow()
    rules = None
    if payload.get("rules"):
        rules = [
            AlertRule(
                metric=r["metric"],
                operator=r["operator"],
                threshold=float(r["threshold"]),
                severity=r["severity"],
                message=r.get("message", f"{r['metric']} threshold breached"),
                device_id=r.get("device_id", "*"),
            )
            for r in payload["rules"]
        ]
    triggered = evaluate_metrics(metrics, rules=rules, device_id=device_id, now=now)
    for alert in triggered:
        _upsert_alert(alert)
    return {"device_id": device_id, "evaluated": len(triggered), "alerts": triggered}


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
