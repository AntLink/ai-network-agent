from datetime import datetime, timedelta, timezone

import pytest

from app.services.task_execution_gate import TaskExecutionGateError, validate_dispatchable_attempt


def _attempt(**overrides):
    now = datetime.now(timezone.utc)
    value = {
        "attempt_id": "attempt-gate",
        "task_id": "task-gate",
        "lease_owner": "CENTRAL",
        "status": "QUEUED",
        "execution_status": "NOT_DISPATCHED",
        "edge_id": "edge-1",
        "execution_location": "EDGE",
        "capability": "device.read.facts",
        "credential_ref": "cred-1",
        "idempotency_key": "idem-gate",
        "execution_fingerprint": "f" * 64,
        "deadline_at": (now + timedelta(minutes=5)).isoformat(),
        "lease_expires_at": (now + timedelta(seconds=60)).isoformat(),
    }
    value.update(overrides)
    return value


def test_execution_gate_accepts_fresh_queued_edge_attempt():
    result = validate_dispatchable_attempt(
        _attempt(),
        expected_edge_id="edge-1",
        expected_capability="device.read.facts",
        expected_execution_location="EDGE",
        expected_fingerprint="f" * 64,
    )
    assert result["attempt_id"] == "attempt-gate"


@pytest.mark.parametrize("overrides", [
    {"status": "RUNNING"},
    {"execution_status": "SUCCEEDED"},
    {"lease_expires_at": "2020-01-01T00:00:00+00:00"},
    {"deadline_at": "2020-01-01T00:00:00+00:00"},
    {"credential_ref": None},
])
def test_execution_gate_rejects_unsafe_or_stale_attempt(overrides):
    with pytest.raises(TaskExecutionGateError):
        validate_dispatchable_attempt(
            _attempt(**overrides),
            expected_edge_id="edge-1",
            expected_capability="device.read.facts",
            expected_execution_location="EDGE",
            expected_fingerprint="f" * 64,
        )
