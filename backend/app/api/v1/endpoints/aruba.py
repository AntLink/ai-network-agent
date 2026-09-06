"""Aruba AOS-CX REST endpoints (feature parity with cisco.py).

All operations are translated to AOS-CX CLI by ArubaDriver. Write
operations go through `write_response()` and are gated by the shared
`safety.direct_write_guard` dependency.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.drivers.aruba.driver import ArubaDriver
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from app.schemas import aruba as schemas
from .helpers import write_response
from .safety import direct_write_guard

router = APIRouter(dependencies=[Depends(direct_write_guard)])


def _get_aruba_driver(device_id: str) -> ArubaDriver:
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if not isinstance(driver, ArubaDriver):
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not an Aruba AOS-CX device")
    return driver


# ---------------------------------------------------------------------------
# Read-only: resources
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/version")
async def get_version(device_id: str):
    return await _get_aruba_driver(device_id).get_facts()


@router.get("/{device_id}/resources/interfaces")
async def get_interfaces(device_id: str):
    return await _get_aruba_driver(device_id).get_interfaces()


@router.get("/{device_id}/resources/interfaces-detail")
async def get_interfaces_detail(device_id: str):
    return await _get_aruba_driver(device_id).get_interfaces_detail()


@router.get("/{device_id}/resources/routes")
async def get_routes(device_id: str):
    return await _get_aruba_driver(device_id).get_routes()


@router.get("/{device_id}/resources/arp")
async def get_arp(device_id: str):
    return await _get_aruba_driver(device_id).get_arp()


@router.get("/{device_id}/resources/vlans")
async def get_vlans(device_id: str):
    return await _get_aruba_driver(device_id).get_vlans()


@router.get("/{device_id}/resources/memory")
async def get_memory(device_id: str):
    return await _get_aruba_driver(device_id).get_memory()


@router.get("/{device_id}/resources/running-config")
async def get_running_config(device_id: str):
    return await _get_aruba_driver(device_id).get_config()


# ---------------------------------------------------------------------------
# System (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/system/hostname")
async def set_hostname(device_id: str, payload: dict):
    output = await _get_aruba_driver(device_id).set_hostname(payload["name"])
    return write_response(output, operation="set_hostname")


# ---------------------------------------------------------------------------
# Interface (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/interface/description")
async def interface_description(device_id: str, payload: schemas.InterfaceDescriptionSet):
    output = await _get_aruba_driver(device_id).interface_set_description(
        payload.interface, payload.description
    )
    return write_response(output, operation="interface_set_description")


@router.post("/{device_id}/interface/address")
async def interface_address(device_id: str, payload: schemas.InterfaceAddressSet):
    driver = _get_aruba_driver(device_id)
    try:
        output = await driver.interface_set_address(payload.interface, payload.address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="interface_set_address")


@router.delete("/{device_id}/interface/address")
async def interface_remove_address(device_id: str, payload: schemas.InterfaceTarget):
    output = await _get_aruba_driver(device_id).interface_remove_address(payload.interface)
    return write_response(output, operation="interface_remove_address")


@router.post("/{device_id}/interface/state")
async def interface_state(device_id: str, payload: schemas.InterfaceStateSet):
    if payload.action not in ("shutdown", "no-shutdown"):
        raise HTTPException(status_code=400, detail="action must be shutdown|no-shutdown")
    output = await _get_aruba_driver(device_id).interface_set_state(
        payload.interface, payload.action == "no-shutdown"
    )
    return write_response(output, operation="interface_set_state")


# ---------------------------------------------------------------------------
# Layer-2 (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/l2/vlan")
async def create_vlan(device_id: str, payload: schemas.VlanCreate):
    driver = _get_aruba_driver(device_id)
    try:
        output = await driver.create_vlan(payload.vlan_id, payload.name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="create_vlan")


@router.delete("/{device_id}/l2/vlan/{vlan_id}")
async def delete_vlan(device_id: str, vlan_id: int):
    output = await _get_aruba_driver(device_id).delete_vlan(vlan_id)
    return write_response(output, operation="delete_vlan")


@router.post("/{device_id}/l2/access")
async def set_access_port(device_id: str, payload: schemas.AccessPortSet):
    output = await _get_aruba_driver(device_id).set_access_port(payload.interface, payload.vlan_id)
    return write_response(output, operation="set_access_port")


@router.post("/{device_id}/l2/trunk")
async def set_trunk_port(device_id: str, payload: schemas.TrunkPortSet):
    output = await _get_aruba_driver(device_id).set_trunk_port(payload.interface, payload.allowed_vlans)
    return write_response(output, operation="set_trunk_port")


# ---------------------------------------------------------------------------
# Routing (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: schemas.StaticRouteCreate):
    driver = _get_aruba_driver(device_id)
    try:
        output = await driver.add_static_route(payload.prefix, payload.gateway, payload.distance)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="add_static_route")


@router.delete("/{device_id}/static-route")
async def remove_static_route(device_id: str, payload: schemas.StaticRouteDelete):
    driver = _get_aruba_driver(device_id)
    try:
        output = await driver.remove_static_route(payload.prefix, payload.gateway)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="remove_static_route")


# ---------------------------------------------------------------------------
# Operations (exec / tools / save)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/commands/run")
async def run_command(device_id: str, payload: schemas.CommandRunRequest):
    driver = _get_aruba_driver(device_id)
    if not hasattr(driver, "exec_logged"):
        raise HTTPException(status_code=400, detail="Driver does not expose exec_logged")
    output = await driver.exec_logged(payload.command)
    return {"status": "ok", "command": payload.command, "output": output}


@router.post("/{device_id}/tools/ping")
async def ping_tool(device_id: str, payload: schemas.PingRequest):
    driver = _get_aruba_driver(device_id)
    output = await driver.ping_tool(payload.address, payload.repeat, payload.timeout)
    return write_response(output, operation="ping_tool", default_status="ok")


@router.post("/{device_id}/tools/traceroute")
async def traceroute_tool(device_id: str, payload: schemas.TracerouteRequest):
    driver = _get_aruba_driver(device_id)
    output = await driver.traceroute_tool(payload.address, payload.timeout, payload.probes)
    return write_response(output, operation="traceroute_tool", default_status="ok")


@router.post("/{device_id}/config/save")
async def save_config(device_id: str):
    output = await _get_aruba_driver(device_id).save_config()
    return write_response(output, operation="save_config", default_status="saved")