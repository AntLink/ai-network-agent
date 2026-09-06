from pathlib import Path
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

LOG_FILE = Path("C:/Users/mohfa/PycharmProjects/ai-network-agent/logs/audit.log")


def _infer_result(action: str, command: str) -> str:
    action_lower = action.lower()
    if action_lower in ("error", "failed", "rollback"):
        return "failed"
    if action_lower in ("pending", "queued"):
        return "pending"
    return "success"


def _infer_source(action: str, user: str) -> str:
    user_lower = user.lower()
    action_lower = action.lower()
    if user_lower in ("system", "agent", "ai"):
        return "ai-agent"
    if action_lower.startswith("auto") or action_lower in ("health_check", "monitor"):
        return "automation"
    if user_lower.startswith("api") or user_lower == "webhook":
        return "api"
    return "user"


@router.get("")
async def audit_events(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    search: Optional[str] = Query(None, description="Free text search"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    device: Optional[str] = Query(None, description="Filter by device_id"),
    result: Optional[str] = Query(None, description="Filter by result"),
    source: Optional[str] = Query(None, description="Filter by source"),
    user: Optional[str] = Query(None, description="Filter by user"),
):
    if not LOG_FILE.exists():
        return {"events": [], "total": 0, "page": page, "limit": limit, "pages": 0, "filters": {}}

    lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
    all_events = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(" | ")
        timestamp = parts[0].strip() if len(parts) > 0 else ""
        device_id = parts[1].strip() if len(parts) > 1 else ""
        act = parts[2].strip() if len(parts) > 2 else ""
        command = parts[3].strip() if len(parts) > 3 else ""
        usr = parts[4].replace("user=", "").strip() if len(parts) > 4 else "system"

        res = _infer_result(act, command)
        src = _infer_source(act, usr)

        all_events.append({
            "timestamp": timestamp,
            "device_id": device_id,
            "action": act,
            "command": command,
            "user": usr,
            "result": res,
            "source": src,
        })

    # Reverse — newest first
    all_events.reverse()

    # Apply filters
    filtered = all_events
    if search:
        q = search.lower()
        filtered = [e for e in filtered if q in e["action"].lower() or q in e["device_id"].lower() or q in e["command"].lower() or q in e["user"].lower() or q in e["timestamp"].lower()]
    if action:
        filtered = [e for e in filtered if e["action"].lower() == action.lower()]
    if device:
        filtered = [e for e in filtered if e["device_id"].lower() == device.lower()]
    if result:
        filtered = [e for e in filtered if e["result"].lower() == result.lower()]
    if source:
        filtered = [e for e in filtered if e["source"].lower() == source.lower()]
    if user:
        filtered = [e for e in filtered if e["user"].lower() == user.lower()]

    # Collect unique values for filter dropdowns
    all_actions = sorted(set(e["action"] for e in all_events))
    all_devices = sorted(set(e["device_id"] for e in all_events))
    all_users = sorted(set(e["user"] for e in all_events))
    all_results = sorted(set(e["result"] for e in all_events))
    all_sources = sorted(set(e["source"] for e in all_events))

    total = len(filtered)
    pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    end = start + limit

    return {
        "events": filtered[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "filters": {
            "actions": all_actions,
            "devices": all_devices,
            "users": all_users,
            "results": all_results,
            "sources": all_sources,
        },
    }
