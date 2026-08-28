"""Event builders for agent SSE/WebSocket consumers."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.agent.state_machine import build_workflow_state_event


def build_event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "id": f"evt-{uuid.uuid4().hex[:12]}",
        "type": event_type,
        "createdAt": datetime.utcnow().isoformat(),
    }
    event.update(payload or {})
    return event


def build_start_event(
    *,
    session_id: str | None,
    device_ids: list[str],
    lab_id: str | None = None,
    project_id: str | None = None,
    environment: str = "lab",
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_event(
        "start",
        {
            "session_id": session_id,
            "device_ids": device_ids,
            "lab_id": lab_id,
            "project_id": project_id,
            "environment": environment,
            "intent": intent,
        },
    )


def build_agent_workflow_event(**kwargs) -> dict[str, Any]:
    return build_event("workflow_state", build_workflow_state_event(**kwargs))


def build_tool_output(
    *,
    tool: str,
    policy: str,
    evidence: str,
    target: dict[str, Any],
    summary: str,
    data: dict[str, Any] | None = None,
    raw: str = "",
    error: str | None = None,
) -> dict[str, Any]:
    return build_event(
        "tool_output",
        {
            "status": "failed" if error else "ok",
            "tool": tool,
            "policy": policy,
            "evidence": evidence,
            "target": target,
            "summary": summary,
            "data": data or {},
            "raw": raw,
            "error": error,
        },
    )
