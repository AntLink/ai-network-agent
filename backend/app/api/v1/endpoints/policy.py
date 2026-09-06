from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PolicyCheckRequest(BaseModel):
    device_id: str
    operation: str
    risk_level: str = "MEDIUM"
    plan_id: str | None = None
    approved_by: str | None = None


RISK_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


@router.post("/check")
async def policy_check(payload: PolicyCheckRequest):
    """Minimal executable policy gate for development/lab use.

    This makes the OpenCode policy_check tool real. It is intentionally
    conservative: anything MEDIUM or higher needs an approval identity.
    """
    risk = payload.risk_level.upper()
    score = RISK_ORDER.get(risk, RISK_ORDER["HIGH"])
    requires_approval = score >= RISK_ORDER["MEDIUM"]
    approved = bool(payload.approved_by)
    allowed = not requires_approval or approved

    return {
        "device_id": payload.device_id,
        "operation": payload.operation,
        "risk_level": risk if risk in RISK_ORDER else "HIGH",
        "plan_id": payload.plan_id,
        "requires_approval": requires_approval,
        "allowed": allowed,
        "reason": "approval required" if requires_approval and not approved else "allowed",
    }
