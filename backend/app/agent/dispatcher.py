"""Tool dispatcher: maps tool_registry names to real backend execution.

The tool registry (`tool_registry.py`) describes tools by namespace
(`devices.interfaces`, `cisco.exec_readonly`, ...). This module is the single
place that turns a registry tool name + params into a real backend call and a
normalized `tool_output` payload, while enforcing the tool's declared policy.

Read-only tools execute directly. Approval-required tools return an
`approval_required` result unless an explicit approval is provided, in which
case they are routed through the existing vendor command/execution layer.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Awaitable, Callable

from app.agent import workspace as ws
from app.agent.risk import AgentPolicy
from app.agent.tool_registry import default_tool_registry
from app.services.device_service import device_service


def _result(
    *,
    tool: str,
    policy: str,
    evidence: str,
    target: dict[str, Any],
    status: str = "ok",
    data: Any = None,
    summary: str = "",
    raw: str = "",
    error: str | None = None,
    approval_id: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "tool": tool,
        "policy": policy,
        "evidence": evidence,
        "target": target,
        "summary": summary,
        "data": data if data is not None else {},
        "raw": raw,
        "error": error,
        "approval_id": approval_id,
    }


async def _devices_list() -> dict[str, Any]:
    devices = await device_service.list_devices()
    return {"devices": devices}


async def _devices_get(device_id: str) -> dict[str, Any]:
    return await device_service.get_device(device_id)


async def _devices_health(device_id: str) -> dict[str, Any]:
    return await device_service.health(device_id)


async def _devices_facts(device_id: str) -> dict[str, Any]:
    return await device_service.facts(device_id)


async def _devices_interfaces(device_id: str) -> dict[str, Any]:
    return await device_service.interfaces(device_id)


async def _devices_routes(device_id: str) -> dict[str, Any]:
    return await device_service.routes(device_id)


async def _devices_config(device_id: str) -> dict[str, Any]:
    return await device_service.config(device_id)


async def _exec_readonly(device_id: str, command: str, vendor: str | None = None) -> dict[str, Any]:
    from app.agent.tools import run_device_command, run_cisco_command, run_mikrotik_command, run_linux_command

    if vendor == "cisco":
        return await run_cisco_command(device_id, command)
    if vendor == "mikrotik":
        return await run_mikrotik_command(device_id, command)
    if vendor == "linux":
        return await run_linux_command(device_id, command)
    return await run_device_command(device_id, command)


async def _linux_service_status(device_id: str, service: str) -> dict[str, Any]:
    from app.agent.tools import run_linux_command

    return await run_linux_command(device_id, f"systemctl status {service} --no-pager")


async def _ws_list(path: str = "", depth: int = 2) -> dict[str, Any]:
    return await asyncio.to_thread(ws.list_files, path, depth)


async def _ws_search(pattern: str, path: str = "") -> dict[str, Any]:
    return await asyncio.to_thread(ws.search_code, pattern, path)


async def _ws_read(path: str, start: int = 1, limit: int = 400) -> dict[str, Any]:
    return await asyncio.to_thread(ws.read_file, path, start, limit)


async def _ws_write(path: str, content: str) -> dict[str, Any]:
    return await asyncio.to_thread(ws.write_file, path, content)


async def _ws_edit(path: str, old: str, new: str) -> dict[str, Any]:
    return await asyncio.to_thread(ws.edit_file, path, old, new)


async def _ws_task_tracker(task_id: str = "", items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return await asyncio.to_thread(ws.task_tracker, task_id, items)


async def _ws_think(reasoning: str = "") -> dict[str, Any]:
    return await asyncio.to_thread(ws.think, reasoning)


async def _ws_finish(summary: str = "") -> dict[str, Any]:
    return await asyncio.to_thread(ws.finish, summary)


# Registry tool name -> async callable(params dict) -> result dict
_DISPATCH_TABLE: dict[str, Callable[..., Awaitable[Any]]] = {
    "devices.list": lambda **p: _devices_list(),
    "devices.get": lambda device_id, **p: _devices_get(device_id),
    "devices.health": lambda device_id, **p: _devices_health(device_id),
    "devices.facts": lambda device_id, **p: _devices_facts(device_id),
    "devices.interfaces": lambda device_id, **p: _devices_interfaces(device_id),
    "devices.routes": lambda device_id, **p: _devices_routes(device_id),
    "devices.config": lambda device_id, **p: _devices_config(device_id),
    "cisco.exec_readonly": lambda device_id, command, **p: _exec_readonly(device_id, command, vendor="cisco"),
    "mikrotik.exec_readonly": lambda device_id, command, **p: _exec_readonly(device_id, command, vendor="mikrotik"),
    "aruba.exec_readonly": lambda device_id, command, **p: _exec_readonly(device_id, command, vendor=None),
    "linux.exec_readonly": lambda device_id, command, **p: _exec_readonly(device_id, command, vendor="linux"),
    "linux.service_status": lambda device_id, service, **p: _linux_service_status(device_id, service),
    "workspace.list_files": lambda path="", depth=2, **p: _ws_list(path, depth),
    "workspace.search_code": lambda pattern, path="", **p: _ws_search(pattern, path),
    "workspace.read_file": lambda path, start=1, limit=400, **p: _ws_read(path, start, limit),
    "workspace.write_file": lambda path, content, **p: _ws_write(path, content),
    "workspace.edit_file": lambda path, old, new, **p: _ws_edit(path, old, new),
    "workspace.run_command": lambda command, timeout=120, **p: ws.run_command(command, timeout),
    "workspace.run_tests": lambda **p: ws.run_tests(),
    "workspace.run_lint": lambda **p: ws.run_lint(),
    "workspace.run_build": lambda **p: ws.run_build(),
    "workspace.task_tracker": lambda task_id="", items=None, **p: _ws_task_tracker(task_id, items),
    "workspace.think": lambda reasoning="", **p: _ws_think(reasoning),
    "workspace.finish": lambda summary="", **p: _ws_finish(summary),
}

# Namespaced tools that are described in the registry but execute through their
# own dedicated endpoints (not through the agent dispatcher). Returned honestly
# so the agent can route the user to the right flow instead of faking success.
_EXTERNAL_TOOLS = {
    "devices.create",
    "devices.update",
    "devices.delete",
    "linux.restart_service",
    "cisco.deploy_config",
    "mikrotik.deploy_config",
    "aruba.deploy_config",
    "gns3.templates.list",
    "gns3.project.create",
    "gns3.node.create_from_template",
    "topology.generate_from_intent",
    "topology.save_snapshot",
    "containerlab.inspect",
    "containerlab.deploy",
}


def _normalize_params(descriptor_inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Pass through params keyed by the descriptor input schema names."""
    return {key: value for key, value in params.items() if value is not None}


async def dispatch_tool(
    tool_name: str,
    params: dict[str, Any] | None = None,
    *,
    approved: bool = False,
    approval_id: str = "",
    approved_by: str = "",
) -> dict[str, Any]:
    """Execute a registry tool by name and return a normalized tool_output."""
    params = params or {}
    registry = default_tool_registry()
    descriptor = registry.get(tool_name)
    if descriptor is None:
        return _result(
            tool=tool_name,
            policy="READ_ONLY",
            evidence="audit_record",
            target={},
            status="failed",
            error=f"Unknown tool: {tool_name}",
        )

    policy = descriptor.policy
    evidence = descriptor.evidence_type.value
    target = {"device_id": params.get("device_id")} if params.get("device_id") else {}

    if policy == AgentPolicy.BLOCKED:
        return _result(
            tool=tool_name,
            policy=policy.value,
            evidence=evidence,
            target=target,
            status="blocked",
            error="Tool is blocked by policy",
        )

    impl = _DISPATCH_TABLE.get(tool_name)
    if impl is None:
        if tool_name in _EXTERNAL_TOOLS:
            status = "approval_required" if policy == AgentPolicy.APPROVAL_REQUIRED else "not_implemented"
            return _result(
                tool=tool_name,
                policy=policy.value,
                evidence=evidence,
                target=target,
                status=status,
                summary=f"{tool_name} is handled by its dedicated endpoint, not the agent dispatcher",
            )
        return _result(
            tool=tool_name,
            policy=policy.value,
            evidence=evidence,
            target=target,
            status="not_implemented",
            error=f"No dispatcher implementation for {tool_name}",
        )

    if policy == AgentPolicy.APPROVAL_REQUIRED and not approved:
        pending_id = approval_id or uuid.uuid4().hex[:12]
        return _result(
            tool=tool_name,
            policy=policy.value,
            evidence=evidence,
            target=target,
            status="approval_required",
            summary="Approval required before execution",
            approval_id=pending_id,
        )

    try:
        payload = await impl(**_normalize_params(dict(descriptor.input_schema), params))
    except Exception as exc:  # noqa: BLE001
        return _result(
            tool=tool_name,
            policy=policy.value,
            evidence=evidence,
            target=target,
            status="failed",
            error=str(exc),
        )

    data = payload if isinstance(payload, dict) else {"result": payload}
    raw = ""
    if isinstance(data.get("data"), str):
        raw = data.get("data", "")
    elif data.get("raw") is not None:
        raw = str(data.get("raw", ""))

    status = "failed" if data.get("error") else "ok"
    return _result(
        tool=tool_name,
        policy=policy.value,
        evidence=evidence,
        target=target,
        status=status,
        data=data,
        summary=data.get("summary", ""),
        raw=raw,
        error=data.get("error"),
    )
