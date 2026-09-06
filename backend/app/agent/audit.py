"""Audit helpers for agent actions.

The first implementation only creates normalized records. Persistence is kept
separate so existing endpoints can adopt this gradually.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    user: str
    session_id: str
    task_id: str
    source: str
    action: str
    target_type: str
    target_id: str
    policy: str
    risk: str
    result: str
    evidence: str
    summary: str
    approval_id: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": f"audit-{uuid.uuid4().hex[:12]}",
            "time": datetime.utcnow().isoformat(),
            "user": self.user,
            "sessionId": self.session_id,
            "taskId": self.task_id,
            "approvalId": self.approval_id or None,
            "source": self.source,
            "action": self.action,
            "targetType": self.target_type,
            "targetId": self.target_id,
            "policy": self.policy,
            "risk": self.risk,
            "result": self.result,
            "evidence": self.evidence,
            "summary": _scrub_secret_text(self.summary),
            "error": _scrub_secret_text(self.error) if self.error else None,
        }


def build_audit_record(**kwargs) -> dict[str, Any]:
    return AuditRecord(**kwargs).to_dict()


def _scrub_secret_text(value: str) -> str:
    redacted = value or ""
    secret_markers = ("password", "secret", "token", "apikey", "api_key", "private-key")
    for marker in secret_markers:
        lowered = redacted.lower()
        while marker in lowered:
            index = lowered.find(marker)
            end = redacted.find("\n", index)
            if end == -1:
                end = len(redacted)
            redacted = redacted[:index] + f"{marker}=<redacted>" + redacted[end:]
            lowered = redacted.lower()
    return redacted
