import asyncio

import httpx
import uuid
import base64
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.main import app
from app.services.task_attempt_leases import task_attempt_lease_store
from app.core.config import settings
from app.services.journal_signature import canonical_summary
from app.services.edge_identity import edge_identity_registry
from app.services.edge_sessions import InMemoryEdgeSessionRegistry


def request(method: str, path: str, **kwargs):
    async def call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(call())


def test_central_edge_handshake_and_separate_heartbeats():
    headers = {"X-Client-Edge-ID": "edge-test-1"}
    hello = request(
        "POST",
        "/api/v1/control/hello",
        json={
            "edge_id": "edge-test-1",
            "edge_version": "m1",
            "min_protocol_version": 1,
            "max_protocol_version": 1,
            "driver_capability_version": 1,
            "capabilities": ["device.read.facts"],
            "boot_id": "boot-test-1",
        },
        headers=headers,
    )
    assert hello.status_code == 200
    session_id = hello.json()["session_id"]

    ready = request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers)
    assert ready.status_code == 200
    presence = request(
        "POST",
        "/api/v1/control/heartbeat",
        json={"session_id": session_id, "edge_id": "edge-test-1", "boot_id": "boot-test-1"},
        headers=headers,
    )
    assert presence.status_code == 200
    task = request(
        "POST",
        "/api/v1/control/task-heartbeat",
        json={"session_id": session_id, "attempt_id": "attempt-test-1"},
        headers=headers,
    )
    assert task.status_code == 200
    assert task.json()["type"] == "TASK_HEARTBEAT_ACK"


def test_central_edge_task_poll_and_result_round_trip(monkeypatch):
    """The native Edge control contract carries one capability task end-to-end."""
    import app.api.v1.endpoints.edge_control as edge_control

    registry = InMemoryEdgeSessionRegistry()
    monkeypatch.setattr(edge_control, "edge_session_registry", registry)
    edge_id = f"edge-task-{uuid.uuid4().hex}"
    headers = {"X-Client-Edge-ID": edge_id}
    hello = request(
        "POST",
        "/api/v1/control/hello",
        json={
            "edge_id": edge_id,
            "edge_version": "m1",
            "min_protocol_version": 1,
            "max_protocol_version": 1,
            "driver_capability_version": 1,
            "capabilities": ["device.read.facts"],
            "boot_id": uuid.uuid4().hex,
        },
        headers=headers,
    )
    assert hello.status_code == 200
    session_id = hello.json()["session_id"]
    assert request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers).status_code == 200

    envelope = {
        "task_id": "task-contract-1",
        "attempt_id": "attempt-contract-1",
        "capability": "device.read.facts",
        "credential_ref": "cred-ref-only",
    }
    assert awaitable_run(registry.enqueue_task(edge_id, envelope)) is True
    next_task = request("POST", "/api/v1/control/tasks/next", json={"session_id": session_id}, headers=headers)
    assert next_task.status_code == 200
    assert next_task.json()["type"] == "TASK_AVAILABLE"
    assert next_task.json()["task"] == envelope

    result = {"status": "SUCCEEDED", "data": {"hostname": "R1", "vendor": "cisco"}}
    submitted = request(
        "POST",
        "/api/v1/control/tasks/result",
        json={"session_id": session_id, "attempt_id": envelope["attempt_id"], "result": result},
        headers=headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["type"] == "TASK_RESULT_ACK"
    assert awaitable_run(registry.wait_task_result(edge_id, envelope["attempt_id"], timeout_seconds=1)) == result


def awaitable_run(awaitable):
    """Run one registry coroutine without changing the existing sync test helper."""
    return asyncio.run(awaitable)


def test_central_rejects_heartbeat_before_ready():
    headers = {"X-Client-Edge-ID": "edge-test-2"}
    hello = request(
        "POST",
        "/api/v1/control/hello",
        json={
            "edge_id": "edge-test-2",
            "edge_version": "m1",
            "min_protocol_version": 1,
            "max_protocol_version": 1,
            "driver_capability_version": 1,
            "capabilities": [],
            "boot_id": "boot-test-2",
        },
        headers=headers,
    )
    session_id = hello.json()["session_id"]
    response = request(
        "POST",
        "/api/v1/control/heartbeat",
        json={"session_id": session_id, "edge_id": "edge-test-2", "boot_id": "boot-test-2"},
        headers=headers,
    )
    assert response.status_code == 409


def test_central_rejects_missing_edge_identity():
    response = request(
        "POST",
        "/api/v1/control/hello",
        json={
            "edge_id": "edge-test-3",
            "edge_version": "m1",
            "min_protocol_version": 1,
            "max_protocol_version": 1,
            "driver_capability_version": 1,
            "capabilities": [],
            "boot_id": "boot-test-3",
        },
    )
    assert response.status_code == 401


def test_central_marks_unresolved_attempts_for_reconciliation_without_replay():
    headers = {"X-Client-Edge-ID": "edge-reconcile-1"}
    response = request(
        "POST",
        "/api/v1/control/hello",
        json={
            "edge_id": "edge-reconcile-1",
            "edge_version": "m1",
            "min_protocol_version": 1,
            "max_protocol_version": 1,
            "driver_capability_version": 1,
            "capabilities": ["device.read.facts"],
            "boot_id": "boot-reconcile-1",
            "unresolved_attempt_ids": ["attempt-unknown-1", "attempt-unknown-2"],
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["reconciliation"] == {
        "attempt-unknown-1": "RECONCILE_REQUIRED",
        "attempt-unknown-2": "RECONCILE_REQUIRED",
    }


def test_central_reconciliation_classifies_terminal_unknown_and_scope_mismatch():
    attempt_id = f"attempt-reconcile-{uuid.uuid4().hex}"
    asyncio.run(task_attempt_lease_store.create(attempt_id, {
        "task_id": "task-reconcile",
        "edge_id": "edge-reconcile-known",
        "status": "SUCCEEDED",
        "result": {"status": "SUCCEEDED"},
        "idempotency_key": f"idem-{uuid.uuid4().hex}",
        "lease_expires_at": "2099-01-01T00:00:00+00:00",
    }))
    headers = {"X-Client-Edge-ID": "edge-reconcile-known"}
    hello = request("POST", "/api/v1/control/hello", json={
        "edge_id": "edge-reconcile-known", "edge_version": "m1", "min_protocol_version": 1,
        "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex,
    }, headers=headers)
    session_id = hello.json()["session_id"]
    assert request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers).status_code == 200
    result = request("POST", "/api/v1/control/reconcile", json={
        "session_id": session_id,
        "attempt_ids": [attempt_id, "attempt-does-not-exist"],
    }, headers=headers)
    assert result.status_code == 200
    decisions = result.json()["decisions"]
    assert decisions[attempt_id]["decision"] == "TERMINAL_RECORDED"
    assert decisions["attempt-does-not-exist"]["decision"] == "UNKNOWN_ATTEMPT"


def test_central_reconciliation_holds_mismatched_edge_summary():
    attempt_id = f"attempt-mismatch-{uuid.uuid4().hex}"
    asyncio.run(task_attempt_lease_store.create(attempt_id, {
        "task_id": "task-mismatch", "edge_id": "edge-mismatch", "status": "FAILED",
        "idempotency_key": f"idem-{uuid.uuid4().hex}", "lease_expires_at": "2099-01-01T00:00:00+00:00",
    }))
    headers = {"X-Client-Edge-ID": "edge-mismatch"}
    hello = request("POST", "/api/v1/control/hello", json={
        "edge_id": "edge-mismatch", "edge_version": "m1", "min_protocol_version": 1,
        "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex,
    }, headers=headers)
    session_id = hello.json()["session_id"]
    request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers)
    result = request("POST", "/api/v1/control/reconcile", json={
        "session_id": session_id, "summaries": [{"attempt_id": attempt_id, "status": "SUCCEEDED"}],
    }, headers=headers)
    assert result.json()["decisions"][attempt_id]["decision"] == "REPORT_MISMATCH"


def test_central_requires_valid_signed_summary_when_enabled(monkeypatch):
    attempt_id = f"attempt-signed-{uuid.uuid4().hex}"
    asyncio.run(task_attempt_lease_store.create(attempt_id, {
        "task_id": "task-signed", "edge_id": "edge-signed", "status": "FAILED",
        "idempotency_key": f"idem-{uuid.uuid4().hex}", "lease_expires_at": "2099-01-01T00:00:00+00:00",
    }))
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setattr(settings, "EDGE_RECONCILIATION_REQUIRE_SIGNATURE", True)
    monkeypatch.setattr(settings, "EDGE_RECONCILIATION_PUBLIC_KEYS_JSON", json.dumps({"edge-signed": base64.urlsafe_b64encode(public_key).rstrip(b"=").decode()}))
    summary = {"attempt_id": attempt_id, "idempotency_key": "reported-idem", "status": "FAILED", "result_available": False}
    signature = private_key.sign(canonical_summary(summary))
    summary["signature"] = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    headers = {"X-Client-Edge-ID": "edge-signed"}
    hello = request("POST", "/api/v1/control/hello", json={"edge_id": "edge-signed", "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers)
    session_id = hello.json()["session_id"]
    request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers)
    result = request("POST", "/api/v1/control/reconcile", json={"session_id": session_id, "summaries": [summary]}, headers=headers)
    assert result.status_code == 200
    assert result.json()["decisions"][attempt_id]["decision"] == "TERMINAL_RECORDED"


def test_central_rejects_valid_summary_from_revoked_edge(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setattr(settings, "EDGE_RECONCILIATION_REQUIRE_SIGNATURE", True)
    monkeypatch.setattr(settings, "EDGE_RECONCILIATION_PUBLIC_KEYS_JSON", json.dumps({"edge-revoked": base64.urlsafe_b64encode(public_key).rstrip(b"=").decode()}))
    monkeypatch.setattr(settings, "EDGE_RECONCILIATION_REVOKED_EDGES_JSON", json.dumps(["edge-revoked"]))
    headers = {"X-Client-Edge-ID": "edge-revoked"}
    hello = request("POST", "/api/v1/control/hello", json={"edge_id": "edge-revoked", "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers)
    session_id = hello.json()["session_id"]
    request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers)
    summary = {"attempt_id": "attempt-revoked", "idempotency_key": "idem-revoked", "status": "UNKNOWN", "result_available": False}
    signature = private_key.sign(canonical_summary(summary))
    summary["signature"] = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    result = request("POST", "/api/v1/control/reconcile", json={"session_id": session_id, "summaries": [summary]}, headers=headers)
    assert result.status_code == 401


def test_revoke_edge_disconnects_sessions_and_blocks_future_hello():
    edge_id = f"edge-revoke-{uuid.uuid4().hex}"
    headers = {"X-Client-Edge-ID": edge_id}
    hello = request("POST", "/api/v1/control/hello", json={"edge_id": edge_id, "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers)
    assert hello.status_code == 200
    session_id = hello.json()["session_id"]
    assert request("POST", "/api/v1/control/ready", json={"session_id": session_id}, headers=headers).status_code == 200
    revoked = request("POST", "/api/v1/control/revoke", json={"edge_id": edge_id, "reason": "test compromise"}, headers={"X-Authenticated-Operator": "admin-1", "X-Operator-Role": "network-admin"})
    assert revoked.status_code == 200
    assert revoked.json()["state"] == "REVOKED"
    assert revoked.json()["disconnected_sessions"] == 1
    assert request("POST", "/api/v1/control/heartbeat", json={"session_id": session_id, "edge_id": edge_id, "boot_id": "ignored"}, headers=headers).status_code == 403
    assert request("POST", "/api/v1/control/hello", json={"edge_id": edge_id, "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers).status_code == 403


def test_quarantine_preserves_limited_control_channel_but_changes_state():
    edge_id = f"edge-quarantine-{uuid.uuid4().hex}"
    headers = {"X-Client-Edge-ID": edge_id}
    hello = request("POST", "/api/v1/control/hello", json={"edge_id": edge_id, "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers)
    assert hello.status_code == 200
    response = request("POST", "/api/v1/control/quarantine", json={"edge_id": edge_id, "reason": "investigation"}, headers={"X-Authenticated-Operator": "admin-2", "X-Operator-Role": "network-admin"})
    assert response.status_code == 200
    assert response.json() == {"edge_id": edge_id, "state": "QUARANTINED", "recovery_channel": "LIMITED"}
    assert request("POST", "/api/v1/control/hello", json={"edge_id": edge_id, "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers).status_code == 200


def test_clear_quarantine_requires_admin_and_restores_active_hello():
    edge_id = f"edge-clear-quarantine-{uuid.uuid4().hex}"
    headers = {"X-Client-Edge-ID": edge_id}
    request("POST", "/api/v1/control/quarantine", json={"edge_id": edge_id, "reason": "test"}, headers={"X-Authenticated-Operator": "admin-3", "X-Operator-Role": "network-admin"})
    denied = request("POST", "/api/v1/control/clear-quarantine", json={"edge_id": edge_id, "reason": "reviewed"}, headers={"X-Authenticated-Operator": "operator-3", "X-Operator-Role": "network-operator"})
    assert denied.status_code == 403
    cleared = request("POST", "/api/v1/control/clear-quarantine", json={"edge_id": edge_id, "reason": "reviewed"}, headers={"X-Authenticated-Operator": "admin-3", "X-Operator-Role": "network-admin"})
    assert cleared.status_code == 200
    assert cleared.json() == {"edge_id": edge_id, "state": "ACTIVE"}
    assert request("POST", "/api/v1/control/hello", json={"edge_id": edge_id, "edge_version": "m1", "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": [], "boot_id": uuid.uuid4().hex}, headers=headers).status_code == 200
