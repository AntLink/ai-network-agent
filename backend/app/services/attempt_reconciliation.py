"""Central-side classification of Edge-reported unresolved attempts."""
from __future__ import annotations

from typing import Any


TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED_BEFORE_START"}


async def reconcile_attempts(*, attempt_ids: list[str], edge_id: str, store: Any, summaries: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Classify attempts without creating a retry or dispatching a device action."""
    decisions: dict[str, dict[str, Any]] = {}
    reported = {str(item.get("attempt_id")): item for item in (summaries or []) if item.get("attempt_id")}
    for attempt_id in dict.fromkeys(attempt_ids or list(reported)):
        if not attempt_id:
            continue
        attempt = await store.get(attempt_id)
        if attempt is None:
            decisions[attempt_id] = {"decision": "UNKNOWN_ATTEMPT"}
            continue
        if attempt.get("edge_id") != edge_id:
            decisions[attempt_id] = {"decision": "EDGE_SCOPE_MISMATCH"}
            continue
        status = str(attempt.get("status", ""))
        reported_status = reported.get(attempt_id, {}).get("status")
        if reported_status and str(reported_status) != status:
            decisions[attempt_id] = {"decision": "REPORT_MISMATCH", "central_status": status, "reported_status": str(reported_status)}
            continue
        if status in TERMINAL_STATUSES:
            decisions[attempt_id] = {
                "decision": "TERMINAL_RECORDED",
                "status": status,
                "result": attempt.get("result"),
                "error_code": attempt.get("error_code"),
            }
        else:
            decisions[attempt_id] = {"decision": "RECONCILE_REQUIRED", "status": status}
    return decisions
