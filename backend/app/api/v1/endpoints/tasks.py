"""Task execution tracking endpoints."""

import asyncio
import hashlib
import json
import secrets
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.edge import CapabilityRequest, RetryClass
from app.schemas.edge import EdgeEnvelope
from app.services.edge_dispatch import EdgeDispatchError, edge_dispatch_client
from app.services.task_attempt_leases import task_attempt_lease_store
from app.core.config import settings
from app.services.retry_policy import evaluate_retry
from app.services.approval_verifier import ApprovalVerificationError, HMACApprovalVerifier
from app.services.replay_gate import build_replay_plan
from app.core.audit import log_event
from app.repositories.inventory import inventory_repository
from app.services.execution_routing import execution_routing_resolver
from app.services.task_execution_gate import TaskExecutionGateError, validate_dispatchable_attempt
from app.services.edge_identity import EdgeLifecycleState, edge_identity_registry
from app.api.v1.endpoints.edge_control import edge_session_registry

router = APIRouter()

_tasks: list[dict[str, Any]] = []
_task_subscribers: list[asyncio.Queue] = []
_task_steps: dict[str, list[dict[str, Any]]] = {}


class RetryDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transport_lost: bool = False
    verification: str | None = Field(default=None, max_length=40)
    execution_fingerprint: str | None = Field(default=None, min_length=64, max_length=64)
    operator_approved: bool = False
    operator: str = Field(min_length=1, max_length=100)
    operator_approval_ref: str | None = Field(default=None, min_length=1, max_length=200)
    operator_approval_token: str | None = Field(default=None, min_length=20, max_length=2000)

    @model_validator(mode="after")
    def require_approval_reference(self):
        if self.operator_approved and (not self.operator_approval_ref or not self.operator_approval_token):
            raise ValueError("operator approval reference and token are required when operator_approved is true")
        return self


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_tasks() -> None:
    if _tasks:
        return

    register_task(
        task_id="task-ospf-r1-r2",
        name="Configure OSPF",
        device="R1, R2",
        device_id="cisco-iosv-r1,cisco-iosv-r2",
        action="Configuration",
        status="success",
        started="2026-08-26T14:20:00+08:00",
        duration="18 sec",
        user="admin",
        agent="AI Agent",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T14:20:01+08:00", "output": "Intent parsed and device set resolved to R1, R2."},
            {"name": "Pre-check", "status": "success", "timestamp": "2026-08-26T14:20:04+08:00", "output": "SSH reachable, privilege 15 confirmed, interfaces are up."},
            {"name": "Backup", "status": "success", "timestamp": "2026-08-26T14:20:08+08:00", "output": "Running configuration backed up for both devices."},
            {"name": "Configuration", "status": "success", "timestamp": "2026-08-26T14:20:12+08:00", "output": "OSPF process and network statements applied."},
            {"name": "Validation", "status": "success", "timestamp": "2026-08-26T14:20:17+08:00", "output": "Neighbor state FULL, expected routes installed."},
            {"name": "Save", "status": "success", "timestamp": "2026-08-26T14:20:18+08:00", "output": "Configuration saved."},
        ],
    )
    register_task(
        task_id="task-backup-all",
        name="Backup all configs",
        device="All devices",
        device_id="all",
        action="Backup",
        status="running",
        started="2026-08-26T14:31:00+08:00",
        duration="42 sec",
        user="admin",
        agent="Scheduler",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T14:31:01+08:00", "output": "Inventory scan completed."},
            {"name": "Backup", "status": "running", "timestamp": "2026-08-26T14:31:10+08:00", "output": "Backing up device configurations in progress."},
        ],
    )
    register_task(
        task_id="task-check-mt",
        name="Check MikroTik internet reachability",
        device="MT-R1",
        device_id="mikrotik-chr-mt-r1",
        action="Validation",
        status="failed",
        started="2026-08-26T13:52:00+08:00",
        duration="11 sec",
        user="admin",
        agent="AI Agent",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T13:52:01+08:00", "output": "Intent matched to MT-R1."},
            {"name": "Reachability", "status": "failed", "timestamp": "2026-08-26T13:52:07+08:00", "output": "Unable to reach upstream internet gateway.", "errors": "Gateway ping timeout."},
        ],
    )


def register_task(
    *,
    task_id: str | None = None,
    name: str,
    device: str,
    device_id: str,
    action: str,
    status: str,
    started: str,
    duration: str,
    user: str,
    agent: str,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    record = {
        "id": task_id or _make_task_id(),
        "name": name,
        "device": device,
        "device_id": device_id,
        "action": action,
        "status": status,
        "started": started,
        "duration": duration,
        "user": user,
        "agent": agent,
    }
    _tasks.insert(0, record)
    _task_steps[record["id"]] = [normalize_step(record["id"], step, index) for index, step in enumerate(steps or [])]
    return record


def create_task_record(**kwargs: Any) -> dict[str, Any]:
    return register_task(**kwargs)


def _make_task_id() -> str:
    return f"task-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


def normalize_step(task_id: str, step: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": str(step.get("id") or f"{task_id}-step-{index}"),
        "taskId": task_id,
        "name": str(step.get("name") or f"Step {index + 1}"),
        "status": str(step.get("status") or "queued"),
        "timestamp": str(step.get("timestamp") or now_iso()),
        "output": str(step.get("output") or ""),
        **({"errors": str(step["errors"])} if step.get("errors") else {}),
    }


def list_task_records() -> list[dict[str, Any]]:
    _seed_tasks()
    return deepcopy(_tasks)


def get_task_record(task_id: str) -> dict[str, Any] | None:
    _seed_tasks()
    for task in _tasks:
        if task.get("id") == task_id:
            return deepcopy(task)
    return None


def get_task_steps(task_id: str) -> list[dict[str, Any]]:
    _seed_tasks()
    return deepcopy(_task_steps.get(task_id, []))


def append_task_step(
    task_id: str,
    name: str,
    status: str,
    *,
    output: str = "",
    errors: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    step = {
        "id": f"{task_id}-step-{len(_task_steps.get(task_id, [])) + 1}",
        "taskId": task_id,
        "name": name,
        "status": status,
        "timestamp": timestamp or now_iso(),
        "output": output,
    }
    if errors:
        step["errors"] = errors

    _task_steps.setdefault(task_id, []).append(step)
    task = _find_task(task_id)
    if task is not None:
        task["steps"] = deepcopy(_task_steps[task_id])

    asyncio.create_task(_broadcast_task_event({"type": "task_progress", "taskId": task_id, "step": deepcopy(step)}))
    return deepcopy(step)


def update_task_record(task_id: str, **updates: Any) -> dict[str, Any] | None:
    task = _find_task(task_id)
    if task is None:
        return None
    task.update({k: v for k, v in updates.items() if k != "id"})
    if "steps" in task:
        _task_steps[task_id] = [normalize_step(task_id, step, index) for index, step in enumerate(task["steps"])]
    asyncio.create_task(_broadcast_task_event({"type": "task_updated", "task": deepcopy(task)}))
    return deepcopy(task)


def finalize_task_record(task_id: str, status: str, *, duration: str | None = None, output: str | None = None) -> dict[str, Any] | None:
    task = _find_task(task_id)
    if task is None:
        return None
    task["status"] = status
    if duration is not None:
        task["duration"] = duration
    if output is not None:
        task["output"] = output
    task["steps"] = deepcopy(_task_steps.get(task_id, []))
    asyncio.create_task(_broadcast_task_event({"type": "task_completed", "task": deepcopy(task)}))
    return deepcopy(task)


def _find_task(task_id: str) -> dict[str, Any] | None:
    _seed_tasks()
    for task in _tasks:
        if task.get("id") == task_id:
            return task
    return None


@router.get("")
async def list_tasks():
    return {"tasks": list_task_records()}


@router.get("/stream")
async def stream_task_updates():
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        _task_subscribers.append(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': now_iso()})}\n\n"
        finally:
            if queue in _task_subscribers:
                _task_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = get_task_record(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"task": task, "steps": get_task_steps(task_id)}


@router.post("")
async def create_task(payload: dict[str, Any]):
    task = register_task(
        name=str(payload.get("name", "Unnamed task")),
        device=str(payload.get("device", payload.get("device_id", "-"))),
        device_id=str(payload.get("device_id", payload.get("device", ""))),
        action=str(payload.get("action", "")),
        status=str(payload.get("status", "queued")),
        started=str(payload.get("started", now_iso())),
        duration=str(payload.get("duration", "-")),
        user=str(payload.get("user", "system")),
        agent=str(payload.get("agent", "manual")),
        steps=list(payload.get("steps", [])) if isinstance(payload.get("steps"), list) else [],
    )
    await _broadcast_task_event({"type": "task_created", "task": deepcopy(task)})
    return {"task": task, "steps": get_task_steps(task["id"])}


@router.post("/capability")
async def execute_capability(payload: CapabilityRequest):
    """Create a canonical logical task and route a safe read capability.

    The first slice deliberately returns an explicit not-configured response for
    remote Edge dispatch; it never silently executes an Edge task on Central.
    """
    device = inventory_repository.get_device(payload.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    try:
        route = execution_routing_resolver.resolve(
            device,
            requested_location=payload.execution_location,
            requested_edge_id=payload.edge_id,
            requested_customer_id=payload.customer_id,
            requested_site_id=payload.site_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if route.location.value == "EDGE" and edge_identity_registry.state(str(route.edge_id)) is EdgeLifecycleState.QUARANTINED:
        raise HTTPException(status_code=403, detail="Edge is quarantined; privileged execution is disabled")
    execution_fingerprint = hashlib.sha256(f"{payload.device_id}:{payload.capability}:{payload.idempotency_key}".encode()).hexdigest()
    existing_attempt = await task_attempt_lease_store.get_by_idempotency(payload.idempotency_key)
    if existing_attempt is not None:
        same_operation = (
            existing_attempt.get("device_id") == payload.device_id
            and existing_attempt.get("capability") == payload.capability
            and existing_attempt.get("edge_id") == route.edge_id
            and existing_attempt.get("execution_location") == route.location.value
            and existing_attempt.get("execution_fingerprint") == execution_fingerprint
        )
        if not same_operation:
            raise HTTPException(status_code=409, detail="idempotency key is already bound to a different operation")
        existing_task = _find_task(str(existing_attempt.get("task_id", "")))
        return {
            "duplicate": True,
            "task": deepcopy(existing_task) if existing_task is not None else {
                "id": existing_attempt.get("task_id"),
                "status": "success" if existing_attempt.get("status") == "SUCCEEDED" else "queued",
                "device_id": payload.device_id,
                "capability": payload.capability,
                "execution_location": route.location.value,
                "attempt_id": existing_attempt.get("attempt_id"),
            },
            "attempt": existing_attempt,
            "route": route.__dict__,
        }
    task = register_task(
        task_id=payload.task_id,
        name=f"{payload.capability} - {device.get('hostname', payload.device_id)}",
        device=str(device.get("hostname", payload.device_id)),
        device_id=payload.device_id,
        action=payload.capability,
        status="queued",
        started=now_iso(),
        duration="-",
        user="api",
        agent="capability-router",
        steps=[],
    )
    attempt_id = f"attempt-{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)
    await task_attempt_lease_store.create(attempt_id, {
        "attempt_id": attempt_id,
        "task_id": task["id"],
        "edge_id": route.edge_id,
        "execution_location": route.location.value,
        "retry_class": RetryClass.SAFE_RETRY.value,
        "status": "QUEUED",
        "routing_reason": route.reason,
        "credential_ref": payload.credential_ref,
        "idempotency_key": payload.idempotency_key,
        "device_id": payload.device_id,
        "capability": payload.capability,
        "execution_location": route.location.value,
        "execution_fingerprint": execution_fingerprint,
        "accepted_at": now_iso(),
        "deadline_at": (payload.deadline_at or now + timedelta(minutes=5)).isoformat(),
        "lease_expires_at": (now + timedelta(seconds=60)).isoformat(),
    })
    task.update({"capability": payload.capability, "execution_location": route.location.value, "attempt_id": attempt_id})
    if route.location.value == "EDGE":
        if not payload.credential_ref:
            raise HTTPException(status_code=422, detail="EDGE execution requires credential_ref")
        try:
            validate_dispatchable_attempt(
                await task_attempt_lease_store.get(attempt_id) or {},
                expected_edge_id=route.edge_id,
                expected_capability=payload.capability,
                expected_execution_location=route.location.value,
                expected_fingerprint=execution_fingerprint,
            )
        except TaskExecutionGateError as exc:
            await task_attempt_lease_store.update(attempt_id, status="FAILED", error_code="TASK_EXECUTION_GATE_REJECTED")
            raise HTTPException(status_code=409, detail="TaskAttempt execution gate rejected") from exc
        claimed = await task_attempt_lease_store.claim_for_dispatch(attempt_id, edge_id=str(route.edge_id))
        if claimed is None:
            raise HTTPException(status_code=409, detail="TaskAttempt dispatch claim rejected")
        envelope = EdgeEnvelope(
            protocol_version=1,
            driver_capability_version=1,
            message_id=f"msg-{secrets.token_urlsafe(12)}",
            task_id=task["id"],
            attempt_id=attempt_id,
            edge_id=str(route.edge_id),
            sequence=0,
            nonce=secrets.token_urlsafe(24),
            issued_at=datetime.now(timezone.utc),
            valid_for_seconds=60,
            lease_duration_seconds=60,
            retry_class=RetryClass.SAFE_RETRY,
            capability=payload.capability,
            credential_ref=payload.credential_ref,
            idempotency_key=payload.idempotency_key,
            payload={
                "device_id": payload.device_id,
                "device_host": device.get("management_address"),
                "device_port": device.get("management_port") or 22,
                "device_vendor": device.get("vendor", ""),
            },
        )
        try:
            envelope_data = envelope.model_dump(mode="json")
            if not await edge_session_registry.enqueue_task(str(route.edge_id), envelope_data):
                raise EdgeDispatchError("Edge has no ready outbound session")
            result = await edge_session_registry.wait_task_result(str(route.edge_id), attempt_id, timeout_seconds=60)
            if result is None:
                raise EdgeDispatchError("Edge task result timed out")
        except EdgeDispatchError as exc:
            await task_attempt_lease_store.update(attempt_id, status="FAILED", error_code="EDGE_DISPATCH_FAILED")
            task.update({"status": "failed", "output": str(exc)})
            log_event(
                device_id=payload.device_id,
                action="TASK-EDGE-DISPATCH",
                command=payload.capability,
                result="EDGE_DISPATCH_FAILED",
                user="api",
                status="FAILED",
                error=type(exc).__name__,
            )
            await _broadcast_task_event({"type": "task_updated", "task": deepcopy(task)})
            raise HTTPException(status_code=503, detail={"code": "EDGE_DISPATCH_FAILED", "attempt_id": attempt_id}) from exc
        final_status = str(result.get("status", "FAILED")).upper()
        await task_attempt_lease_store.update(attempt_id, status=final_status, result=result, finished_at=now_iso())
        task.update({"status": "success" if final_status in {"SUCCEEDED", "OK"} else "failed", "output": result})
        log_event(
            device_id=payload.device_id,
            action="TASK-EDGE-EXECUTION",
            command=payload.capability,
            result=final_status,
            user="api",
            status=final_status,
            error=str(result.get("error_code")) if result.get("error_code") else None,
        )
        await _broadcast_task_event({"type": "task_updated", "task": deepcopy(task)})
    await _broadcast_task_event({"type": "task_created", "task": deepcopy(task)})
    return {"task": task, "attempt": await task_attempt_lease_store.get(attempt_id), "route": route.__dict__}


@router.post("/attempts/{attempt_id}/retry-decision")
async def retry_decision(
    attempt_id: str,
    payload: RetryDecisionRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
):
    if not operator_identity or payload.operator != operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role not in {"network-operator", "network-admin"}:
        raise HTTPException(status_code=403, detail="operator role is not permitted")
    if payload.operator_approved and operator_role not in {"network-operator", "network-admin"}:
        raise HTTPException(status_code=403, detail="operator approval role is not permitted")
    attempt = await task_attempt_lease_store.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Task attempt not found")
    try:
        retry_class = RetryClass(str(attempt.get("retry_class")))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Task attempt has invalid retry class") from exc
    if payload.operator_approved:
        try:
            HMACApprovalVerifier(settings.RETRY_APPROVAL_HMAC_SECRET, key_id=settings.RETRY_APPROVAL_KEY_ID).verify(
                payload.operator_approval_token or "",
                approval_ref=payload.operator_approval_ref or "",
                operator=payload.operator,
                attempt_id=attempt_id,
                fingerprint=str(attempt.get("execution_fingerprint", "")),
            )
        except ApprovalVerificationError as exc:
            raise HTTPException(status_code=403, detail="operator approval token is invalid") from exc
    verification = payload.verification
    if verification == "NOT_EXECUTED" and payload.execution_fingerprint != attempt.get("execution_fingerprint"):
        verification = "UNKNOWN"
    evaluation = evaluate_retry(
        retry_class=retry_class,
        prior_status=str(attempt.get("status", "")),
        idempotency_key=attempt.get("idempotency_key"),
        transport_lost=payload.transport_lost,
        verification=verification,
        operator_approved=payload.operator_approved,
    )
    updated = await task_attempt_lease_store.update(
        attempt_id,
        retry_decision=evaluation.decision.value,
        retry_reason=evaluation.reason,
        retry_evaluated_at=now_iso(),
        retry_operator=payload.operator,
        operator_approval_ref=payload.operator_approval_ref,
        operator_approval_token_hash=hashlib.sha256((payload.operator_approval_token or "").encode()).hexdigest() if payload.operator_approval_token else None,
    )
    log_event(
        device_id=str(attempt.get("task_id", "task-attempt")),
        action="TASK_RETRY_DECISION",
        command=f"retry-decision:{attempt_id}",
        result=evaluation.decision.value,
        user=payload.operator,
        status=evaluation.decision.value,
        error=evaluation.reason if evaluation.decision.value != "ALLOW" else None,
    )
    return {"attempt": updated, "decision": evaluation.decision.value, "reason": evaluation.reason, "replay_scheduled": False}


@router.post("/attempts/{attempt_id}/replay-plan")
async def replay_plan(
    attempt_id: str,
    payload: RetryDecisionRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
):
    if not operator_identity or payload.operator != operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role not in {"network-operator", "network-admin"}:
        raise HTTPException(status_code=403, detail="operator role is not permitted")
    attempt = await task_attempt_lease_store.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Task attempt not found")
    try:
        plan = build_replay_plan(
            attempt=attempt,
            operator=payload.operator,
            approval_ref=payload.operator_approval_ref or "",
            approval_token=payload.operator_approval_token or "",
            execution_fingerprint=payload.execution_fingerprint or "",
            verifier=HMACApprovalVerifier(settings.RETRY_APPROVAL_HMAC_SECRET, key_id=settings.RETRY_APPROVAL_KEY_ID),
        )
    except (ValueError, ApprovalVerificationError) as exc:
        raise HTTPException(status_code=409, detail="replay gate rejected") from exc
    log_event(device_id=str(attempt.get("task_id", "task-attempt")), action="TASK_REPLAY_PLAN", command=f"replay-plan:{attempt_id}", result="PREPARED_NOT_EXECUTED", user=payload.operator, status="PREPARED")
    return {"replay_plan": plan.__dict__, "execute": False}


@router.post("/attempts/{attempt_id}/replay-acquire")
async def replay_acquire(
    attempt_id: str,
    payload: RetryDecisionRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
):
    if not operator_identity or payload.operator != operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role not in {"network-operator", "network-admin"}:
        raise HTTPException(status_code=403, detail="operator role is not permitted")
    attempt = await task_attempt_lease_store.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Task attempt not found")
    try:
        plan = build_replay_plan(
            attempt=attempt,
            operator=payload.operator,
            approval_ref=payload.operator_approval_ref or "",
            approval_token=payload.operator_approval_token or "",
            execution_fingerprint=payload.execution_fingerprint or "",
            verifier=HMACApprovalVerifier(settings.RETRY_APPROVAL_HMAC_SECRET, key_id=settings.RETRY_APPROVAL_KEY_ID),
        )
        replay_idempotency = f"{attempt['idempotency_key']}:replay:{payload.operator_approval_ref}"
        replay_attempt_id = f"attempt-replay-{uuid.uuid4().hex[:16]}"
        child = await task_attempt_lease_store.create(replay_attempt_id, {
            "task_id": plan.task_id,
            "idempotency_key": replay_idempotency,
            "edge_id": attempt.get("edge_id"),
            "device_id": attempt.get("device_id"),
            "capability": plan.capability,
            "execution_location": plan.execution_location,
            "credential_ref": plan.credential_ref,
            "status": "QUEUED",
            "retry_class": attempt.get("retry_class"),
            "execution_fingerprint": attempt.get("execution_fingerprint"),
            "accepted_at": now_iso(),
            "deadline_at": attempt.get("deadline_at", now_iso()),
            "lease_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
            "replay_parent_attempt_id": attempt_id,
            "execution_status": "NOT_DISPATCHED",
        })
    except (ValueError, ApprovalVerificationError) as exc:
        raise HTTPException(status_code=409, detail="replay acquisition rejected") from exc
    log_event(device_id=str(attempt.get("task_id", "task-attempt")), action="TASK_REPLAY_ACQUIRE", command=f"replay-acquire:{attempt_id}", result="NOT_DISPATCHED", user=payload.operator, status="QUEUED")
    return {"attempt": child, "execute": False, "replay_parent_attempt_id": attempt_id}


@router.get("/attempts/{attempt_id}")
async def get_task_attempt(attempt_id: str):
    attempt = await task_attempt_lease_store.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Task attempt not found")
    return {"attempt": deepcopy(attempt)}


@router.patch("/{task_id}")
async def update_task(task_id: str, payload: dict[str, Any]):
    task = _find_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")

    if isinstance(payload.get("steps"), list):
        _task_steps[task_id] = [normalize_step(task_id, step, index) for index, step in enumerate(payload["steps"])]
        task["steps"] = deepcopy(_task_steps[task_id])

    task.update({k: v for k, v in payload.items() if k not in {"id", "steps"}})
    await _broadcast_task_event({"type": "task_updated", "task": deepcopy(task)})
    return {"task": deepcopy(task), "steps": get_task_steps(task_id)}


async def _broadcast_task_event(event: dict[str, Any]):
    for queue in list(_task_subscribers):
        try:
            await queue.put(event)
        except Exception:
            pass


_seed_tasks()
