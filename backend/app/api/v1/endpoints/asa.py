"""Cisco ASA / ASAv REST endpoints (feature parity with cisco.py).

ASAs speak ASA/IOS-Firewall syntax; writes are translated by the console
based AsaDriver. All write operations go through `write_response()` and the
shared `safety.direct_write_guard` dependency.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.drivers.cisco.asa import AsaDriver
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from .helpers import write_response
from .safety import direct_write_guard

router = APIRouter(dependencies=[Depends(direct_write_guard)])


class InterfaceAddress(BaseModel):
    interface: str
    address: str
    mask: Optional[str] = None


class StaticRouteCreate(BaseModel):
    prefix: str
    gateway: str
    distance: Optional[int] = None
    interface: str = "inside"


class StaticRouteDelete(BaseModel):
    prefix: str
    gateway: str
    interface: str = "inside"


class AclOp(BaseModel):
    name: str
    acl_type: str = "extended"
    rules: list[str] = []


class AclApplyOp(BaseModel):
    name: str
    interface: str
    direction: str = "in"


class NatCreate(BaseModel):
    real_ip: str
    mapped_ip: str
    interface: str = "outside"


class CommandRunRequest(BaseModel):
    command: str


def _get_asa_driver(device_id: str) -> AsaDriver:
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if not isinstance(driver, AsaDriver):
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a Cisco ASA device")
    return driver


# ---------------------------------------------------------------------------
# Read-only: resources
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/version")
async def get_version(device_id: str):
    return await _get_asa_driver(device_id).get_facts()


@router.get("/{device_id}/resources/interfaces")
async def get_interfaces(device_id: str):
    return await _get_asa_driver(device_id).get_interfaces()


@router.get("/{device_id}/resources/interfaces-detail")
async def get_interfaces_detail(device_id: str):
    return await _get_asa_driver(device_id).get_interfaces_detail()


@router.get("/{device_id}/resources/routes")
async def get_routes(device_id: str):
    return await _get_asa_driver(device_id).get_routes()


@router.get("/{device_id}/resources/acls")
async def get_acls(device_id: str):
    return await _get_asa_driver(device_id).get_acls()


@router.get("/{device_id}/resources/arp")
async def get_arp(device_id: str):
    return await _get_asa_driver(device_id).get_arp()


@router.get("/{device_id}/resources/cpu-memory")
async def get_cpu_memory(device_id: str):
    return await _get_asa_driver(device_id).get_cpu_memory()


@router.get("/{device_id}/resources/running-config")
async def get_running_config(device_id: str):
    return await _get_asa_driver(device_id).get_config()


# ---------------------------------------------------------------------------
# Interface (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/interface/address")
async def interface_address(device_id: str, payload: InterfaceAddress):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.set_interface_address(payload.interface, payload.address, payload.mask)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="set_interface_address")


# ---------------------------------------------------------------------------
# Routing (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: StaticRouteCreate):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.add_static_route(
            payload.prefix, payload.gateway, payload.distance, payload.interface
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="add_static_route")


@router.delete("/{device_id}/static-route")
async def remove_static_route(device_id: str, payload: StaticRouteDelete):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.remove_static_route(payload.prefix, payload.gateway, payload.interface)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="remove_static_route")


# ---------------------------------------------------------------------------
# ACL (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/acl")
async def create_acl(device_id: str, payload: AclOp):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.acl_create(payload.name, payload.acl_type, rules=payload.rules)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="acl_create")


@router.delete("/{device_id}/acl")
async def delete_acl(device_id: str, payload: AclOp):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.acl_delete(payload.name, payload.acl_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="acl_delete")


@router.post("/{device_id}/acl/apply")
async def apply_acl(device_id: str, payload: AclApplyOp):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.acl_apply(payload.name, payload.interface, payload.direction)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="acl_apply")


@router.post("/{device_id}/acl/unapply")
async def unapply_acl(device_id: str, payload: AclApplyOp):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.acl_unapply(payload.name, payload.interface, payload.direction)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="acl_unapply")


# ---------------------------------------------------------------------------
# NAT (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/nat")
async def add_nat(device_id: str, payload: NatCreate):
    driver = _get_asa_driver(device_id)
    try:
        output = await driver.add_nat(payload.real_ip, payload.mapped_ip, payload.interface)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="add_nat")


# ---------------------------------------------------------------------------
# Operations (exec / save)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/commands/run")
async def run_command(device_id: str, payload: CommandRunRequest):
    driver = _get_asa_driver(device_id)
    output = await driver.exec_logged(payload.command)
    return {"status": "ok", "command": payload.command, "output": output}


@router.post("/{device_id}/config/save")
async def save_config(device_id: str):
    output = await _get_asa_driver(device_id).save_config()
    return write_response(output, operation="save_config", default_status="saved")