import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.config import ConfigPlanRequest, ConfigApplyRequest, ConfigRollbackRequest
from app.services.device_service import device_service

router = APIRouter()

# in-memory plan store (replace with persistent store in production)
_plan_store: dict[str, dict] = {}


@router.post("/plan")
async def create_plan(payload: ConfigPlanRequest):
    plan_id = str(uuid.uuid4())[:8]
    _plan_store[plan_id] = {
        "device_id": payload.device_id,
        "commands": payload.commands,
        "verify": [v.model_dump() for v in payload.verify],
        "save_on_success": payload.save_on_success,
        "description": payload.description or "",
        "status": "planned",
    }
    return {"plan_id": plan_id, **_plan_store[plan_id]}


@router.post("/apply")
async def apply_plan(payload: ConfigApplyRequest):
    plan = _plan_store.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan["status"] != "planned":
        raise HTTPException(status_code=400, detail=f"Plan already {plan['status']}")

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