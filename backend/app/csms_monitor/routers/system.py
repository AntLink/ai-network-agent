from typing import Optional

import httpx
from fastapi import APIRouter

from app.csms_monitor.config import settings
from app.csms_monitor.ssh_client import ssh_client

router = APIRouter()

BRIDGE_URL = settings.CSMS_BRIDGE_URL.rstrip("/")


async def bridge_get(path: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BRIDGE_URL}{path}")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


@router.get("/info")
async def get_system_info():
    data = await bridge_get("/system")
    if data:
        return {
            "hostname": data.get("hostname", ""),
            "uptime_sec": data.get("uptime_sec", 0),
            "cpu_load_pct": data.get("cpu_load_pct", 0.0),
            "mem_total_mb": data.get("mem_total_mb", 0),
            "mem_free_mb": data.get("mem_free_mb", 0),
            "version": data.get("version", ""),
            "timestamp": data.get("timestamp", ""),
            "source": "bridge",
        }
    # Fallback to SSH if the bridge is unreachable
    info = await ssh_client.get_system_info()
    info["source"] = "ssh"
    return info


@router.get("/ntp")
async def get_ntp_status():
    data = await bridge_get("/ntp")
    return data or {"synced": False}


@router.get("/health")
async def get_bridge_health():
    data = await bridge_get("/health")
    return data or {"status": "unreachable"}


@router.get("/services")
async def get_services():
    # No bridge equivalent yet - still uses SSH
    services = await ssh_client.get_services()
    return services


@router.post("/csmsd/start")
async def start_csmsd():
    result = await ssh_client.start_csmsd()
    return {"status": result}


@router.post("/csmsd/stop")
async def stop_csmsd():
    result = await ssh_client.stop_csmsd()
    return {"status": result}


@router.get("/logs/{lines}")
async def get_logs(lines: int = 50):
    logs = await ssh_client.get_logs(lines)
    return {"logs": logs}
