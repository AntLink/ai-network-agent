"""Approval gate for agent workflows.

An approval is a pending decision that a workflow (e.g. the workspace sub-agent)
waits on before executing a state-changing action. The `/agent/execute` and
`/agent/cancel` endpoints resolve it, so the same card that the UI shows is what
unblocks the paused workflow.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any

_pending: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_approval(
    *,
    task_id: str,
    task: str,
    commands: list[str],
    risk: str = "medium",
    message: str = "",
    timeout_seconds: int = 180,
) -> tuple[str, dict[str, Any]]:
    """Create a pending approval and return (approval_id, approval_event)."""
    approval_id = f"approval-{uuid.uuid4().hex[:12]}"
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()
    _pending[approval_id] = {
        "future": future,
        "task_id": task_id,
        "task": task,
        "commands": list(commands),
        "risk": risk,
        "created_at": time.monotonic(),
        "timeout_seconds": timeout_seconds,
    }
    event = {
        "id": approval_id,
        "taskId": approval_id,
        "task": task,
        "devices": [],
        "risk": risk,
        "status": "required",
        "message": message or "Approval required before executing this command.",
        "commands": list(commands),
        "createdAt": _now(),
    }
    return approval_id, event


def poll_approval(approval_id: str) -> dict[str, Any] | None:
    """Return a resolution dict when resolved/expired, else None while pending."""
    entry = _pending.get(approval_id)
    if entry is None:
        return {"status": "expired", "approved_by": ""}
    future: asyncio.Future = entry["future"]
    if future.done():
        return future.result()
    if time.monotonic() - entry["created_at"] > entry["timeout_seconds"]:
        return {"status": "expired", "approved_by": ""}
    return None


def resolve_approval(approval_id: str, status: str, by: str) -> bool:
    """Resolve a pending approval. Returns True if it was still pending."""
    entry = _pending.get(approval_id)
    if entry is None:
        return False
    future: asyncio.Future = entry["future"]
    if future.done():
        return False
    future.set_result({"status": status, "approved_by": by})
    return True
