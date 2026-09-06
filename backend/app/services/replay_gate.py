"""Fail-closed gate for preparing, but not executing, a retry replay."""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.edge import RetryClass
from app.services.approval_verifier import HMACApprovalVerifier


@dataclass(frozen=True)
class ReplayPlan:
    attempt_id: str
    task_id: str
    capability: str
    execution_location: str
    credential_ref: str | None
    execute: bool = False


def build_replay_plan(*, attempt: dict, operator: str, approval_ref: str, approval_token: str, execution_fingerprint: str, verifier: HMACApprovalVerifier) -> ReplayPlan:
    if attempt.get("retry_decision") != "ALLOW":
        raise ValueError("retry decision is not ALLOW")
    if attempt.get("status") in {"SUCCEEDED", "UNKNOWN_EXECUTION_STATE"}:
        raise ValueError("attempt is not eligible for replay")
    if attempt.get("capability") != "device.read.facts":
        raise ValueError("capability is not approved for replay plan")
    expected = str(attempt.get("execution_fingerprint", ""))
    if not expected or execution_fingerprint != expected:
        raise ValueError("execution fingerprint does not match")
    verifier.verify(
        approval_token,
        approval_ref=approval_ref,
        operator=operator,
        attempt_id=str(attempt["attempt_id"]),
        fingerprint=expected,
    )
    return ReplayPlan(
        attempt_id=str(attempt["attempt_id"]),
        task_id=str(attempt["task_id"]),
        capability=str(attempt["capability"]),
        execution_location=str(attempt.get("execution_location", "CENTRAL")),
        credential_ref=attempt.get("credential_ref"),
    )
