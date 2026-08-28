"""Network discovery endpoints."""
from datetime import datetime
from fastapi import APIRouter
from typing import Any

router = APIRouter()

_discovery_results: list = []


@router.get("")
async def list_discovery_results():
    return {"results": _discovery_results[-50:]}


@router.post("/scan")
async def start_scan(payload: dict):
    subnet = payload.get("subnet", "192.168.1.0/24")
    result = {
        "id": "scan-{:03d}".format(len(_discovery_results) % 1000),
        "subnet": subnet,
        "status": "completed",
        "devices_found": 0,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "devices": [],
    }
    _discovery_results.append(result)
    return result


@router.post("/add")
async def add_discovered_device(payload: dict):
    return {"status": "added", "device_id": payload.get("device_id", "")}
