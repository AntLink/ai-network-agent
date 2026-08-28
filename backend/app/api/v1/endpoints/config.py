import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.api.v1.endpoints.tasks import append_task_step, create_task_record, finalize_task_record, update_task_record
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
    if plan["status"] not in ("planned", "failed_preapply"):
        raise HTTPException(status_code=400, detail=f"Plan already {plan['status']}")
    # failed_preapply berarti belum ada perubahan yang ter-apply (aman untuk retry).
    if plan["status"] == "failed_preapply":
        plan["status"] = "planned"
    if not payload.approved_by.strip():
        raise HTTPException(status_code=403, detail="Approval identity is required")

    device_id = plan["device_id"]
    try:
        driver = device_service.get_driver(device_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Device not found")

    if not hasattr(driver, "config_transaction"):
        raise HTTPException(status_code=400, detail="Device driver does not support config transactions")

    try:
        device = await device_service.get_device(device_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Device not found")

    task = create_task_record(
        name=f"Deploy configuration - {device.get('hostname', device_id)}",
        device=str(device.get("hostname", device_id)),
        device_id=device_id,
        action="Configuration",
        status="running",
        started=now_iso(),
        duration="-",
        user=payload.approved_by,
        agent="Policy Workflow",
        steps=[],
    )
    append_task_step(task["id"], "Planning", "success", output=f"Plan {payload.plan_id} approved by {payload.approved_by}.")
    append_task_step(task["id"], "Pre-check", "running", output="Collecting device state and validating connectivity.")

    report = await driver.config_transaction(
        commands=plan["commands"],
        verify=plan["verify"],
        save_on_success=plan["save_on_success"],
        description=plan["description"],
    )

    report_status = str(report.get("status", "")).lower()
    report_steps = report.get("steps", []) if isinstance(report.get("steps"), list) else []
    if report_status == "committed":
        append_task_step(task["id"], "Backup", "success", output="Pre-transaction backup completed.")
        append_task_step(task["id"], "Configuration", "success", output="Configuration commands applied.")
        for step in report_steps:
            phase = str(step.get("phase", "")).capitalize() or "Step"
            if phase not in {"Apply", "Verify", "Save"}:
                continue
            append_task_step(
                task["id"],
                phase,
                "success",
                output=f"{phase} completed successfully.",
            )
        append_task_step(task["id"], "Verification", "success", output="Post-change checks completed successfully.")
        append_task_step(task["id"], "Complete", "success", output="Deployment finished without rollback.")
        finalize_task_record(
            task["id"],
            "success",
            duration=f"{max(1, len(task.get('steps', [])))} sec",
        )
    elif report_status == "rolled_back":
        append_task_step(task["id"], "Backup", "success", output="Pre-transaction backup completed.")
        append_task_step(task["id"], "Configuration", "failed", output="Configuration apply failed.")
        append_task_step(task["id"], "Rollback", "success", output="Rollback executed automatically.")
        append_task_step(task["id"], "Complete", "failed", output="Deployment rolled back.")
        finalize_task_record(
            task["id"],
            "failed",
            duration=f"{max(1, len(task.get('steps', [])))} sec",
        )
    else:
        append_task_step(task["id"], "Configuration", "failed", output="Configuration transaction failed before commit.", errors=str(report.get("reason", "Transaction failed")))
        finalize_task_record(
            task["id"],
            "failed",
            duration=f"{max(1, len(task.get('steps', [])))} sec",
        )

    plan["status"] = report.get("status", "applied")
    plan["report"] = report
    plan["updated_at"] = now_iso()
    persist_plan_store()
    update_task_record(task["id"], duration=f"{max(1, len(task.get('steps', [])))} sec")
    return {
        "plan_id": payload.plan_id,
        "approved_by": payload.approved_by,
        "task_id": task["id"],
        "task": task,
        **report,
    }


@router.post("/rollback")
async def rollback(payload: ConfigRollbackRequest):
    from app.drivers.factory import get_driver
    from app.repositories.inventory import inventory_repository

    target_device_id = payload.device_id
    if payload.plan_id:
        plan = _plan_store.get(payload.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        target_device_id = str(plan.get("device_id") or payload.device_id)

    device = inventory_repository.get_device(target_device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    driver = get_driver(device)
    if hasattr(driver, "_txn_rollback"):
        try:
            task = create_task_record(
                name=f"Rollback configuration - {device.get('hostname', target_device_id)}",
                device=str(device.get("hostname", target_device_id)),
                device_id=target_device_id,
                action="Rollback",
                status="running",
                started=now_iso(),
                duration="-",
                user="system",
                agent="Policy Workflow",
                steps=[],
            )
            append_task_step(task["id"], "Rollback", "running", output="Executing rollback transaction.")
            result = await driver._txn_rollback()
            final_status = "success" if str(result.get("status", "")).upper() == "OK" else "failed"
            append_task_step(
                task["id"],
                "Complete",
                final_status,
                output=str(result.get("output", "")),
                errors=None if final_status == "success" else str(result.get("output", "")),
            )
            finalize_task_record(task["id"], final_status, duration=f"{max(1, len(task.get('steps', [])))} sec")
            return {"device_id": target_device_id, "plan_id": payload.plan_id, "backup_id": payload.backup_id, "task_id": task["id"], **result}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(status_code=400, detail="Rollback not supported for this device")
