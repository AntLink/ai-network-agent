from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.device_service import device_service

router = APIRouter()


class ConsoleExecRequest(BaseModel):
    command: str


@router.get("")
async def list_devices():
    return await device_service.list_devices()


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
