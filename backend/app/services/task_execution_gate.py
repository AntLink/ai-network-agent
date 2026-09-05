"""Fail-closed validation immediately before dispatching a TaskAttempt."""
from __future__ import annotations

from datetime import datetime, timezone


class TaskExecutionGateError(ValueError):
    """The attempt is not safe or eligible for dispatch."""


def _timestamp(attempt: dict, field: str) -> datetime:
    value = attempt.get(field)
    if not value:
        raise TaskExecutionGateError(f"{field} is required")
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise TaskExecutionGateError(f"{field} is invalid") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def validate_dispatchable_attempt(
    attempt: dict,
    *,
    expected_edge_id: str | None,
    expected_capability: str,
    expected_execution_location: str,
    expected_fingerprint: str,
    now: datetime | None = None,
) -> dict:
    """Validate the current Central-owned lease without executing anything."""
    if not attempt.get("attempt_id") or not attempt.get("task_id"):
        raise TaskExecutionGateError("attempt and task identity are required")
    if attempt.get("lease_owner", "CENTRAL") != "CENTRAL":
        raise TaskExecutionGateError("Central lease ownership is required")
    if attempt.get("status") != "QUEUED":
        raise TaskExecutionGateError("attempt is not queued for dispatch")
    if attempt.get("execution_status") not in {None, "NOT_DISPATCHED"}:
        raise TaskExecutionGateError("attempt execution status is not dispatchable")
    if attempt.get("capability") != expected_capability:
        raise TaskExecutionGateError("capability does not match the dispatch request")
    if attempt.get("execution_location", "CENTRAL") != expected_execution_location:
        raise TaskExecutionGateError("execution location does not match the dispatch route")
    if expected_execution_location == "EDGE" and attempt.get("edge_id") != expected_edge_id:
        raise TaskExecutionGateError("attempt Edge does not match the dispatch route")
    if not attempt.get("idempotency_key"):
        raise TaskExecutionGateError("idempotency key is required")
    if not attempt.get("execution_fingerprint") or attempt.get("execution_fingerprint") != expected_fingerprint:
        raise TaskExecutionGateError("execution fingerprint does not match")
    if expected_execution_location == "EDGE" and not attempt.get("credential_ref"):
        raise TaskExecutionGateError("EDGE dispatch requires credential_ref")
    current = now or datetime.now(timezone.utc)
    if _timestamp(attempt, "deadline_at") < current:
        raise TaskExecutionGateError("task deadline has expired")
    if _timestamp(attempt, "lease_expires_at") < current:
        raise TaskExecutionGateError("TaskAttempt lease has expired")
    return attempt
