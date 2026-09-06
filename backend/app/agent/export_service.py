"""Export service: collect device data and build downloadable documents."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from app.agent.export import render_document, FORMATTERS, Section
from app.services.device_service import device_service


def _pick(obj: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = obj.get(key)
        if value is not None and value != "":
            return str(value)
    return ""


def _rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("data", "items", "interfaces", "routes", "rows"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def _normalize_interfaces(value: Any) -> list[list[Any]]:
    columns = ["Interface", "IP Address", "Type", "Status", "Protocol"]
    rows: list[list[Any]] = []
    for item in _rows(value):
        rows.append(
            [
                _pick(item, "name", "interface", "ifname", "port"),
                _pick(item, "ip_address", "ip", "address", "ipaddress"),
                _pick(item, "type", "kind"),
                _pick(item, "status", "admin_status", "state", "admin"),
                _pick(item, "protocol", "oper_status", "link", "oper"),
            ]
        )
    return rows


def _normalize_routes(value: Any) -> list[list[Any]]:
    columns = ["Network", "Next Hop", "Interface", "Distance", "Metric"]
    rows: list[list[Any]] = []
    for item in _rows(value):
        rows.append(
            [
                _pick(item, "dst", "destination", "network", "prefix"),
                _pick(item, "gateway", "via", "next_hop", "gw", "nexthop"),
                _pick(item, "interface", "iface", "out_interface", "dev"),
                _pick(item, "metric", "distance", "admin_distance"),
                _pick(item, "metric", "cost"),
            ]
        )
    return rows


def _config_lines(value: Any) -> list[str]:
    if isinstance(value, dict):
        config = value.get("data") if isinstance(value.get("data"), list) else None
        if config:
            return [str(x) for x in config]
        raw = value.get("raw")
        if raw:
            return str(raw).splitlines()
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str):
        return value.splitlines()
    return []


async def _collect_device(device_id: str) -> dict[str, Any]:
    base = await device_service.get_device(device_id)
    reachable = False
    try:
        health = await asyncio.wait_for(device_service.health(device_id), timeout=6.0)
        reachable = bool(health.get("reachable", False)) if isinstance(health, dict) else False
    except Exception:
        health = {}
    facts = base or {}
    interfaces: Any = None
    routes: Any = None
    config: Any = None
    if reachable:
        collectors = {
            "interfaces": device_service.interfaces,
            "routes": device_service.routes,
            "config": device_service.config,
        }
        for attr, method in collectors.items():
            try:
                result = await asyncio.wait_for(method(device_id), timeout=12.0)
            except Exception:
                continue
            if attr == "interfaces":
                interfaces = result
            elif attr == "routes":
                routes = result
            else:
                config = result
    return {
        "device_id": device_id,
        "hostname": facts.get("hostname") or device_id,
        "vendor": facts.get("vendor") or "",
        "platform": facts.get("platform") or "",
        "reachable": reachable,
        "interfaces": interfaces,
        "routes": routes,
        "config": config,
    }


async def collect_devices(device_ids: list[str]) -> list[dict[str, Any]]:
    return list(await asyncio.gather(*[_collect_device(device_id) for device_id in device_ids]))


def build_export_document(
    devices: list[dict[str, Any]],
    *,
    kind: str = "all",
    fmt: str = "xlsx",
    title: str = "",
) -> tuple[str, bytes]:
    """Build an export document from collected device data."""
    fmt = fmt if fmt in FORMATTERS else "xlsx"
    title = title or "Network Device Report"
    sections: list[Section] = []

    for device in devices:
        hostname = str(device.get("hostname") or device.get("device_id"))
        heading = f"{hostname} ({device.get('device_id')})"

        facts = [
            ["Hostname", device.get("hostname", "-")],
            ["Vendor", device.get("vendor", "-")],
            ["Platform", device.get("platform", "-")],
            ["Reachable", "yes" if device.get("reachable") else "no"],
        ]
        sections.append((f"{heading} — Summary", ["Field", "Value"], facts))

        interfaces = device.get("interfaces")
        if kind in {"all", "interfaces"} and interfaces is not None:
            rows = _normalize_interfaces(interfaces)
            if rows:
                sections.append((f"{heading} — Interfaces", ["Interface", "IP Address", "Type", "Status", "Protocol"], rows))

        routes = device.get("routes")
        if kind in {"all", "routes"} and routes is not None:
            rows = _normalize_routes(routes)
            if rows:
                sections.append((f"{heading} — Routes", ["Network", "Next Hop", "Interface", "Distance", "Metric"], rows))

        config = device.get("config")
        if kind in {"all", "config"} and config is not None:
            lines = _config_lines(config)
            if lines:
                sections.append((f"{heading} — Running Config", [], [[line] for line in lines]))

    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"network-export-{stamp}.{fmt}"
    data = render_document(title, sections, fmt)
    return filename, data
