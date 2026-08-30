"""Fortinet FortiOS REST endpoints (feature parity with aruba.py/asa.py/ruijie.py).

FortiOS does not use `configure terminal`; writes enter config mode directly
(`config system interface`, `config system global`, ...). All writes go
through `write_response()` + the shared `safety.direct_write_guard`.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.drivers.fortinet.driver import FortiOSDriver
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from .helpers import write_response
from .safety import direct_write_guard

router = APIRouter(dependencies=[Depends(direct_write_guard)])


class InterfaceAddressSet(BaseModel):
    interface: str
    address: str


class InterfaceTarget(BaseModel):
    interface: str


class StaticRouteCreate(BaseModel):
    prefix: str
    gateway: str
    interface: str = "port1"


class CommandRunRequest(BaseModel):
    command: str


def _get_fortios_driver(device_id: str) -> FortiOSDriver:
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if not isinstance(driver, FortiOSDriver):
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a Fortinet FortiOS device")
    return driver


@router.get("/{device_id}/resources/version")
async def get_version(device_id: str):
    return await _get_fortios_driver(device_id).get_facts()


@router.get("/{device_id}/resources/interfaces")
async def get_interfaces(device_id: str):
    return await _get_fortios_driver(device_id).get_interfaces()


@router.get("/{device_id}/resources/routes")
async def get_routes(device_id: str):
    return await _get_fortios_driver(device_id).get_routes()


@router.get("/{device_id}/resources/running-config")
async def get_running_config(device_id: str):
    return await _get_fortios_driver(device_id).get_config()


@router.post("/{device_id}/commands/run")
async def run_command(device_id: str, payload: CommandRunRequest):
    output = await _get_fortios_driver(device_id).exec_logged(payload.command)
    return {"status": "ok", "command": payload.command, "output": output}


@router.post("/{device_id}/system/hostname")
async def set_hostname(device_id: str, payload: dict):
    output = await _get_fortios_driver(device_id).set_hostname(payload["name"])
    return write_response(output, operation="set_hostname")


@router.post("/{device_id}/interface/address")
async def interface_address(device_id: str, payload: InterfaceAddressSet):
    driver = _get_fortios_driver(device_id)
    try:
        output = await driver.set_interface_address(payload.interface, payload.address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="set_interface_address")


@router.delete("/{device_id}/interface/address")
async def interface_remove_address(device_id: str, payload: InterfaceTarget):
    driver = _get_fortios_driver(device_id)
    try:
        output = await driver.remove_interface_address(payload.interface)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="remove_interface_address")


@router.get("/{device_id}/resources/static-routes")
async def get_static_routes(device_id: str):
    return await _get_fortios_driver(device_id).get_static_routes()


@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: StaticRouteCreate):
    driver = _get_fortios_driver(device_id)
    try:
        output = await driver.add_static_route(payload.prefix, payload.gateway, payload.interface)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="add_static_route")


@router.delete("/{device_id}/static-route/{route_id}")
async def delete_static_route(device_id: str, route_id: str):
    driver = _get_fortios_driver(device_id)
    try:
        output = await driver.delete_static_route(int(route_id))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail="route_id must be an integer")
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return write_response(output, operation="delete_static_route")