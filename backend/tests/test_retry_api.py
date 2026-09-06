import asyncio
import uuid

import httpx

from app.main import app
from app.core.config import settings
from app.services.approval_verifier import HMACApprovalVerifier
from app.services.task_attempt_leases import task_attempt_lease_store


def test_retry_decision_api_requires_review_for_unknown_transport_execution():
    attempt_id = f"attempt-review-{uuid.uuid4().hex}"

    async def setup_and_request():
        await task_attempt_lease_store.create(
            attempt_id,
            {
                "task_id": "task-review",
                "edge_id": "edge-1",
                "status": "RUNNING",
                "retry_class": "SAFE_RETRY",
                "idempotency_key": "idem-review",
                "lease_expires_at": "2099-01-01T00:00:00+00:00",
            },
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                f"/api/v1/tasks/attempts/{attempt_id}/retry-decision",
                json={"transport_lost": True, "operator": "operator-1"},
                headers={"X-Authenticated-Operator": "operator-1", "X-Operator-Role": "network-operator"},
            )

    response = asyncio.run(setup_and_request())
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REQUIRE_REVIEW"
    assert body["replay_scheduled"] is False


def test_retry_decision_rejects_unverified_non_execution_fingerprint():
    attempt_id = f"attempt-fingerprint-{uuid.uuid4().hex}"

    async def setup_and_request():
        await task_attempt_lease_store.create(
            attempt_id,
            {
                "task_id": "task-fingerprint",
                "edge_id": "edge-1",
                "status": "FAILED",
                "retry_class": "CONDITIONAL_RETRY",
                "idempotency_key": "idem-fingerprint",
                "execution_fingerprint": "a" * 64,
                "lease_expires_at": "2099-01-01T00:00:00+00:00",
            },
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                f"/api/v1/tasks/attempts/{attempt_id}/retry-decision",
                json={"verification": "NOT_EXECUTED", "execution_fingerprint": "b" * 64, "operator_approved": False, "operator": "operator-2"},
                headers={"X-Authenticated-Operator": "operator-2", "X-Operator-Role": "network-operator"},
            )

    response = asyncio.run(setup_and_request())
    assert response.status_code == 200
    assert response.json()["decision"] == "REQUIRE_REVIEW"


def test_retry_decision_requires_authenticated_operator_identity():
    async def call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/api/v1/tasks/attempts/does-not-matter/retry-decision",
                json={"operator": "operator-3"},
            )

    response = asyncio.run(call())
    assert response.status_code == 401


def test_retry_approval_requires_approval_reference():
    async def call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/api/v1/tasks/attempts/does-not-matter/retry-decision",
                json={"operator": "operator-4", "operator_approved": True},
                headers={"X-Authenticated-Operator": "operator-4", "X-Operator-Role": "network-admin"},
            )

    response = asyncio.run(call())
    assert response.status_code == 422


def test_replay_acquire_creates_fresh_lease_and_rejects_duplicate_idempotency(monkeypatch):
    attempt_id = f"attempt-replay-parent-{uuid.uuid4().hex}"
    fingerprint = "c" * 64
    approval_ref = f"approval-{uuid.uuid4().hex}"
    verifier = HMACApprovalVerifier("replay-test-secret", key_id="test")
    token = verifier.issue_token(
        approval_ref=approval_ref,
        operator="operator-replay",
        attempt_id=attempt_id,
        fingerprint=fingerprint,
        expires_at=4102444800,
    )
    monkeypatch.setattr(settings, "RETRY_APPROVAL_HMAC_SECRET", "replay-test-secret")
    monkeypatch.setattr(settings, "RETRY_APPROVAL_KEY_ID", "test")

    async def setup_and_request():
        await task_attempt_lease_store.create(
            attempt_id,
            {
                "task_id": "task-replay",
                "edge_id": "edge-1",
                "device_id": "device-1",
                "capability": "device.read.facts",
                "execution_location": "EDGE",
                "credential_ref": "cred-ref-1",
                "status": "FAILED",
                "retry_class": "SAFE_RETRY",
                "idempotency_key": f"idem-parent-{uuid.uuid4().hex}",
                "execution_fingerprint": fingerprint,
                "retry_decision": "ALLOW",
                "deadline_at": "2099-01-01T00:00:00+00:00",
                "lease_expires_at": "2099-01-01T00:00:00+00:00",
            },
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            request = {
                "operator": "operator-replay",
                "execution_fingerprint": fingerprint,
                "operator_approval_ref": approval_ref,
                "operator_approval_token": token,
            }
            first = await client.post(
                f"/api/v1/tasks/attempts/{attempt_id}/replay-acquire",
                json=request,
                headers={"X-Authenticated-Operator": "operator-replay", "X-Operator-Role": "network-admin"},
            )
            second = await client.post(
                f"/api/v1/tasks/attempts/{attempt_id}/replay-acquire",
                json=request,
                headers={"X-Authenticated-Operator": "operator-replay", "X-Operator-Role": "network-admin"},
            )
            return first, second

    first, second = asyncio.run(setup_and_request())
    assert first.status_code == 200
    child = first.json()["attempt"]
    assert first.json()["execute"] is False
    assert child["replay_parent_attempt_id"] == attempt_id
    assert child["execution_status"] == "NOT_DISPATCHED"
    assert child["lease_expires_at"] != "2099-01-01T00:00:00+00:00"
    assert second.status_code == 409
