import time

import pytest

from app.services.approval_verifier import HMACApprovalVerifier
from app.services.replay_gate import build_replay_plan


def test_replay_gate_prepares_safe_plan_only_after_allow_and_valid_token():
    verifier = HMACApprovalVerifier("test-secret")
    fingerprint = "f" * 64
    token = verifier.issue_token(approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint=fingerprint, expires_at=int(time.time()) + 60)
    plan = build_replay_plan(
        attempt={"attempt_id": "attempt-1", "task_id": "task-1", "status": "FAILED", "retry_decision": "ALLOW", "capability": "device.read.facts", "execution_location": "EDGE", "credential_ref": "cred-1", "execution_fingerprint": fingerprint},
        operator="operator-1", approval_ref="approval-1", approval_token=token, execution_fingerprint=fingerprint, verifier=verifier,
    )
    assert plan.execute is False
    assert plan.credential_ref == "cred-1"


def test_replay_gate_rejects_non_allow():
    with pytest.raises(ValueError, match="not ALLOW"):
        build_replay_plan(
            attempt={"attempt_id": "attempt-2", "task_id": "task-2", "status": "FAILED", "retry_decision": "REQUIRE_REVIEW", "capability": "device.read.facts", "execution_fingerprint": "f" * 64},
            operator="operator-1", approval_ref="approval-1", approval_token="invalid-token", execution_fingerprint="f" * 64, verifier=HMACApprovalVerifier("test-secret"),
        )
