"""Task execution tracking endpoints."""

import asyncio
import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

_tasks: list[dict[str, Any]] = []
_task_subscribers: list[asyncio.Queue] = []
_task_steps: dict[str, list[dict[str, Any]]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_tasks() -> None:
    if _tasks:
        return

    register_task(
        task_id="task-ospf-r1-r2",
        name="Configure OSPF",
        device="R1, R2",
        device_id="cisco-iosv-r1,cisco-iosv-r2",
        action="Configuration",
        status="success",
        started="2026-08-26T14:20:00+08:00",
        duration="18 sec",
        user="admin",
        agent="AI Agent",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T14:20:01+08:00", "output": "Intent parsed and device set resolved to R1, R2."},
            {"name": "Pre-check", "status": "success", "timestamp": "2026-08-26T14:20:04+08:00", "output": "SSH reachable, privilege 15 confirmed, interfaces are up."},
            {"name": "Backup", "status": "success", "timestamp": "2026-08-26T14:20:08+08:00", "output": "Running configuration backed up for both devices."},
            {"name": "Configuration", "status": "success", "timestamp": "2026-08-26T14:20:12+08:00", "output": "OSPF process and network statements applied."},
            {"name": "Validation", "status": "success", "timestamp": "2026-08-26T14:20:17+08:00", "output": "Neighbor state FULL, expected routes installed."},
            {"name": "Save", "status": "success", "timestamp": "2026-08-26T14:20:18+08:00", "output": "Configuration saved."},
        ],
    )
    register_task(
        task_id="task-backup-all",
        name="Backup all configs",
        device="All devices",
        device_id="all",
        action="Backup",
        status="running",
        started="2026-08-26T14:31:00+08:00",
        duration="42 sec",
        user="admin",
        agent="Scheduler",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T14:31:01+08:00", "output": "Inventory scan completed."},
            {"name": "Backup", "status": "running", "timestamp": "2026-08-26T14:31:10+08:00", "output": "Backing up device configurations in progress."},
        ],
    )
    register_task(
        task_id="task-check-mt",
        name="Check MikroTik internet reachability",
        device="MT-R1",
        device_id="mikrotik-chr-mt-r1",
        action="Validation",
        status="failed",
        started="2026-08-26T13:52:00+08:00",
        duration="11 sec",
        user="admin",
        agent="AI Agent",
        steps=[
            {"name": "Planning", "status": "success", "timestamp": "2026-08-26T13:52:01+08:00", "output": "Intent matched to MT-R1."},
            {"name": "Reachability", "status": "failed", "timestamp": "2026-08-26T13:52:07+08:00", "output": "Unable to reach upstream internet gateway.", "errors": "Gateway ping timeout."},
        ],
    )


def register_task(
    *,
    task_id: str | None = None,
    name: str,
    device: str,
    device_id: str,
    action: str,
    status: str,
    started: str,
    duration: str,
    user: str,
    agent: str,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    record = {
        "id": task_id or _make_task_id(),
        "name": name,
        "device": device,
        "device_id": device_id,
        "action": action,
        "status": status,
        "started": started,
        "duration": duration,
        "user": user,
        "agent": agent,
    }
    _tasks.insert(0, record)
    _task_steps[record["id"]] = [normalize_step(record["id"], step, index) for index, step in enumerate(steps or [])]
    return record


def create_task_record(**kwargs: Any) -> dict[str, Any]:
    return register_task(**kwargs)


def _make_task_id() -> str:
    return f"task-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


def normalize_step(task_id: str, step: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": str(step.get("id") or f"{task_id}-step-{index}"),
        "taskId": task_id,
        "name": str(step.get("name") or f"Step {index + 1}"),
        "status": str(step.get("status") or "queued"),
        "timestamp": str(step.get("timestamp") or now_iso()),
        "output": str(step.get("output") or ""),
        **({"errors": str(step["errors"])} if step.get("errors") else {}),
    }


def list_task_records() -> list[dict[str, Any]]:
    _seed_tasks()
    return deepcopy(_tasks)


def get_task_record(task_id: str) -> dict[str, Any] | None:
    _seed_tasks()
    for task in _tasks:
        if task.get("id") == task_id:
            return deepcopy(task)
    return None


def get_task_steps(task_id: str) -> list[dict[str, Any]]:
    _seed_tasks()
    return deepcopy(_task_steps.get(task_id, []))


def append_task_step(
    task_id: str,
    name: str,
    status: str,
    *,
    output: str = "",
    errors: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    step = {
        "id": f"{task_id}-step-{len(_task_steps.get(task_id, [])) + 1}",
        "taskId": task_id,
        "name": name,
        "status": status,
        "timestamp": timestamp or now_iso(),
        "output": output,
    }
    if errors:
        step["errors"] = errors

    _task_steps.setdefault(task_id, []).append(step)
    task = _find_task(task_id)
    if task is not None:
        task["steps"] = deepcopy(_task_steps[task_id])

    asyncio.create_task(_broadcast_task_event({"type": "task_progress", "taskId": task_id, "step": deepcopy(step)}))
    return deepcopy(step)


def update_task_record(task_id: str, **updates: Any) -> dict[str, Any] | None:
    task = _find_task(task_id)
    if task is None:
        return None
    task.update({k: v for k, v in updates.items() if k != "id"})
    if "steps" in task:
        _task_steps[task_id] = [normalize_step(task_id, step, index) for index, step in enumerate(task["steps"])]
    asyncio.create_task(_broadcast_task_event({"type": "task_updated", "task": deepcopy(task)}))
    return deepcopy(task)


def finalize_task_record(task_id: str, status: str, *, duration: str | None = None, output: str | None = None) -> dict[str, Any] | None:
    task = _find_task(task_id)
    if task is None:
        return None
    task["status"] = status
    if duration is not None:
        task["duration"] = duration
    if output is not None:
        task["output"] = output
    task["steps"] = deepcopy(_task_steps.get(task_id, []))
    asyncio.create_task(_broadcast_task_event({"type": "task_completed", "task": deepcopy(task)}))
    return deepcopy(task)


def _find_task(task_id: str) -> dict[str, Any] | None:
    _seed_tasks()
    for task in _tasks:
        if task.get("id") == task_id:
            return task
    return None


@router.get("")
async def list_tasks():
    return {"tasks": list_task_records()}


@router.get("/stream")
async def stream_task_updates():
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        _task_subscribers.append(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': now_iso()})}\n\n"
        finally:
            if queue in _task_subscribers:
                _task_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = get_task_record(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"task": task, "steps": get_task_steps(task_id)}


@router.post("")
async def create_task(payload: dict[str, Any]):
    task = register_task(
        name=str(payload.get("name", "Unnamed task")),
        device=str(payload.get("device", payload.get("device_id", "-"))),
        device_id=str(payload.get("device_id", payload.get("device", ""))),
        action=str(payload.get("action", "")),
        status=str(payload.get("status", "queued")),
        started=str(payload.get("started", now_iso())),
        duration=str(payload.get("duration", "-")),
        user=str(payload.get("user", "system")),
        agent=str(payload.get("agent", "manual")),
        steps=list(payload.get("steps", [])) if isinstance(payload.get("steps"), list) else [],
    )
    await _broadcast_task_event({"type": "task_created", "task": deepcopy(task)})
    return {"task": task, "steps": get_task_steps(task["id"])}


@router.patch("/{task_id}")
async def update_task(task_id: str, payload: dict[str, Any]):
    task = _find_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")

    if isinstance(payload.get("steps"), list):
        _task_steps[task_id] = [normalize_step(task_id, step, index) for index, step in enumerate(payload["steps"])]
        task["steps"] = deepcopy(_task_steps[task_id])

    task.update({k: v for k, v in payload.items() if k not in {"id", "steps"}})
    await _broadcast_task_event({"type": "task_updated", "task": deepcopy(task)})
    return {"task": deepcopy(task), "steps": get_task_steps(task_id)}


async def _broadcast_task_event(event: dict[str, Any]):
    for queue in list(_task_subscribers):
        try:
            await queue.put(event)
        except Exception:
            pass


_seed_tasks()
