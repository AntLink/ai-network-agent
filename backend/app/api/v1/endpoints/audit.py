from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

LOG_FILE = Path("C:/Users/mohfa/PycharmProjects/ai-network-agent/logs/audit.log")

@router.get("")
async def audit_events():
    if not LOG_FILE.exists():
        return {"events": []}
    lines = LOG_FILE.read_text(encoding="utf-8").strip().split("\n")
    events = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(" | ")
        events.append({
            "timestamp": parts[0].strip() if len(parts) > 0 else "",
            "device_id": parts[1].strip() if len(parts) > 1 else "",
            "action": parts[2].strip() if len(parts) > 2 else "",
            "command": parts[3].strip() if len(parts) > 3 else "",
            "user": parts[4].replace("user=", "").strip() if len(parts) > 4 else "",
        })
    return {"events": events[-50:]}
