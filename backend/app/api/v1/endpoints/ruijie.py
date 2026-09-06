"""Ruijie RGOS REST endpoints (feature parity with cisco.py/aruba.py).

All operations are translated to RGOS (IOS-like) CLI by RuijieDriver.
Write operations go through `write_response()` and the shared
`safety.direct_write_guard` dependency. RGOS interface names contain spaces
(e.g. "GigabitEthernet 0/1") so interface targets come in the JSON body.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.drivers.ruijie.driver import RuijieDriver
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from .helpers import write_response
from .safety import direct_write_guard

router = APIRouter(dependencies=[Depends(direct_write_guard)])


class InterfaceTarget(BaseModel):
    interface: str


class InterfaceAddressSet(BaseModel):
    interface: str
    address: str


class InterfaceStateSet(BaseModel):
    interface: str
    action: str


class StaticRouteCreate(BaseModel):
    prefix: str
    gateway: str
    distance: Optional[int] = None


class StaticRouteDelete(BaseModel):
    prefix: str
    gateway: str


class VlanCreate(BaseModel):
    vlan_id: int
    name: Optional[str] = None


class AccessPortSet(BaseModel):
    interface: str
    vlan_id: int


class TrunkPortSet(BaseModel):
    interface: str
    allowed_vlans: str = "all"


class CommandRunRequest(BaseModel):
    command: str


class PingRequest(BaseModel):
    address: str
    repeat: Optional[int] = 3
    timeout: Optional[int] = 2


class TracerouteRequest(BaseModel):
    address: str
    timeout: Optional[int] = 2
    probes: Optional[int] = 2


def _get_ruijie_driver(device_id: str) -> RuijieDriver:
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if not isinstance(driver, RuijieDriver):
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a Ruijie RGOS device")
    return driver


# ---------------------------------------------------------------------------
# Read-only: resources
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/version")
async def get_version(device_id: str):
    return await _get_ruijie_driver(device_id).get_facts()


@router.get("/{device_id}/resources/interfaces")
async def get_interfaces(device_id: str):
    return await _get_ruijie_driver(device_id).get_interfaces()


@router.get("/{device_id}/resources/interfaces-detail")
async def get_interfaces_detail(device_id: str):
    return await _get_ruijie_driver(device_id).get_interfaces_detail()


@router.get("/{device_id}/resources/routes")
async def get_routes(device_id: str):
    return await _get_ruijie_driver(device_id).get_routes()


@router.get("/{device_id}/resources/arp")
async def get_arp(device_id: str):
    return await _get_ruijie_driver(device_id).get_arp()


@router.get("/{device_id}/resources/vlans")
async def get_vlans(device_id: str):
    return await _get_ruijie_driver(device_id).get_vlans()


@router.get("/{device_id}/resources/running-config")
async def get_running_config(device_id: str):
    return await _get_ruijie_driver(device_id).get_config()


# ---------------------------------------------------------------------------
# System / interface (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/system/hostname")
async def set_hostname(device_id: str, payload: dict):
    output = await _get_ruijie_driver(device_id).set_hostname(payload["name"])
    return write_response(output, operation="set_hostname")


@router.post("/{device_id}/interface/address")
async def interface_address(device_id: str, payload: InterfaceAddressSet):
    driver = _get_ruijie_driver(device_id)
    try:
        output = await driver.interface_set_address(payload.interface, payload.address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="interface_set_address")


@router.delete("/{device_id}/interface/address")
async def interface_remove_address(device_id: str, payload: InterfaceTarget):
    driver = _get_ruijie_driver(device_id)
    try:
        output = await driver.interface_remove_address(payload.interface)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="interface_remove_address")


@router.post("/{device_id}/interface/state")
async def interface_state(device_id: str, payload: InterfaceStateSet):
    if payload.action not in ("shutdown", "no-shutdown"):
        raise HTTPException(status_code=400, detail="action must be shutdown|no-shutdown")
    output = await _get_ruijie_driver(device_id).interface_set_state(
        payload.interface, payload.action == "no-shutdown"
    )
    return write_response(output, operation="interface_set_state")


# ---------------------------------------------------------------------------
# Layer-2 (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/l2/vlan")
async def create_vlan(device_id: str, payload: VlanCreate):
    driver = _get_ruijie_driver(device_id)
    try:
        output = await driver.create_vlan(payload.vlan_id, payload.name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="create_vlan")


@router.delete("/{device_id}/l2/vlan/{vlan_id}")
async def delete_vlan(device_id: str, vlan_id: int):
    output = await _get_ruijie_driver(device_id).delete_vlan(vlan_id)
    return write_response(output, operation="delete_vlan")


@router.post("/{device_id}/l2/access")
async def set_access_port(device_id: str, payload: AccessPortSet):
    output = await _get_ruijie_driver(device_id).set_access_port(payload.interface, payload.vlan_id)
    return write_response(output, operation="set_access_port")


@router.post("/{device_id}/l2/trunk")
async def set_trunk_port(device_id: str, payload: TrunkPortSet):
    output = await _get_ruijie_driver(device_id).set_trunk_port(payload.interface, payload.allowed_vlans)
    return write_response(output, operation="set_trunk_port")


# ---------------------------------------------------------------------------
# Routing (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: StaticRouteCreate):
    driver = _get_ruijie_driver(device_id)
    try:
        output = await driver.add_static_route(payload.prefix, payload.gateway, payload.distance)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="add_static_route")


@router.delete("/{device_id}/static-route")
async def remove_static_route(device_id: str, payload: StaticRouteDelete):
    driver = _get_ruijie_driver(device_id)
    try:
        output = await driver.remove_static_route(payload.prefix, payload.gateway)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="remove_static_route")


# ---------------------------------------------------------------------------
# Operations (exec / tools / save)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/commands/run")
async def run_command(device_id: str, payload: CommandRunRequest):
    output = await _get_ruijie_driver(device_id).exec_logged(payload.command)
    return {"status": "ok", "command": payload.command, "output": output}


@router.post("/{device_id}/tools/ping")
async def ping_tool(device_id: str, payload: PingRequest):
    driver = _get_ruijie_driver(device_id)
    output = await driver.ping_tool(payload.address, payload.repeat, payload.timeout)
    return write_response(output, operation="ping_tool", default_status="ok")


@router.post("/{device_id}/tools/traceroute")
async def traceroute_tool(device_id: str, payload: TracerouteRequest):
    driver = _get_ruijie_driver(device_id)
    output = await driver.traceroute_tool(payload.address, payload.timeout, payload.probes)
    return write_response(output, operation="traceroute_tool", default_status="ok")


@router.post("/{device_id}/config/save")
async def save_config(device_id: str):
    output = await _get_ruijie_driver(device_id).save_config()
    return write_response(output, operation="save_config", default_status="saved")