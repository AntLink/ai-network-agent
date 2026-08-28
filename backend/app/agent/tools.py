"""Internal agent tools for Network Copilot.

These tools provide structured access to real device state (via the
existing backend service/driver layer) without exposing SSH credentials
or raw CLI primitives to the LLM.
"""
import json
import re
import uuid
from typing import Any

from app.drivers.factory import get_driver
from app.services.device_service import device_service
from app.repositories.inventory import inventory_repository


async def get_device(device_id: str) -> dict[str, Any]:
    """Get device facts and status."""
    try:
        device = await device_service.get_device(device_id)
        health = await device_service.health(device_id)
        reachable = health.get("reachable", True) if isinstance(health, dict) else True
        return {
            "id": device.get("id", device_id),
            "hostname": device.get("hostname", "unknown"),
            "vendor": device.get("vendor", "unknown"),
            "platform": device.get("platform", "unknown"),
            "management_address": device.get("management_address", "-"),
            "status": "online" if reachable else "offline",
        }
    except Exception as e:
        return {"error": str(e)}


async def get_interfaces(device_id: str) -> dict[str, Any]:
    """Get device interface status."""
    try:
        return await device_service.interfaces(device_id)
    except Exception as e:
        return {"error": str(e)}


async def get_routes(device_id: str) -> dict[str, Any]:
    """Get device routing table."""
    try:
        return await device_service.routes(device_id)
    except Exception as e:
        return {"error": str(e)}


async def get_running_config(device_id: str) -> dict[str, Any]:
    """Get device running configuration."""
    try:
        return await device_service.config(device_id)
    except Exception as e:
        return {"error": str(e)}


async def ping(device_id: str, target: str) -> dict[str, Any]:
    """Ping from device to target via the vendor driver."""
    try:
        device = inventory_repository.get_device(device_id)
        if not device:
            return {"error": f"Device {device_id} not found"}
        from app.drivers.factory import get_driver
        driver = get_driver(device)
        method = getattr(driver, "ping", None) or getattr(driver, "ping_tool", None)
        if method is None:
            return {"error": f"Driver for {device.get('vendor')} does not support ping"}
        return await method(target)
    except Exception as e:
        return {"error": str(e)}


async def traceroute(device_id: str, target: str) -> dict[str, Any]:
    """Traceroute from device to target via the vendor driver."""
    try:
        device = inventory_repository.get_device(device_id)
        if not device:
            return {"error": f"Device {device_id} not found"}
        from app.drivers.factory import get_driver
        driver = get_driver(device)
        if not hasattr(driver, "traceroute"):
            return {"error": f"Driver for {device.get('vendor')} does not support traceroute"}
        return await driver.traceroute(target)
    except Exception as e:
        return {"error": str(e)}


async def validate_config(device_id: str, commands: list[str]) -> dict[str, Any]:
    """Validate configuration commands without applying."""
    checks = []

    for cmd in commands:
        cmd_lower = cmd.lower().strip()

        if not cmd.strip():
            checks.append({"check": "syntax", "result": "warning", "detail": "Empty command"})
            continue

        destructive_keywords = ["delete", "remove", "reload", "shutdown", "factory"]
        is_destructive = any(kw in cmd_lower for kw in destructive_keywords)
        if is_destructive:
            checks.append({
                "check": "safety",
                "result": "warning",
                "detail": f"Potentially destructive: {cmd}",
            })

        if cmd_lower.startswith("interface ") or cmd_lower.startswith("router "):
            checks.append({
                "check": "scope",
                "result": "safe",
                "detail": f"Config mode: {cmd}",
            })
        else:
            checks.append({
                "check": "syntax",
                "result": "safe",
                "detail": f"Command accepted: {cmd}",
            })

    return {
        "device_id": device_id,
        "commands": commands,
        "checks": checks,
        "valid": all(c["result"] != "blocked" for c in checks),
    }


async def backup_config(device_id: str) -> dict[str, Any]:
    """Backup device configuration to a file and return a download link."""
    try:
        config = await get_running_config(device_id)
        if "error" in config:
            return config

        raw = str(config.get("raw", config.get("config", "")))
        from app.api.v1.endpoints.backups import save_backup
        meta = save_backup(device_id, raw, created_by="agent-backup_config")
        meta["config"] = raw
        return meta
    except Exception as e:
        return {"error": str(e)}


_PENDING_COMMAND_APPROVALS: dict[str, dict[str, Any]] = {}


def _looks_like_read_only_command(command: str) -> bool:
    normalized = command.strip().lower()
    if not normalized:
        return False

    read_only_prefixes = (
        "show ",
        "display ",
        "print ",
        "get ",
        "ping ",
        "traceroute ",
        "trace ",
        "write memory",
        "save config",
        "system resource print",
        "system identity print",
        "ip route print",
        "interface print",
        "ss ",
        "journalctl",
        "systemctl status",
        "ps ",
        "cat ",
        "free ",
        "df ",
        "uptime",
        "uname",
        "ip addr",
        "ip route",
    )
    if normalized.startswith(read_only_prefixes):
        return True
    if normalized.startswith("/"):
        return any(token in normalized for token in ("print", "show", "get", "probe", "ping", "traceroute"))
    return False


def classify_command_risk(command: str, vendor: str = "", mode: str = "auto") -> dict[str, Any]:
    """Classify a command before execution."""
    normalized = " ".join(command.strip().lower().split())
    vendor = (vendor or "unknown").lower()
    mode = (mode or "auto").lower()
    read_only = _looks_like_read_only_command(command)

    destructive_keywords = (
        "delete",
        "remove",
        "clear",
        "erase",
        "reload",
        "reboot",
        "shutdown",
        "power off",
        "format",
        "factory reset",
        "write erase",
        "format disk",
        "rm -rf",
        "kill ",
    )
    config_keywords = (
        "configure terminal",
        "conf t",
        "interface ",
        "router ",
        "vlan ",
        "ip address ",
        "ipv6 address ",
        "set ",
        "add ",
        "replace ",
        "system ",
        "restore",
        "commit",
        "save",
        "apply",
    )

    risk = "low"
    reason = "Read-only command"

    if read_only:
        risk = "low"
        reason = "Read-only inspection command"
    elif any(keyword in normalized for keyword in destructive_keywords):
        risk = "high"
        reason = "Potentially destructive command"
    elif any(keyword in normalized for keyword in config_keywords):
        risk = "medium"
        reason = "Configuration-changing command"
    elif mode == "exec":
        risk = "low"
        reason = "Explicit exec mode"

    approval_required = risk in {"medium", "high"}
    if vendor == "linux" and normalized.startswith(("ip ", "ss ", "journalctl", "systemctl restart", "systemctl stop")):
        risk = "medium" if not read_only else "low"
        approval_required = risk in {"medium", "high"}
        reason = "Linux operational command"
    if vendor == "mikrotik" and normalized.startswith(("/ip ", "/interface ", "/routing ", "/system ", "/ip firewall ")):
        if any(keyword in normalized for keyword in ("add ", "set ", "remove ", "disable ", "enable ", "reset ", "delete")):
            risk = "medium" if not any(keyword in normalized for keyword in destructive_keywords) else "high"
            approval_required = True
            reason = "RouterOS configuration command"
    if vendor == "cisco" and normalized.startswith(("configure terminal", "conf t", "interface ", "router ", "vlan ", "crypto ")):
        risk = "medium" if not any(keyword in normalized for keyword in destructive_keywords) else "high"
        approval_required = True
        reason = "Cisco configuration command"

    return {
        "vendor": vendor,
        "mode": mode,
        "read_only": read_only,
        "risk": risk,
        "approval_required": approval_required,
        "reason": reason,
        "normalized": normalized,
    }


async def _execute_vendor_command(
    device_id: str,
    command: str,
    *,
    mode: str = "auto",
    expected_vendor: str | None = None,
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    device = inventory_repository.get_device(device_id)
    if not device:
        return {"error": f"Device {device_id} not found"}

    vendor = (device.get("vendor") or "unknown").lower()
    if expected_vendor and vendor != expected_vendor:
        return {"error": f"Device {device_id} is vendor {vendor}, expected {expected_vendor}"}

    command = command.strip()
    if not command:
        return {"error": "Command is required"}

    assessment = classify_command_risk(command, vendor=vendor, mode=mode)
    approval_key = ""

    if assessment["approval_required"] and not approved:
        approval_key = uuid.uuid4().hex[:12]
        _PENDING_COMMAND_APPROVALS[approval_key] = {
            "device_id": device_id,
            "vendor": vendor,
            "command": command,
            "mode": mode,
            "risk": assessment["risk"],
            "reason": assessment["reason"],
            "approved": False,
            "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
        return {
            "device_id": device_id,
            "hostname": device.get("hostname", "unknown"),
            "vendor": vendor,
            "command": command,
            "mode": mode,
            "status": "approval_required",
            "approval_required": True,
            "approval_id": approval_key,
            "risk": assessment["risk"],
            "reason": assessment["reason"],
            "message": "Approval required before command execution",
        }

    if approved and approval_id:
        pending = _PENDING_COMMAND_APPROVALS.get(approval_id)
        if not pending:
            return {"error": f"Approval '{approval_id}' not found"}
        if pending.get("device_id") != device_id or pending.get("command") != command:
            return {"error": "Approval token does not match the requested command"}
        pending["approved"] = True
        pending["approved_by"] = approved_by or "system"
        pending["approved_at"] = __import__("datetime").datetime.utcnow().isoformat()

    transport = "driver"
    result: Any

    wants_exec = assessment["read_only"] and vendor == "cisco"
    if wants_exec and hasattr(device_service.get_driver(device_id), "exec_logged"):
        driver = device_service.get_driver(device_id)
        result = await driver.exec_logged(command)
        output = result
        raw = result
    else:
        driver = get_driver(device)
        if hasattr(driver, "apply"):
            result = await driver.apply([command])
            output = result.get("outputs", result)
            raw = output[0] if isinstance(output, list) and len(output) == 1 else json.dumps(result, default=str, ensure_ascii=False)
        else:
            result = await device_service.console_exec(device_id, command)
            transport = "console"
            output = result.get("output", result)
            raw = output if isinstance(output, str) else json.dumps(result, default=str, ensure_ascii=False)

    if approval_id and approval_id in _PENDING_COMMAND_APPROVALS:
        _PENDING_COMMAND_APPROVALS.pop(approval_id, None)

    return {
        "device_id": device_id,
        "hostname": device.get("hostname", "unknown"),
        "vendor": vendor,
        "command": command,
        "mode": "exec" if wants_exec else "apply",
        "transport": transport,
        "status": "ok",
        "risk": assessment["risk"],
        "approval_required": False,
        "approved_by": approved_by or None,
        "output": output,
        "raw": raw,
        "result": result,
    }


async def run_device_command(
    device_id: str,
    command: str,
    mode: str = "auto",
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    """Run a single command on a device via the backend driver layer.

    This keeps SSH credentials and transport handling in the backend while
    letting the agent execute MikroTik, Cisco, and Linux commands through a
    vendor-aware path.
    """
    try:
        return await _execute_vendor_command(
            device_id,
            command,
            mode=mode,
            approved=approved,
            approval_id=approval_id,
            approved_by=approved_by,
        )
    except Exception as e:
        return {"error": str(e)}


async def run_cisco_command(
    device_id: str,
    command: str,
    mode: str = "auto",
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    return await _execute_vendor_command(
        device_id,
        command,
        mode=mode,
        expected_vendor="cisco",
        approved=approved,
        approval_id=approval_id,
        approved_by=approved_by,
    )


async def run_mikrotik_command(
    device_id: str,
    command: str,
    mode: str = "auto",
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    return await _execute_vendor_command(
        device_id,
        command,
        mode=mode,
        expected_vendor="mikrotik",
        approved=approved,
        approval_id=approval_id,
        approved_by=approved_by,
    )


async def run_linux_command(
    device_id: str,
    command: str,
    mode: str = "auto",
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    return await _execute_vendor_command(
        device_id,
        command,
        mode=mode,
        expected_vendor="linux",
        approved=approved,
        approval_id=approval_id,
        approved_by=approved_by,
    )


# Tool registry for agent
AGENT_TOOLS = {
    "get_device": {
        "function": get_device,
        "description": "Get device facts and status",
        "parameters": {"device_id": {"type": "string", "required": True}},
    },
    "get_interfaces": {
        "function": get_interfaces,
        "description": "Get device interface status",
        "parameters": {"device_id": {"type": "string", "required": True}},
    },
    "get_routes": {
        "function": get_routes,
        "description": "Get device routing table",
        "parameters": {"device_id": {"type": "string", "required": True}},
    },
    "get_running_config": {
        "function": get_running_config,
        "description": "Get device running configuration",
        "parameters": {"device_id": {"type": "string", "required": True}},
    },
    "ping": {
        "function": ping,
        "description": "Ping from device to target",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "target": {"type": "string", "required": True},
        },
    },
    "traceroute": {
        "function": traceroute,
        "description": "Traceroute from device to target",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "target": {"type": "string", "required": True},
        },
    },
    "validate_config": {
        "function": validate_config,
        "description": "Validate configuration commands without applying",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "commands": {"type": "array", "required": True},
        },
    },
    "backup_config": {
        "function": backup_config,
        "description": "Backup device configuration",
        "parameters": {"device_id": {"type": "string", "required": True}},
    },
    "run_device_command": {
        "function": run_device_command,
        "description": "Run a single command on Cisco, MikroTik, or Linux through the backend driver layer",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "command": {"type": "string", "required": True},
            "mode": {"type": "string", "required": False},
            "approved": {"type": "boolean", "required": False},
            "approval_id": {"type": "string", "required": False},
            "approved_by": {"type": "string", "required": False},
        },
    },
    "run_cisco_command": {
        "function": run_cisco_command,
        "description": "Run a Cisco IOS/IOSv command through the backend driver layer",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "command": {"type": "string", "required": True},
            "mode": {"type": "string", "required": False},
            "approved": {"type": "boolean", "required": False},
            "approval_id": {"type": "string", "required": False},
            "approved_by": {"type": "string", "required": False},
        },
    },
    "run_mikrotik_command": {
        "function": run_mikrotik_command,
        "description": "Run a MikroTik RouterOS command through the backend driver layer",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "command": {"type": "string", "required": True},
            "mode": {"type": "string", "required": False},
            "approved": {"type": "boolean", "required": False},
            "approval_id": {"type": "string", "required": False},
            "approved_by": {"type": "string", "required": False},
        },
    },
    "run_linux_command": {
        "function": run_linux_command,
        "description": "Run a Linux command through the backend driver layer",
        "parameters": {
            "device_id": {"type": "string", "required": True},
            "command": {"type": "string", "required": True},
            "mode": {"type": "string", "required": False},
            "approved": {"type": "boolean", "required": False},
            "approval_id": {"type": "string", "required": False},
            "approved_by": {"type": "string", "required": False},
        },
    },
}


def get_tool_descriptions() -> list[dict[str, Any]]:
    """Return tool descriptions for LLM function calling."""
    return [
        {
            "name": name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        }
        for name, tool in AGENT_TOOLS.items()
    ]


async def execute_tool(tool_name: str, **kwargs) -> dict[str, Any]:
    """Execute an agent tool by name."""
    tool = AGENT_TOOLS.get(tool_name)
    if not tool:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return await tool["function"](**kwargs)
    except Exception as e:
        return {"error": f"Tool {tool_name} failed: {e}"}
