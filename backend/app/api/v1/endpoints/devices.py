from fastapi import APIRouter, HTTPException, Query
from pydantic import Field
from pydantic import BaseModel
from typing import Any
import math
from app.services.device_service import device_service
from app.repositories.inventory import inventory_repository

router = APIRouter()


class ConsoleExecRequest(BaseModel):
    command: str


class DeviceCreateRequest(BaseModel):
    id: str
    hostname: str
    management_address: str
    management_port: int | None = None
    vendor: str
    platform: str
    transport: str = "ssh"
    status: str = "active"
    device_type: str = "virtual"
    console_host: str | None = None
    console_port: int | None = None
    model: str | None = None
    serial: str | None = None
    lab: str | None = None
    tags: list[str] = Field(default_factory=list)
    os_version: str | None = None
    uptime: str | None = None
    privilege_level: str | None = None


class DeviceUpdateRequest(BaseModel):
    id: str | None = None
    hostname: str | None = None
    management_address: str | None = None
    management_port: int | None = None
    vendor: str | None = None
    platform: str | None = None
    transport: str | None = None
    status: str | None = None
    device_type: str | None = None
    console_host: str | None = None
    console_port: int | None = None
    model: str | None = None
    serial: str | None = None
    lab: str | None = None
    tags: list[str] | None = None
    os_version: str | None = None
    uptime: str | None = None
    privilege_level: str | None = None


@router.get("")
async def list_devices(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=500),
):
    devices = await device_service.list_devices()
    if page is None:
        return devices
    page = max(1, int(page))
    limit = max(1, min(int(limit or 25), 500))
    start = (page - 1) * limit
    return {
        "devices": devices[start:start + limit],
        "total": len(devices),
        "page": page,
        "limit": limit,
        "pages": max(1, math.ceil(len(devices) / limit)),
    }


@router.post("")
async def create_device(payload: DeviceCreateRequest):
    device_id = payload.id.strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="Device id is required")
    if inventory_repository.get_device(device_id):
        raise HTTPException(status_code=409, detail=f"Device '{device_id}' already exists")

    device: dict[str, Any] = {
        "id": device_id,
        "hostname": payload.hostname.strip(),
        "management_address": payload.management_address.strip(),
        "vendor": payload.vendor.strip().lower(),
        "platform": payload.platform.strip().lower(),
        "transport": payload.transport.strip().lower() or "ssh",
        "status": payload.status.strip().lower() or "active",
        "device_type": payload.device_type.strip().lower() or "virtual",
        "tags": [tag.strip() for tag in payload.tags if tag.strip()] or [payload.vendor.strip().lower()],
    }
    if payload.console_host:
        device["console_host"] = payload.console_host.strip()
    if payload.console_port is not None:
        device["console_port"] = int(payload.console_port)
    if payload.management_port is not None:
        device["management_port"] = int(payload.management_port)
    if payload.model:
        device["model"] = payload.model.strip()
    if payload.serial:
        device["serial"] = payload.serial.strip()
    if payload.lab:
        device["lab"] = payload.lab.strip()
    if payload.os_version:
        device["os_version"] = payload.os_version.strip()
    if payload.uptime:
        device["uptime"] = payload.uptime.strip()
    if payload.privilege_level:
        device["privilege_level"] = payload.privilege_level.strip()

    created = inventory_repository.create_device(device)
    return created


@router.put("/{device_id}")
async def update_device(device_id: str, payload: DeviceUpdateRequest):
    current = inventory_repository.get_device(device_id)
    if not current:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    updated: dict[str, Any] = dict(current)
    if payload.id is not None:
        updated["id"] = payload.id.strip()
    if payload.hostname is not None:
        updated["hostname"] = payload.hostname.strip()
    if payload.management_address is not None:
        updated["management_address"] = payload.management_address.strip()
    if payload.vendor is not None:
        updated["vendor"] = payload.vendor.strip().lower()
    if payload.platform is not None:
        updated["platform"] = payload.platform.strip().lower()
    if payload.transport is not None:
        updated["transport"] = payload.transport.strip().lower()
    if payload.status is not None:
        updated["status"] = payload.status.strip().lower()
    if payload.device_type is not None:
        updated["device_type"] = payload.device_type.strip().lower()
    if payload.console_host is not None:
        updated["console_host"] = payload.console_host.strip()
    if payload.console_port is not None:
        updated["console_port"] = int(payload.console_port)
    if payload.management_port is not None:
        updated["management_port"] = int(payload.management_port)
    if payload.model is not None:
        updated["model"] = payload.model.strip()
    if payload.serial is not None:
        updated["serial"] = payload.serial.strip()
    if payload.lab is not None:
        updated["lab"] = payload.lab.strip()
    if payload.tags is not None:
        updated["tags"] = [tag.strip() for tag in payload.tags if tag.strip()]
    if payload.os_version is not None:
        updated["os_version"] = payload.os_version.strip()
    if payload.uptime is not None:
        updated["uptime"] = payload.uptime.strip()
    if payload.privilege_level is not None:
        updated["privilege_level"] = payload.privilege_level.strip()

    return inventory_repository.update_device(device_id, updated)


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    try:
        return inventory_repository.delete_device(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ⚠️ /batch-status HARUS sebelum /{device_id}
# agar tidak tertangkap oleh wildcard {device_id}
@router.get("/batch-status")
async def batch_device_status():
    """Status + CPU + Memory + Latency untuk semua device (satu panggilan)."""
    return await device_service.batch_status()


@router.get("/{device_id}")
async def get_device(device_id: str):
    try:
        return await device_service.get_device(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{device_id}/health")
async def get_device_health(device_id: str):
    try:
        return await device_service.health(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{device_id}/console/exec")
async def console_exec(device_id: str, payload: ConsoleExecRequest):
    """Run one command over telnet console (recovery path when SSH is down)."""
    try:
        return await device_service.console_exec(device_id, payload.command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"console failed: {e}")

@router.get("/{device_id}/identify")
async def identify_device(device_id: str):
    try:
        return await device_service.identify(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/facts")
async def get_facts(device_id: str):
    try:
        return await device_service.facts(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/interfaces")
async def get_interfaces(device_id: str):
    try:
        return await device_service.interfaces(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/routes")
async def get_routes(device_id: str):
    try:
        return await device_service.routes(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/config")
async def get_config(device_id: str):
    try:
        return await device_service.config(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/vlans")
async def get_vlans(device_id: str):
    try:
        return await device_service.vlans(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/services")
async def get_services(device_id: str):
    try:
        return await device_service.services(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/disk")
async def get_disk(device_id: str):
    try:
        return await device_service.disk(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/memory")
async def get_memory(device_id: str):
    try:
        return await device_service.memory(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{device_id}/ntp")
async def get_ntp(device_id: str):
    try:
        return await device_service.ntp(device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
