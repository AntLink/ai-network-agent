"""Central control-plane endpoints for outbound Edge sessions.

Deployment must place these endpoints behind the Central mTLS termination and
identity validation layer. This in-process registry is an M1 ephemeral seam;
Redis-backed distributed session state is a later HA milestone.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.services.edge_sessions import build_edge_session_registry
from app.services.task_attempt_leases import task_attempt_lease_store
from app.services.attempt_reconciliation import reconcile_attempts
from app.services.journal_signature import EdgeJournalKeyRegistry, JournalSignatureError, verify_summary_signature
from app.services.edge_identity import EdgeLifecycleState, edge_identity_registry
from app.services.certificate_revocation import CertificateRevocationRegistry
from app.core.audit import log_event

router = APIRouter()


class HelloRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1, max_length=200)
    edge_version: str = Field(min_length=1, max_length=100)
    min_protocol_version: int = 1
    max_protocol_version: int = 1
    driver_capability_version: int = 1
    capabilities: list[str] = Field(default_factory=list)
    boot_id: str = Field(min_length=1, max_length=200)
    unresolved_attempt_ids: list[str] = Field(default_factory=list, max_length=256)


class ReadyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=300)


class PresenceHeartbeatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=300)
    edge_id: str = Field(min_length=1, max_length=200)
    boot_id: str = Field(min_length=1, max_length=200)


class TaskHeartbeatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=300)
    attempt_id: str = Field(min_length=1, max_length=300)
    sent_at: datetime | None = None


class ReconcileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=300)
    attempt_ids: list[str] = Field(default_factory=list, max_length=256)
    summaries: list[dict[str, str | bool | None]] = Field(default_factory=list, max_length=256)


class RevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=300)
    certificate_fingerprint: str | None = Field(default=None, max_length=80)
    certificate_serial: str | None = Field(default=None, max_length=200)


class TaskResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=300)
    attempt_id: str = Field(min_length=1, max_length=300)
    result: dict = Field(default_factory=dict)


EDGE_IDENTITY_HEADER = "X-Client-Edge-ID"
edge_session_registry = build_edge_session_registry(
    backend=settings.EDGE_SESSION_BACKEND,
    redis_url=settings.REDIS_URL,
    ttl_seconds=settings.EDGE_SESSION_TTL_SECONDS,
)
certificate_revocation_registry = CertificateRevocationRegistry(settings.EDGE_CERT_REVOCATION_STATE_FILE)


def _require_identity(identity: str | None, expected: str) -> None:
    if not identity or identity != expected:
        raise HTTPException(status_code=401, detail="Edge certificate identity is required")


async def _session(session_id: str):
    current = await edge_session_registry.get(session_id)
    if current is None:
        raise HTTPException(status_code=403, detail="unknown Edge control session")
    return current


@router.post("/control/hello")
async def hello(request: HelloRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER), certificate_fingerprint: str | None = Header(default=None, alias="X-Client-Cert-Fingerprint")) -> dict[str, object]:
    _require_identity(edge_identity, request.edge_id)
    if certificate_revocation_registry.is_revoked(certificate_fingerprint):
        raise HTTPException(status_code=403, detail="Edge certificate is revoked")
    if edge_identity_registry.state(request.edge_id) in {EdgeLifecycleState.REVOKED, EdgeLifecycleState.DELETED}:
        raise HTTPException(status_code=403, detail="Edge identity is not permitted")
    if request.min_protocol_version > 1 or request.max_protocol_version < 1:
        raise HTTPException(status_code=400, detail="unsupported protocol version")
    if request.driver_capability_version != 1:
        raise HTTPException(status_code=400, detail="unsupported driver capability version")
    session_id = await edge_session_registry.create(edge_id=request.edge_id, boot_id=request.boot_id)
    return {
        "type": "WELCOME",
        "session_id": session_id,
        "protocol_version": 1,
        "driver_capability_version": 1,
        "heartbeat_interval_seconds": 15,
        "server_time": datetime.now(timezone.utc),
        "reconciliation": {attempt_id: "RECONCILE_REQUIRED" for attempt_id in request.unresolved_attempt_ids if attempt_id},
    }


@router.post("/control/ready")
async def ready(request: ReadyRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, str]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    await edge_session_registry.mark_ready(request.session_id)
    return {"type": "READY_ACK", "session_id": request.session_id}


@router.post("/control/heartbeat")
async def presence_heartbeat(request: PresenceHeartbeatRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, object]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    if not await edge_session_registry.touch_presence(request.session_id, edge_id=request.edge_id, boot_id=request.boot_id):
        raise HTTPException(status_code=409, detail="Edge control session is not ready")
    return {"type": "SESSION_HEARTBEAT_ACK", "session_id": request.session_id, "server_time": datetime.now(timezone.utc)}


@router.post("/control/task-heartbeat")
async def task_heartbeat(request: TaskHeartbeatRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, object]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    if not await edge_session_registry.record_task_heartbeat(request.session_id, attempt_id=request.attempt_id, sent_at=request.sent_at):
        raise HTTPException(status_code=409, detail="Edge control session is not ready")
    renewed = await task_attempt_lease_store.renew(
        request.attempt_id,
        edge_id=edge_identity or "",
        now=datetime.now(timezone.utc),
    ) is not None
    # Central decides whether a known, owned, unexpired attempt may renew.
    return {"type": "TASK_HEARTBEAT_ACK", "session_id": request.session_id, "attempt_id": request.attempt_id, "lease_renewed": renewed, "server_time": datetime.now(timezone.utc)}


@router.post("/control/tasks/next")
async def next_task(request: ReadyRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, object]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    if not session.ready:
        raise HTTPException(status_code=409, detail="Edge control session is not ready")
    envelope = await edge_session_registry.claim_task(request.session_id)
    return {"type": "TASK_AVAILABLE" if envelope else "NO_TASK", "session_id": request.session_id, "task": envelope}


@router.post("/control/tasks/result")
async def task_result(request: TaskResultRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, object]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    if not await edge_session_registry.submit_task_result(request.session_id, request.attempt_id, request.result):
        raise HTTPException(status_code=409, detail="Edge control session is not ready")
    return {"type": "TASK_RESULT_ACK", "session_id": request.session_id, "attempt_id": request.attempt_id}


@router.post("/control/reconcile")
async def reconcile(request: ReconcileRequest, edge_identity: str | None = Header(default=None, alias=EDGE_IDENTITY_HEADER)) -> dict[str, object]:
    session = await _session(request.session_id)
    _require_identity(edge_identity, session.edge_id)
    if not session.ready:
        raise HTTPException(status_code=409, detail="Edge control session is not ready")
    try:
        public_keys = json.loads(settings.EDGE_RECONCILIATION_PUBLIC_KEYS_JSON)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail="Edge reconciliation key registry is invalid") from exc
    if not isinstance(public_keys, dict):
        raise HTTPException(status_code=503, detail="Edge reconciliation key registry is invalid")
    try:
        revoked_edges = json.loads(settings.EDGE_RECONCILIATION_REVOKED_EDGES_JSON)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail="Edge revocation registry is invalid") from exc
    if not isinstance(revoked_edges, list) or not all(isinstance(edge_id, str) for edge_id in revoked_edges):
        raise HTTPException(status_code=503, detail="Edge revocation registry is invalid")
    registry = EdgeJournalKeyRegistry(public_keys, set(revoked_edges))
    if settings.EDGE_RECONCILIATION_REQUIRE_SIGNATURE:
        try:
            for summary in request.summaries:
                verify_summary_signature(edge_id=session.edge_id, summary=summary, public_keys=registry.verification_keys())
        except JournalSignatureError as exc:
            raise HTTPException(status_code=401, detail="signed journal summary is invalid") from exc
    decisions = await reconcile_attempts(
        attempt_ids=request.attempt_ids,
        summaries=request.summaries,
        edge_id=session.edge_id,
        store=task_attempt_lease_store,
    )
    return {"type": "RECONCILIATION_RESULT", "session_id": request.session_id, "decisions": decisions}


@router.post("/control/revoke")
async def revoke_edge(
    request: RevokeRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
) -> dict[str, object]:
    if not operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role != "network-admin":
        raise HTTPException(status_code=403, detail="network-admin role is required")
    try:
        state = edge_identity_registry.set_state(request.edge_id, EdgeLifecycleState.REVOKED)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="Edge lifecycle transition rejected") from exc
    disconnected = await edge_session_registry.revoke_edge(request.edge_id)
    certificate_revoked = False
    if request.certificate_fingerprint:
        try:
            certificate_revocation_registry.revoke(
                fingerprint=request.certificate_fingerprint,
                serial=request.certificate_serial,
                reason=request.reason,
            )
            certificate_revoked = True
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid certificate fingerprint") from exc
    log_event(device_id=request.edge_id, action="EDGE_REVOKE", command="edge-revoke", result="REVOKED", user=operator_identity, status="REVOKED", error=request.reason)
    return {"edge_id": request.edge_id, "state": state.value, "disconnected_sessions": disconnected, "certificate_revoked": certificate_revoked}


@router.post("/control/quarantine")
async def quarantine_edge(
    request: RevokeRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
) -> dict[str, object]:
    if not operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role != "network-admin":
        raise HTTPException(status_code=403, detail="network-admin role is required")
    try:
        state = edge_identity_registry.set_state(request.edge_id, EdgeLifecycleState.QUARANTINED)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="Edge lifecycle transition rejected") from exc
    log_event(device_id=request.edge_id, action="EDGE_QUARANTINE", command="edge-quarantine", result="QUARANTINED", user=operator_identity, status="QUARANTINED", error=request.reason)
    return {"edge_id": request.edge_id, "state": state.value, "recovery_channel": "LIMITED"}


@router.post("/control/clear-quarantine")
async def clear_quarantine(
    request: RevokeRequest,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
) -> dict[str, object]:
    if not operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role != "network-admin":
        raise HTTPException(status_code=403, detail="network-admin role is required")
    try:
        state = edge_identity_registry.clear_quarantine(request.edge_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="Edge is not quarantined") from exc
    log_event(device_id=request.edge_id, action="EDGE_CLEAR_QUARANTINE", command="edge-clear-quarantine", result="ACTIVE", user=operator_identity, status="ACTIVE", error=request.reason)
    return {"edge_id": request.edge_id, "state": state.value}
