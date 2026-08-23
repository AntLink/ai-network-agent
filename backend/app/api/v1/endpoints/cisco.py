from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.drivers.cisco.netmiko_driver import NetmikoCiscoDriver
from app.drivers.factory import get_driver
from app.repositories.inventory import inventory_repository
from app.schemas import cisco as schemas

router = APIRouter()


def _get_cisco_driver(device_id: str):
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if driver.__class__.__name__ != "CiscoDriver":
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a Cisco device")
    return driver


# ---------------------------------------------------------------------------
# Read-only: resource dumps
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/version")
async def get_version(device_id: str):
    return await _get_cisco_driver(device_id).get_facts()


@router.get("/{device_id}/resources/interfaces")
async def get_interfaces(device_id: str):
    return await _get_cisco_driver(device_id).get_interfaces()


@router.get("/{device_id}/resources/interfaces-detail")
async def get_interfaces_detail(device_id: str):
    return await _get_cisco_driver(device_id).get_interfaces_detail()


@router.get("/{device_id}/resources/routes")
async def get_routes(device_id: str):
    return await _get_cisco_driver(device_id).get_routes()


@router.get("/{device_id}/resources/arp")
async def get_arp(device_id: str):
    return await _get_cisco_driver(device_id).get_arp()


@router.get("/{device_id}/resources/cpu-memory")
async def get_cpu_memory(device_id: str):
    return await _get_cisco_driver(device_id).get_cpu_memory()


@router.get("/{device_id}/resources/acls")
async def get_acls(device_id: str):
    return await _get_cisco_driver(device_id).get_acls()


@router.get("/{device_id}/resources/cdp-neighbors")
async def get_cdp_neighbors(device_id: str):
    return await _get_cisco_driver(device_id).get_cdp_neighbors()


@router.get("/{device_id}/resources/nat-translations")
async def get_nat_translations(device_id: str):
    return await _get_cisco_driver(device_id).get_nat_translations()


@router.get("/{device_id}/resources/logs")
async def get_logs(device_id: str):
    return await _get_cisco_driver(device_id).get_logs()


# ---------------------------------------------------------------------------
# System configuration (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/system/hostname")
async def set_hostname(device_id: str, payload: dict):
    output = await _get_cisco_driver(device_id).set_hostname(payload["name"])
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/dns")
async def set_dns(device_id: str, payload: schemas.DnsSet):
    output = await _get_cisco_driver(device_id).set_dns(payload.servers)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/ntp")
async def add_ntp_server(device_id: str, payload: schemas.NtpServerAdd):
    output = await _get_cisco_driver(device_id).add_ntp_server(payload.server)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/system/ntp/{server}")
async def remove_ntp_server(device_id: str, server: str):
    output = await _get_cisco_driver(device_id).remove_ntp_server(server)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/banner")
async def set_banner(device_id: str, payload: schemas.BannerSet):
    output = await _get_cisco_driver(device_id).set_banner_motd(payload.text)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/users")
async def create_local_user(device_id: str, payload: schemas.LocalUserCreate):
    output = await _get_cisco_driver(device_id).create_local_user(
        payload.username, payload.password, payload.privilege
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/users/{username}")
async def delete_local_user(device_id: str, username: str):
    output = await _get_cisco_driver(device_id).delete_local_user(username)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Interface configuration (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/interface/description")
async def interface_description(device_id: str, payload: schemas.InterfaceDescriptionSet):
    try:
        output = await _get_cisco_driver(device_id).interface_set_description(
            payload.interface, payload.description
        )
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.post("/{device_id}/interface/address")
async def interface_address(device_id: str, payload: schemas.InterfaceAddressSet):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.interface_set_address(payload.interface, payload.address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/interface/{interface}/address")
async def interface_remove_address(device_id: str, interface: str):
    output = await _get_cisco_driver(device_id).interface_remove_address(interface)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/interface/mtu")
async def interface_mtu(device_id: str, payload: schemas.InterfaceMtuSet):
    output = await _get_cisco_driver(device_id).interface_set_mtu(payload.interface, payload.mtu)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/interface/{name}/{action}")
async def interface_state(device_id: str, name: str, action: str):
    if action not in ("shutdown", "no-shutdown"):
        raise HTTPException(status_code=400, detail="action must be shutdown|no-shutdown")
    output = await _get_cisco_driver(device_id).interface_set_state(name, action == "no-shutdown")
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Routing configuration (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: schemas.StaticRouteCreate):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.add_static_route(payload.prefix, payload.gateway, payload.distance)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/static-route")
async def remove_static_route(device_id: str, payload: schemas.StaticRouteDelete):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.remove_static_route(payload.prefix, payload.gateway)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# ACLs (write)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/acl")
async def create_acl(device_id: str, payload: schemas.AclCreate):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.acl_create(payload.name, payload.acl_type, payload.rules)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/acl")
async def delete_acl(device_id: str, payload: schemas.AclDelete):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.acl_delete(payload.name, payload.acl_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.post("/{device_id}/acl/apply")
async def apply_acl(device_id: str, payload: schemas.AclApply):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.acl_apply(payload.name, payload.interface, payload.direction)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


@router.post("/{device_id}/acl/unapply")
async def unapply_acl(device_id: str, payload: schemas.AclApply):
    driver = _get_cisco_driver(device_id)
    try:
        output = await driver.acl_unapply(payload.name, payload.interface, payload.direction)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Layer-2 (VLAN / access / trunk / subinterface / SVI)
# ---------------------------------------------------------------------------

@router.post("/{device_id}/l2/vlan")
async def create_vlan(device_id: str, payload: schemas.VlanCreate):
    output = await _get_cisco_driver(device_id).create_vlan(payload.vlan_id, payload.name)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/l2/vlan/{vlan_id}")
async def delete_vlan(device_id: str, vlan_id: int):
    output = await _get_cisco_driver(device_id).delete_vlan(vlan_id)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/l2/access")
async def set_access_port(device_id: str, payload: schemas.AccessPortSet):
    output = await _get_cisco_driver(device_id).set_access_port(payload.interface, payload.vlan_id)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/l2/trunk")
async def set_trunk_port(device_id: str, payload: schemas.TrunkPortSet):
    output = await _get_cisco_driver(device_id).set_trunk_port(payload.interface, payload.allowed_vlans)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/l2/subinterface")
async def create_subinterface(device_id: str, payload: schemas.SubinterfaceCreate):
    output = await _get_cisco_driver(device_id).create_subinterface(
        payload.parent_interface, payload.sub_id, payload.vlan_id, payload.ip_address
    )
    return {"status": "applied", "output": output}


@router.post("/{device_id}/l2/svi")
async def set_svi(device_id: str, payload: schemas.SviSet):
    output = await _get_cisco_driver(device_id).set_svi(payload.vlan_id, payload.ip_address, payload.shutdown)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Operations: raw commands, tools, config save/backup
# ---------------------------------------------------------------------------

@router.post("/{device_id}/commands/run")
async def run_commands(device_id: str, payload: schemas.CommandRunRequest):
    result = await _get_cisco_driver(device_id).apply(payload.commands)
    return {"status": "applied", **result}


@router.post("/{device_id}/tools/ping")
async def ping_tool(device_id: str, payload: schemas.PingRequest):
    output = await _get_cisco_driver(device_id).ping_tool(payload.address, payload.repeat, payload.timeout)
    return {"status": "ok", "output": output}


@router.post("/{device_id}/tools/traceroute")
async def traceroute_tool(device_id: str, payload: schemas.TracerouteRequest):
    output = await _get_cisco_driver(device_id).traceroute_tool(
        payload.address, payload.timeout, payload.probes
    )
    return {"status": "ok", "output": output}


@router.post("/{device_id}/config/save")
async def save_config(device_id: str):
    result = await _get_cisco_driver(device_id).save_config()
    return {"status": "saved" if result["saved"] else "failed", "output": result["output"]}


@router.post("/{device_id}/config/transaction")
async def config_transaction(device_id: str, payload: schemas.ConfigTransaction):
    """Transaksi konfigurasi: backup -> apply -> verify -> commit | rollback."""
    driver = _get_cisco_driver(device_id)

    # Backup lokal (berlapis dengan backup flash di dalam transaksi)
    raw = (await driver.backup()).get("raw", "")
    backup_dir = Path(settings.BACKUP_DIR).resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    local_file = backup_dir / f"{device_id}-pretxn-{ts}.cfg"
    local_file.write_text(raw, encoding="utf-8")

    report = await driver.config_transaction(
        commands=payload.commands,
        verify=[v.model_dump() for v in payload.verify],
        save_on_success=payload.save_on_success,
        description=payload.description or "",
    )
    report["local_backup"] = str(local_file)
    status_code = 200 if report.get("status") in ("committed",) else 200
    return JSONResponse(status_code=status_code, content=report)


@router.post("/{device_id}/config/backup")
async def backup_config(device_id: str):
    result = await _get_cisco_driver(device_id).backup()
    backup_dir = Path(settings.BACKUP_DIR).resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = backup_dir / f"{device_id}-backup-{ts}.cfg"
    path.write_text(result.get("raw", ""), encoding="utf-8")
    return {"status": "saved", "file": str(path), "size": path.stat().st_size}


# ---------------------------------------------------------------------------
# Netmiko-based config push (proper enable/config/save flow)
# ---------------------------------------------------------------------------

def _get_netmiko_driver(device_id: str) -> NetmikoCiscoDriver:
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if driver.__class__.__name__ != "CiscoDriver":
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a Cisco device")
    # Return Netmiko driver using same device info
    return NetmikoCiscoDriver(device)


@router.post("/{device_id}/config/push")
async def netmiko_config_push(device_id: str, payload: schemas.NetmikoConfigPush):
    """Push configuration using Netmiko with proper enable/config/save flow."""
    driver = _get_netmiko_driver(device_id)
    try:
        output = driver.run_config(payload.commands)
        if payload.save:
            save_out = driver.save_config()
            output += "\n--- SAVE ---\n" + save_out
        return {"status": "pushed", "output": output}
    except Exception as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    finally:
        driver.disconnect()


@router.post("/{device_id}/exec")
async def netmiko_exec(device_id: str, payload: schemas.CommandRunRequest):
    """Run exec commands via Netmiko (proper prompt handling)."""
    driver = _get_netmiko_driver(device_id)
    try:
        outputs = driver.run_batch(payload.commands)
        return {"status": "ok", "outputs": outputs}
    except Exception as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    finally:
        driver.disconnect()
