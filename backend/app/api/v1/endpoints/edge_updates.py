"""Edge binary update / rollout endpoints (Milestone 4)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.audit import log_event
from app.services.edge_updates import EdgeRelease
from app.services.edge_deployment import (
    DeploymentError,
    get_deployment,
    list_deployments,
    plan_rollout,
)

router = APIRouter()


class RolloutRequest(BaseModel):
    version: str = Field(min_length=1, max_length=128)
    digest_sha256: str = Field(min_length=64, max_length=64)
    signature: str = Field(min_length=1, max_length=4096)
    current_version: str
    target_ring: str | None = None
    current_ring: str | None = None
    health_gate_ok: bool = False
    pending_task: bool = False
    min_protocol_version: int = 1
    max_protocol_version: int = 2
    min_driver_capability_version: int = 1
    notes: str = ""


@router.get("/deployments")
async def list_rollouts(limit: int = 20):
    return {"deployments": list_deployments(limit=limit)}


@router.get("/deployments/{deployment_id}")
async def get_rollout(deployment_id: str):
    rec = get_deployment(deployment_id)
    if not rec:
        raise HTTPException(status_code=404, detail="deployment not found")
    return {
        "deployment_id": rec.deployment_id,
        "version": rec.version,
        "from_version": rec.from_version,
        "from_ring": rec.from_ring,
        "to_ring": rec.to_ring,
        "promotion": rec.promotion,
        "health_gate_ok": rec.health_gate_ok,
        "created_at": rec.created_at,
    }


@router.post("/rollout")
async def rollout(
    payload: RolloutRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
):
    """Plan + record a bounded Edge rollout (canary/ring) — fail-closed.

    Requires a `network-admin` operator. Validates release digest/compatibility/
    rings via the safety core; records the deterministic rollout plan.
    """
    if not operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role != "network-admin":
        raise HTTPException(status_code=403, detail="network-admin role is required")

    release = EdgeRelease(
        version=payload.version,
        digest_sha256=payload.digest_sha256,
        signature=payload.signature,
        min_protocol_version=payload.min_protocol_version,
        max_protocol_version=payload.max_protocol_version,
        min_driver_capability_version=payload.min_driver_capability_version,
        notes=payload.notes,
    )
    try:
        plan = plan_rollout(
            release,
            package=None,  # digest-only validation here; binary intact check is executor-side
            current_version=payload.current_version,
            target_ring=payload.target_ring,
            current_ring=payload.current_ring,
            health_gate_ok=payload.health_gate_ok,
            pending_task=payload.pending_task,
            operator=operator_identity,
        )
    except DeploymentError as exc:
        log_event(
            device_id="edge-system",
            action="EDGE-ROLLOUT-REJECTED",
            command=f"rollout:{payload.version}",
            result="REJECTED",
            user=operator_identity,
            status="FAILED",
            error=str(exc),
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_event(
        device_id="edge-system",
        action="EDGE-ROLLOUT-PLANNED",
        command=f"rollout:{payload.version}",
        result="PLANNED",
        user=operator_identity,
        status="PLANNED",
        error=None,
    )
    return {"status": "planned", "plan": plan}
