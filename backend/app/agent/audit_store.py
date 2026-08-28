"""Append-only audit persistence for AI Network Agent actions.

Stores normalized audit records (see `audit.py`) to a JSON lines file so agent
actions survive restarts and can be reviewed independently of the in-memory
event bus.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.agent.audit import build_audit_record

AUDIT_FILE = Path(__file__).resolve().parents[3] / "logs" / "agent-audit.json"

_write_lock = threading.Lock()


def record(**kwargs: Any) -> dict[str, Any]:
    """Build a normalized audit record and append it to the audit log."""
    entry = build_audit_record(**kwargs)
    try:
        with _write_lock:
            AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with AUDIT_FILE.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:  # noqa: BLE001
        pass
    return entry


def list_records(limit: int = 200) -> list[dict[str, Any]]:
    """Return the most recent audit records (newest first)."""
    if not AUDIT_FILE.exists():
        return []
    try:
        lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:  # noqa: BLE001
        return []
    records: list[dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
        if len(records) >= limit:
            break
    return records
