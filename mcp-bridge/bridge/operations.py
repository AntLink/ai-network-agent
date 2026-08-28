"""MCP tool logic — maps each tool to the backend REST API.

Functions here are plain async functions (callable for tests) and are
registered as MCP tools by server.py.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from . import config
from .backend import backend, BackendError


def _ok(data: Any) -> dict:
    if isinstance(data, dict):
        return data
    return {"result": data}


# ---------------------------------------------------------------------------
# Inventory & status
# ---------------------------------------------------------------------------


async def net_list_devices() -> dict:
    """Daftar semua device di inventory beserta status dasarnya."""
    return _ok(await backend.get("/devices"))


async def net_add_device(
    device_id: str,
    hostname: str,
    management_address: str,
    vendor: str,
    platform: str,
    management_port: int | None = None,
    transport: str = "ssh",
    status: str = "active",
    device_type: str = "virtual",
    console_host: str | None = None,
    console_port: int | None = None,
    model: str | None = None,
    serial: str | None = None,
    lab: str | None = None,
    tags: list[str] | None = None,
    os_version: str | None = None,
    uptime: str | None = None,
    privilege_level: str | None = None,
) -> dict:
    """Tambahkan perangkat baru ke inventory.

    Contoh: device_id='mikrotik-gw1', hostname='GW1', vendor='mikrotik',
    platform='routeros', management_address='192.168.1.1'. vendor umum:
    mikrotik, cisco, linux. platform: routeros / ios / debian / ubuntu, dll.
    """
    body: dict = {
        "id": device_id.strip(),
        "hostname": hostname.strip(),
        "management_address": management_address.strip(),
        "vendor": vendor.strip().lower(),
        "platform": platform.strip().lower(),
    }
    if management_port is not None:
        body["management_port"] = int(management_port)
    if console_host:
        body["console_host"] = console_host
    if console_port is not None:
        body["console_port"] = int(console_port)
    if model:
        body["model"] = model
    if serial:
        body["serial"] = serial
    if lab:
        body["lab"] = lab
    if tags:
        body["tags"] = tags
    if os_version:
        body["os_version"] = os_version
    if uptime:
        body["uptime"] = uptime
    if privilege_level:
        body["privilege_level"] = privilege_level
    if transport:
        body["transport"] = transport
    if status:
        body["status"] = status
    if device_type:
        body["device_type"] = device_type
    return _ok(await backend.post("/devices", json=body))


async def net_update_device(
    device_id: str,
    hostname: str | None = None,
    management_address: str | None = None,
    vendor: str | None = None,
    platform: str | None = None,
    management_port: int | None = None,
    transport: str | None = None,
    status: str | None = None,
    model: str | None = None,
    lab: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Perbarui data sebuah device di inventory (PUT)."""
    body: dict = {"id": device_id.strip()}
    for key in (
        "hostname", "management_address", "vendor", "platform",
        "management_port", "transport", "status", "model", "lab", "tags",
    ):
        val = locals().get(key)
        if val is not None:
            body[key] = val
    return _ok(await backend.request("PUT", f"/devices/{device_id}", json=body))


async def net_delete_device(device_id: str) -> dict:
    """Hapus sebuah device dari inventory."""
    return _ok(await backend.request("DELETE", f"/devices/{device_id}"))


async def net_console_exec(device_id: str, command: str) -> dict:
    """Jalankan perintah via console/telnet (GNS3 serial) ke sebuah device.

    Cocok untuk perangkat yang tidak punya SSH: MikroTik CHR baru, VPCS/PC,
    atau saat SSH gagal. Backend memakai console_host/console_port dari
    inventory (transport=telnet/console).
    """
    return _ok(await backend.post(f"/devices/{device_id}/console/exec", json={"command": command}))


async def net_console_exec_node(
    project_id: str,
    node_id: str,
    command: str,
    username: str | None = None,
    password: str = "",
    enable: bool = False,
    bootstrap: bool = False,
    login_timeout: float = 45.0,
) -> dict:
    """Jalankan perintah ANTI-GAGAL untuk first-boot di node GNS3 apa pun.

    Port console di-resolve LANGSUNG dari GNS3 (tidak bergantung inventory),
    project dibuka otomatis. Param:
    - username: untuk device yang butuh login (mis. 'admin' utk CHR)
    - password: password login (kosong = coba kosong bila bootstrap/kosong
      diizinkan)
    - enable: True untuk Cisco IOS/ASAv (privilege exec)
    - bootstrap: True bila node masih first-boot (CHR: isi password default)
    Contoh: net_console_exec_node(proj, node, "show ver", username="admin", enable=True)
    """
    await _ensure_project_open(project_id)
    try:
        await net_gns3_start_node(project_id, node_id)  # best-effort: pastikan jalan
    except Exception:
        pass
    body: dict = {
        "command": command,
        "username": username,
        "password": password,
        "enable": enable,
        "allow_empty_password": bootstrap or not username,
        "bootstrap_password": "admin123" if bootstrap else None,
        "login_timeout": login_timeout,
    }
    return _ok(await backend.post(f"/gns3/projects/{project_id}/nodes/{node_id}/console-exec", json=body))


async def net_get_device(device_id: str) -> dict:
    """Detail sebuah device berdasarkan ID (vendor, platform, IP manajemen, dll)."""
    return _ok(await backend.get(f"/devices/{device_id}"))


async def net_get_device_health(device_id: str) -> dict:
    """Cek kesehatan/reachability sebuah device via SSH."""
    return _ok(await backend.get(f"/devices/{device_id}/health"))


async def net_get_facts(device_id: str) -> dict:
    """Fakta perangkat (hostname, versi OS, model, uptime) via driver vendor."""
    return _ok(await backend.get(f"/devices/{device_id}/facts"))


async def net_get_interfaces(device_id: str) -> dict:
    """Status semua interface pada sebuah device."""
    return _ok(await backend.get(f"/devices/{device_id}/interfaces"))


async def net_get_routes(device_id: str) -> dict:
    """Tabel routing sebuah device."""
    return _ok(await backend.get(f"/devices/{device_id}/routes"))


async def net_get_running_config(device_id: str) -> dict:
    """Ambil running-config sebuah device."""
    return _ok(await backend.get(f"/devices/{device_id}/config"))


async def net_get_vlans(device_id: str) -> dict:
    """Daftar VLAN pada device (jika didukung)."""
    return _ok(await backend.get(f"/devices/{device_id}/vlans"))


async def net_get_memory(device_id: str) -> dict:
    """Penggunaan memori device."""
    return _ok(await backend.get(f"/devices/{device_id}/memory"))


async def net_get_ntp(device_id: str) -> dict:
    """Konfigurasi NTP sebuah device."""
    return _ok(await backend.get(f"/devices/{device_id}/ntp"))


# ---------------------------------------------------------------------------
# Command execution (melalui agen copilot internal agar klasifikasi
# risiko & approval backend tetap berlaku)
# ---------------------------------------------------------------------------


async def _agent_tool(tool: str, **params) -> dict:
    return _ok(await backend.post("/agent/tools/execute", json={"tool": tool, **params}))


async def net_run_command(device_id: str, command: str, approved: bool = False) -> dict:
    """Jalankan satu perintah CLI pada device (Cisco/MikroTik/Linux).

    Backend mengklasifikasi risiko & meminta approval untuk perintah yang
    mengubah konfigurasi. Gunakan approved=True hanya jika sudah yakin.
    """
    return await _agent_tool("run_device_command", device_id=device_id, command=command, approved=approved)


async def net_validate_config(device_id: str, commands: list[str]) -> dict:
    """Validasi daftar perintah konfigurasi TANPA mengaplikasikannya."""
    return await _agent_tool("validate_config", device_id=device_id, commands=commands)


async def net_backup_config(device_id: str) -> dict:
    """Backup running-config sebuah device dan kembalikan isinya."""
    return await _agent_tool("backup_config", device_id=device_id)


async def net_agent_tools() -> dict:
    """Daftar semua tool internal yang dimiliki Network Copilot backend."""
    return _ok(await backend.get("/agent/tools"))


async def net_execute_agent_tool(
    tool: str,
    device_id: str | None = None,
    command: str | None = None,
    commands: list[str] | None = None,
    target: str | None = None,
    mode: str | None = None,
    approved: bool | None = None,
    approved_by: str | None = None,
) -> dict:
    """Eksekusi tool internal Network Copilot backend secara umum.

    Tool yang valid: get_device, get_interfaces, get_routes,
    get_running_config, ping, traceroute, validate_config, backup_config,
    run_device_command, run_cisco_command, run_mikrotik_command,
    run_linux_command.
    """
    params: dict = {}
    if device_id is not None:
        params["device_id"] = device_id
    if command is not None:
        params["command"] = command
    if commands is not None:
        params["commands"] = commands
    if target is not None:
        params["target"] = target
    if mode is not None:
        params["mode"] = mode
    if approved is not None:
        params["approved"] = approved
    if approved_by:
        params["approved_by"] = approved_by
    return await _agent_tool(tool, **params)


# ---------------------------------------------------------------------------
# Config workflow: plan -> apply -> rollback
# ---------------------------------------------------------------------------


async def net_config_plan(
    device_id: str,
    commands: list[str],
    description: str = "",
) -> dict:
    """Buat plan konfigurasi (belum dieksekusi). Ambil plan_id dari hasilnya."""
    return _ok(
        await backend.post(
            "/config/plan",
            json={
                "device_id": device_id,
                "commands": commands,
                "verify": [],
                "save_on_success": False,
                "description": description,
            },
        )
    )


async def net_config_apply(plan_id: str, approved_by: str | None = None) -> dict:
    """Eksekusi (apply) plan konfigurasi yang sudah dibuat & disetujui.

    Wajib menyertakan approved_by (identitas petugas persetujuan).
    Backend melakukan backup otomatis sebelum perubahan & verifikasi.
    """
    return _ok(
        await backend.post(
            "/config/apply",
            json={"plan_id": plan_id, "approved_by": approved_by or config.DEFAULT_APPROVED_BY},
        )
    )


async def net_config_rollback(device_id: str, plan_id: str | None = None) -> dict:
    """Rollback konfigurasi device (atau berdasarkan plan tertentu)."""
    body: dict[str, Any] = {"device_id": device_id}
    if plan_id:
        body["plan_id"] = plan_id
    return _ok(await backend.post("/config/rollback", json=body))


async def net_list_plans() -> dict:
    """Daftar semua plan konfigurasi yang pernah dibuat."""
    return _ok(await backend.get("/config/plans"))


async def net_get_plan(plan_id: str) -> dict:
    """Detail sebuah plan konfigurasi."""
    return _ok(await backend.get(f"/config/plans/{plan_id}"))


async def net_list_backups() -> dict:
    """Daftar backup terakhir yang tercatat."""
    return _ok(await backend.get("/backups"))


# ---------------------------------------------------------------------------
# Vendor-specific resource views (baca saja)
# ---------------------------------------------------------------------------

CISCO_RESOURCES = {
    "version": "resources/version",
    "interfaces": "resources/interfaces",
    "interfaces-detail": "resources/interfaces-detail",
    "routes": "resources/routes",
    "arp": "resources/arp",
    "cpu-memory": "resources/cpu-memory",
    "acls": "resources/acls",
    "cdp-neighbors": "resources/cdp-neighbors",
    "nat-translations": "resources/nat-translations",
    "logs": "resources/logs",
}

MIKROTIK_RESOURCES = {
    "interfaces": "resources/interfaces",
    "ip-addresses": "resources/ip-addresses",
    "pools": "resources/pools",
    "dhcp-servers": "resources/dhcp-servers",
    "dhcp-leases": "resources/dhcp-leases",
    "bridges": "resources/bridges",
    "bridge-ports": "resources/bridge-ports",
    "firewall-filter": "resources/firewall/filter",
    "firewall-nat": "resources/firewall/nat",
    "firewall-mangle": "resources/firewall/mangle",
    "address-lists": "resources/firewall/address-lists",
    "ospf": "resources/ospf",
    "bgp": "resources/bgp",
    "static-routes": "resources/static-routes",
    "ppp-secrets": "resources/ppp-secrets",
    "ppp-profiles": "resources/ppp-profiles",
    "wireless": "resources/wireless",
    "snmp": "resources/snmp",
    "users": "resources/users",
    "logging": "resources/logging",
    "log-messages": "resources/log/messages",
    "hotspot-active": "resources/hotspot/active",
    "hotspot-hosts": "resources/hotspot/hosts",
}


async def net_cisco_resources(device_id: str, resource: str) -> dict:
    """Ambil tampilan resource Cisco (baca saja).

    resource valid: version, interfaces, interfaces-detail, routes, arp,
    cpu-memory, acls, cdp-neighbors, nat-translations, logs.
    """
    suffix = CISCO_RESOURCES.get(resource)
    if not suffix:
        return {
            "error": f"Resource '{resource}' tidak dikenal",
            "valid": sorted(CISCO_RESOURCES),
        }
    return _ok(await backend.get(f"/cisco/{device_id}/{suffix}"))


async def net_mikrotik_resources(device_id: str, resource: str) -> dict:
    """Ambil tampilan resource MikroTik RouterOS (baca saja).

    resource valid: interfaces, ip-addresses, pools, dhcp-servers,
    dhcp-leases, bridges, bridge-ports, firewall-filter, firewall-nat,
    firewall-mangle, address-lists, ospf, bgp, static-routes, ppp-secrets,
    ppp-profiles, wireless, snmp, users, logging, log-messages,
    hotspot-active, hotspot-hosts.
    """
    suffix = MIKROTIK_RESOURCES.get(resource)
    if not suffix:
        return {
            "error": f"Resource '{resource}' tidak dikenal",
            "valid": sorted(MIKROTIK_RESOURCES),
        }
    return _ok(await backend.get(f"/mikrotik/{device_id}/{suffix}"))


# ---------------------------------------------------------------------------
# GNS3 (topologi virtual — project / node / link / template / snapshot)
# ---------------------------------------------------------------------------

DEFAULT_GNS3_CONTROLLER = "http://localhost:3080/v2"
DEFAULT_GNS3_USERNAME = "admin"


def _gns3_body(
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
    compute_url: str | None = None,
) -> dict:
    body: dict = {
        "controller_url": controller_url or DEFAULT_GNS3_CONTROLLER,
        "username": username or DEFAULT_GNS3_USERNAME,
        "password": password,
        "verify_ssl": False,
    }
    if compute_url:
        body["compute_url"] = compute_url
    return body


async def _gns3(method: str, path: str, body: dict | None = None) -> dict:
    if method == "GET":
        return _ok(await backend.get(path))
    if method == "DELETE":
        return _ok(await backend.request("DELETE", path, json=body or {}))
    return _ok(await backend.post(path, json=body or {}))


async def _ensure_project_open(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> None:
    """GNS3 hanya melayani operasi node/link pada project yang OPEN.

    Kalau project masih tertutup, GNS3 membalas 404 'not found'. Helper ini
    membuka project otomatis sebelum operasi create node/link berjalan.
    """
    info = await net_gns3_get_project(project_id, controller_url, username, password)
    if isinstance(info, dict) and info.get("status") != "opened":
        await net_gns3_open_project(project_id, controller_url, username, password)


async def net_gns3_local_config() -> dict:
    """Baca konfigurasi GNS3 controller lokal (dari gns3_server.ini)."""
    return _ok(await backend.get("/gns3/local-config"))


async def net_gns3_test_connection(
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
    compute_url: str | None = None,
) -> dict:
    """Uji koneksi ke GNS3 controller (default localhost:3080/v2)."""
    return await _gns3("POST", "/gns3/test-connection", _gns3_body(controller_url, username, password, compute_url))


async def net_gns3_list_projects(
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Daftar semua project/topology di GNS3."""
    return await _gns3("POST", "/gns3/projects", _gns3_body(controller_url, username, password))


async def net_gns3_get_project(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Detail sebuah project GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}", _gns3_body(controller_url, username, password))


async def net_gns3_create_project(
    name: str,
    path: str | None = None,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Buat project/topology GNS3 baru. Pakai ini sebagai langkah awal 'generate topology'."""
    body = _gns3_body(controller_url, username, password)
    body["name"] = name
    if path:
        body["path"] = path
    return await _gns3("POST", "/gns3/projects/create", body)


async def net_gns3_open_project(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Buka sebuah project GNS3 di GUI."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/open", _gns3_body(controller_url, username, password))


async def net_gns3_close_project(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Tutup sebuah project GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/close", _gns3_body(controller_url, username, password))


async def net_gns3_delete_project(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Hapus sebuah project/topologi GNS3 beserta isinya."""
    return await _gns3("DELETE", f"/gns3/projects/{project_id}", _gns3_body(controller_url, username, password))


async def net_gns3_list_nodes(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Daftar node di sebuah project GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/nodes", _gns3_body(controller_url, username, password))


async def net_gns3_get_node_console(
    project_id: str,
    node_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Dapatkan info konsol (host/port/type telnet) sebuah node GNS3.

    Berguna untuk membuka console perangkat (Cisco/MikroTik) via telnet,
    misal `telnet <host> <port>` di terminal.
    """
    await _ensure_project_open(project_id, controller_url, username, password)
    return await _gns3("GET", f"/gns3/projects/{project_id}/nodes/{node_id}/console")


async def net_gns3_create_node(
    project_id: str,
    template_name: str,
    node_name: str | None = None,
    x: int | None = None,
    y: int | None = None,
    adapters: int | None = None,
    ram: int | None = None,
    compute_id: str | None = None,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Tambah node berbasis template ke project GNS3.

    template_name dicocokkan ke template_id GNS3 otomatis (contoh:
    'Cisco Router IOSv15.6(2)T', 'MikroTik CHR 7.22.1', 'Switches IOSv 15.2(4.0.55)E').

    adapters/ram opsional untuk override jumlah port NIC dan RAM node.
    compute_id opsional untuk paksa node dibuat di compute tertentu (mis. 'vm'
    biar semua node satu compute sehingga link lintas-compute tidak bermasalah).
    """
    try:
        await _ensure_project_open(project_id, controller_url, username, password)
        templates = await net_gns3_list_templates()
        items = templates.get("result") if isinstance(templates, dict) else templates
        if not isinstance(items, list):
            items = []
        target = " ".join(template_name.strip().lower().split())
        tpl = None
        for t in items:
            if isinstance(t, dict) and " ".join((t.get("name") or "").strip().lower().split()) == target:
                tpl = t
                break
        if tpl is None:
            return {
                "error": f"Template '{template_name}' tidak ditemukan",
                "valid_templates": sorted((t.get("name") or "") for t in items if isinstance(t, dict) and t.get("name")),
            }
        node_def: dict = {
            "name": node_name or template_name,
            "node_type": tpl.get("template_type") or "qemu",
            "template_id": tpl["template_id"],
            "compute_id": compute_id or tpl.get("compute_id") or "local",
        }
        # QEMU: GNS3 tidak mewarisi properti template saat create node.
        # Salin eksplisit nilai dari template supaya node sesuai template
        # (ram, hda_disk_image, adapters, qemu_path, dsb).
        if (tpl.get("template_type") or "") == "qemu":
            node_def["properties"] = {}
            qemu_keys = (
                "qemu_path", "hda_disk_image", "hda_disk_interface",
                "hdb_disk_image", "hdb_disk_interface", "hdc_disk_image",
                "cdrom_image", "bios_image", "initrd", "kernel_image",
                "kernel_command_line", "ram", "cpus", "adapters",
                "adapter_type", "boot_priority", "options", "on_close",
                "process_priority", "console_type", "legacy_networking",
                "linked_clone", "uefi", "platform",
            )
            for key in qemu_keys:
                val = tpl.get(key)
                if val not in (None, ""):
                    node_def["properties"][key] = val
            if adapters is not None:
                node_def["properties"]["adapters"] = int(adapters)
            if ram is not None:
                node_def["properties"]["ram"] = int(ram)
        if x is not None:
            node_def["x"] = x
        if y is not None:
            node_def["y"] = y
        body = _gns3_body(controller_url, username, password)
        body["node_def"] = node_def
        return await _gns3("POST", f"/gns3/projects/{project_id}/nodes/create", body)
    except Exception as exc:
        return {"error": str(exc)}


async def net_gns3_start_node(
    project_id: str,
    node_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Start sebuah node GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/nodes/{node_id}/start", _gns3_body(controller_url, username, password))


async def net_gns3_stop_node(
    project_id: str,
    node_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Stop sebuah node GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/nodes/{node_id}/stop", _gns3_body(controller_url, username, password))


async def net_gns3_restart_node(
    project_id: str,
    node_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Restart sebuah node GNS3 (stop lalu start)."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/nodes/{node_id}/restart", _gns3_body(controller_url, username, password))


async def net_gns3_set_node_properties(
    project_id: str,
    node_id: str,
    properties: dict,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Ubah properties node GNS3 (mis. adapters, ram, qemu_path, hda_disk_image).

    Contoh properties: {"adapters": 4, "ram": 512}.
    """
    body = _gns3_body(controller_url, username, password)
    body["properties"] = properties
    return await _gns3("POST", f"/gns3/projects/{project_id}/nodes/{node_id}/properties", body)


async def net_gns3_delete_node(
    project_id: str,
    node_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Hapus sebuah node dari project GNS3."""
    return await _gns3("DELETE", f"/gns3/projects/{project_id}/nodes/{node_id}", _gns3_body(controller_url, username, password))


async def net_gns3_list_links(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Daftar link/kabel antar-node di project GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/links", _gns3_body(controller_url, username, password))


async def _port_hint(project_id: str, node_id: str, controller_url, username, password) -> str:
    """Ambil daftar port valid node untuk bantuan error (best effort)."""
    try:
        result = await net_gns3_list_nodes(project_id, controller_url, username, password)
    except Exception:
        return ""
    items = result.get("result") if isinstance(result, dict) else []
    if not isinstance(items, list):
        return ""
    for n in items:
        if isinstance(n, dict) and n.get("node_id") == node_id:
            ports = n.get("ports", []) or []
            if isinstance(ports, list) and ports:
                return ", ".join(
                    f"{p.get('adapter_number')}/{p.get('port_number')}"
                    for p in ports if isinstance(p, dict)
                )
            return "n/a"
    return "?"


async def net_gns3_create_link(
    project_id: str,
    node_a: str,
    port_a: int,
    node_b: str,
    port_b: int,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Hubungkan dua node (buat kabel Ethernet).

    node_a/node_b = node_id dari net_gns3_list_nodes.
    port_a/port_b = NOMOR INTERFACE (mis. 2 => Ethernet2). Untuk node QEMU,
    GNS3 memetakan interface ke (adapter_number=port, port_number=0).
    Validasi: untuk node dengan 8 NIC, interface valid 0..7.

    Retry otomatis (2x): project baru kadang belum siap dilayani GNS3.
    """
    await _ensure_project_open(project_id, controller_url, username, password)
    nodes = [
        {"node_id": node_a, "adapter_number": port_a, "port_number": 0},
        {"node_id": node_b, "adapter_number": port_b, "port_number": 0},
    ]
    body = _gns3_body(controller_url, username, password)
    body["nodes"] = nodes
    path = f"/gns3/projects/{project_id}/links/create"
    last: Exception | None = None
    for attempt in range(3):
        try:
            return await _gns3("POST", path, body)
        except BackendError as exc:
            last = exc
            if "not found" not in str(exc) and "Port" not in str(exc):
                raise
            await net_gns3_open_project(project_id, controller_url, username, password)
            await asyncio.sleep(1 + attempt * 2)
    if isinstance(last, BackendError):
        hint_a = await _port_hint(project_id, node_a, controller_url, username, password)
        hint_b = await _port_hint(project_id, node_b, controller_url, username, password)
        return {
            "error": str(last),
            "hint": f"node_a interface valid: [{hint_a}]; node_b interface valid: [{hint_b}]. "
                    "Pastikan port_a/port_b mengikuti indeks interface (adapters). "
                    "Cek net_gns3_list_nodes / net_gns3_list_links untuk port yang tersedia & bebas.",
        }
    raise last


async def net_gns3_delete_link(
    project_id: str,
    link_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Hapus sebuah kabel/link antar-node di project GNS3."""
    return await _gns3("DELETE", f"/gns3/projects/{project_id}/links/{link_id}", _gns3_body(controller_url, username, password))


async def net_gns3_list_templates() -> dict:
    """Daftar template appliance yang tersedia di GNS3 controller."""
    return await _gns3("GET", "/gns3/templates")


async def net_gns3_list_snapshots(
    project_id: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Daftar snapshot dari sebuah project GNS3."""
    return await _gns3("POST", f"/gns3/projects/{project_id}/snapshots", _gns3_body(controller_url, username, password))


async def net_gns3_create_snapshot(
    project_id: str,
    name: str,
    controller_url: str | None = None,
    username: str | None = None,
    password: str = "",
) -> dict:
    """Buat snapshot (checkpoint) project GNS3."""
    body = _gns3_body(controller_url, username, password)
    body["name"] = name
    return await _gns3("POST", f"/gns3/projects/{project_id}/snapshots/create", body)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def net_backend_health() -> dict:
    """Cek apakah backend FastAPI dapat dijangkau."""
    try:
        return await backend.health()
    except Exception as exc:
        return {"error": str(exc)}


def tool_summary() -> str:
    """Ringkasan tool untuk logging / debugging (tanpa data sensitive)."""
    names = [
        "net_list_devices",
        "net_add_device",
        "net_update_device",
        "net_delete_device",
        "net_console_exec",
        "net_console_exec_node",
        "net_get_device",
        "net_get_device_health",
        "net_get_facts",
        "net_get_interfaces",
        "net_get_routes",
        "net_get_running_config",
        "net_get_vlans",
        "net_get_memory",
        "net_get_ntp",
        "net_run_command",
        "net_validate_config",
        "net_backup_config",
        "net_agent_tools",
        "net_execute_agent_tool",
        "net_config_plan",
        "net_config_apply",
        "net_config_rollback",
        "net_list_plans",
        "net_get_plan",
        "net_list_backups",
        "net_cisco_resources",
        "net_mikrotik_resources",
        "net_gns3_local_config",
        "net_gns3_test_connection",
        "net_gns3_list_projects",
        "net_gns3_get_project",
        "net_gns3_create_project",
        "net_gns3_open_project",
        "net_gns3_close_project",
        "net_gns3_delete_project",
        "net_gns3_list_nodes",
        "net_gns3_get_node_console",
        "net_gns3_create_node",
        "net_gns3_start_node",
        "net_gns3_stop_node",
        "net_gns3_restart_node",
        "net_gns3_set_node_properties",
        "net_gns3_delete_node",
        "net_gns3_list_links",
        "net_gns3_create_link",
        "net_gns3_delete_link",
        "net_gns3_list_templates",
        "net_gns3_list_snapshots",
        "net_gns3_create_snapshot",
        "net_backend_health",
    ]
    return json.dumps({"mcp_server": "ai-network-agent", "tools": names})