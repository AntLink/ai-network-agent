import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.schemas.config import ConfigPlanRequest, ConfigApplyRequest, ConfigRollbackRequest
from app.services.device_service import device_service

router = APIRouter()

PLAN_FILE = Path(settings.CONFIG_PLAN_FILE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_plan_store() -> dict[str, dict]:
    if not PLAN_FILE.exists():
        return {}
    try:
        data = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    plans = data.get("plans", {})
    return plans if isinstance(plans, dict) else {}


def persist_plan_store() -> None:
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PLAN_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"plans": _plan_store}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(PLAN_FILE)


_plan_store: dict[str, dict] = load_plan_store()


def classify_commands(commands: list[str]) -> str:
    text = "\n".join(commands).lower()
    critical_terms = ("factory-reset", "system reset", "reload", "delete", "wipe")
    high_terms = (
        "shutdown",
        "no ip route 0.0.0.0",
        "ip route 0.0.0.0",
        "default-route",
        "ip access-group",
        "firewall",
        "user",
        "secret",
        "password",
        "ppp",
        "tunnel",
        "ipsec",
    )
    if any(term in text for term in critical_terms):
        return "CRITICAL"
    if any(term in text for term in high_terms):
        return "HIGH"
    return "MEDIUM"


@router.post("/plan")
async def create_plan(payload: ConfigPlanRequest):
    plan_id = str(uuid.uuid4())[:8]
    timestamp = now_iso()
    _plan_store[plan_id] = {
        "device_id": payload.device_id,
        "commands": payload.commands,
        "verify": [v.model_dump() for v in payload.verify],
        "save_on_success": payload.save_on_success,
        "description": payload.description or "",
        "risk_level": classify_commands(payload.commands),
        "status": "planned",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    persist_plan_store()
    return {"plan_id": plan_id, **_plan_store[plan_id]}


@router.get("/plans")
async def list_plans():
    return {
        "plans": [
            {"plan_id": plan_id, **plan}
            for plan_id, plan in sorted(
                _plan_store.items(),
                key=lambda item: item[1].get("created_at", ""),
                reverse=True,
            )
        ]
    }


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    plan = _plan_store.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"plan_id": plan_id, **plan}


@router.post("/apply")
async def apply_plan(payload: ConfigApplyRequest):
    plan = _plan_store.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan["status"] != "planned":
        raise HTTPException(status_code=400, detail=f"Plan already {plan['status']}")
    if not payload.approved_by.strip():
        raise HTTPException(status_code=403, detail="Approval identity is required")

    device_id = plan["device_id"]
    try:
        driver = device_service.get_driver(device_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Device not found")

    if not hasattr(driver, "config_transaction"):
        raise HTTPException(status_code=400, detail="Device driver does not support config transactions")

    report = await driver.config_transaction(
        commands=plan["commands"],
        verify=plan["verify"],
        save_on_success=plan["save_on_success"],
        description=plan["description"],
    )
    plan["status"] = report.get("status", "applied")
    plan["report"] = report
    plan["updated_at"] = now_iso()
    persist_plan_store()
    return {"plan_id": payload.plan_id, "approved_by": payload.approved_by, **report}


@router.post("/rollback")
async def rollback(payload: ConfigRollbackRequest):
    # Expect backup_id to be a local backup file path stored during transaction
    # For now, delegate to driver's rollback if available
    from app.drivers.factory import get_driver
    from app.repositories.inventory import inventory_repository
    device = inventory_repository.get_device(payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    driver = get_driver(device)
    if hasattr(driver, "_txn_rollback"):
        result = await driver._txn_rollback()
        return {"device_id": payload.device_id, "backup_id": payload.backup_id, **result}
    raise HTTPException(status_code=400, detail="Rollback not supported for this device")
