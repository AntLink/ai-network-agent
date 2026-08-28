"""Config-change sub-agent for the AI Network Agent.

Turns a network-change request into a safe, approved configuration transaction:

    generate commands -> plan -> approval -> backup -> apply -> verify -> (rollback)

The actual device execution is delegated to the vendor driver's
`config_transaction`, which already performs pre-transaction backup, apply,
verification, save, and automatic rollback on failure.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Awaitable, Callable

from app.agent import approvals
from app.agent.event_bus import build_tool_output
from app.agent.state_machine import build_workflow_state_event
from app.services.device_service import device_service

APPROVAL_TIMEOUT_SECONDS = 600

LlmCall = Callable[[str, str], Awaitable[str]]

_VENDOR_LABELS = {
    "cisco": "Cisco IOS",
    "mikrotik": "MikroTik RouterOS",
    "aruba": "Aruba AOS-CX",
    "linux": "Linux",
    "other": "generic",
}


def _now() -> str:
    return datetime.utcnow().isoformat()


class ConfigChangeAgent:
    """Sub-agent that owns a single config change and its approval/apply flow."""

    def __init__(
        self,
        task: str,
        *,
        device_id: str,
        hostname: str,
        vendor: str,
        session_id: str | None,
        task_id: str,
        llm_call: LlmCall,
        require_approval: bool = True,
    ) -> None:
        self.task = task
        self.device_id = device_id
        self.hostname = hostname
        self.vendor = vendor
        self.session_id = session_id
        self.task_id = task_id
        self.llm_call = llm_call
        self.require_approval = require_approval

    def _vendor_label(self) -> str:
        return _VENDOR_LABELS.get(self.vendor, "generic")

    async def _generate_commands(self) -> list[str]:
        system = "You are a senior network configuration engineer."
        user = (
            f"Generate the exact configuration commands for a {self._vendor_label()} device "
            f"(hostname: {self.hostname}) to fulfill this request:\n\n{self.task}\n\n"
            f"Output ONLY a JSON array of strings. Use {self._vendor_label()} syntax. "
            "Do not add 'configure terminal' or 'end' wrappers. Do not add comments or explanation."
        )
        try:
            raw = await self.llm_call(system, user)
        except Exception:
            return []
        match = re.search(r"\[.*\]", raw or "", re.DOTALL)
        if not match:
            return []
        try:
            parsed = json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError):
            return []
        if not isinstance(parsed, list):
            return []
        return [str(x).strip() for x in parsed if str(x).strip()]

    def _plan_event(self, commands: list[str]) -> dict[str, Any]:
        return {
            "id": f"plan-{uuid.uuid4().hex[:10]}",
            "task": self.task,
            "devices": [self.hostname],
            "plannedActions": [
                "Generate configuration commands",
                "Backup current configuration",
                "Apply configuration",
                "Verify change",
                "Rollback on failure",
            ],
            "risk": "medium",
            "requiresApproval": self.require_approval,
            "createdAt": _now(),
        }

    async def _await_approval(self, approval_id: str) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
        deadline = time.monotonic() + APPROVAL_TIMEOUT_SECONDS
        last_heartbeat = 0.0
        while True:
            resolution = approvals.poll_approval(approval_id)
            if resolution is not None:
                yield (
                    "approval",
                    {
                        "id": f"{approval_id}-result",
                        "taskId": approval_id,
                        "task": self.task,
                        "devices": [self.hostname],
                        "risk": "medium",
                        "status": "approved" if resolution.get("status") == "approved" else "cancelled",
                        "message": f"Approval {resolution.get('status')}",
                        "createdAt": _now(),
                    },
                )
                return
            if time.monotonic() > deadline:
                yield (
                    "approval",
                    {
                        "id": f"{approval_id}-expired",
                        "taskId": approval_id,
                        "task": self.task,
                        "devices": [self.hostname],
                        "risk": "medium",
                        "status": "cancelled",
                        "message": "Approval expired.",
                        "createdAt": _now(),
                    },
                )
                return
            now = time.monotonic()
            if now - last_heartbeat >= 10:
                last_heartbeat = now
                yield (
                    "heartbeat",
                    {
                        "id": f"hb-{int(now)}",
                        "taskId": approval_id,
                        "message": "Menunggu approval. Klik 'Approve & Execute' pada kartu approval.",
                        "createdAt": _now(),
                    },
                )
            await asyncio.sleep(2)

    async def run(self) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
        yield (
            "task_progress",
            {
                "id": f"progress-{uuid.uuid4().hex[:8]}-gen",
                "taskId": self.task_id,
                "step": "Generate commands",
                "status": "running",
                "message": "Menyusun perintah konfigurasi vendor.",
                "order": 1,
                "total": 5,
                "createdAt": _now(),
            },
        )

        commands = await self._generate_commands()
        if not commands:
            yield (
                "verification",
                {
                    "id": f"verify-{uuid.uuid4().hex[:10]}",
                    "taskId": self.task_id,
                    "devices": [self.hostname],
                    "status": "failed",
                    "message": "Gagal menghasilkan perintah konfigurasi dari request.",
                    "checks": ["command_generation"],
                    "createdAt": _now(),
                },
            )
            yield (
                "text",
                {
                    "text": (
                        "Saya belum bisa menyusun perintah konfigurasi untuk request ini. "
                        f"Silakan sebutkan secara eksplisit perubahan yang diinginkan untuk {self.hostname} "
                        "(misalnya 'tambah vlan 10', 'set ip address ...'), atau gunakan halaman Konfigurasi."
                    )
                },
            )
            return

        yield ("plan", self._plan_event(commands))

        approval_id = ""
        if self.require_approval:
            approval_id, approval_event = approvals.create_approval(
                task_id=self.task_id,
                task=f"Terapkan konfigurasi ke {self.hostname}",
                commands=commands,
                risk="medium",
                message=f"Perubahan konfigurasi pada {self.hostname} membutuhkan approval.",
            )
            yield ("approval", approval_event)
            yield (
                "workflow_state",
                build_workflow_state_event(
                    task_id=self.task_id,
                    state="waiting_approval",
                    detail="Menunggu approval sebelum menerapkan konfigurasi.",
                    session_id=self.session_id,
                ),
            )

            resolution: dict[str, Any] = {}
            async for event_type, payload in self._await_approval(approval_id):
                if event_type == "approval":
                    resolution = payload
                    yield (event_type, payload)

            if resolution.get("status") != "approved":
                yield (
                    "text",
                    {"text": f"Perubahan dibatalkan (approval {resolution.get('status')}). Tidak ada konfigurasi yang diterapkan."},
                )
                return

        yield (
            "workflow_state",
            build_workflow_state_event(
                task_id=self.task_id,
                state="running",
                detail="Menerapkan konfigurasi dengan backup + verifikasi + rollback.",
                session_id=self.session_id,
            ),
        )
        yield (
            "task_progress",
            {
                "id": f"progress-{uuid.uuid4().hex[:8]}-apply",
                "taskId": self.task_id,
                "step": "Apply configuration",
                "status": "running",
                "message": "Backup, apply, dan verifikasi sedang berjalan.",
                "order": 3,
                "total": 5,
                "createdAt": _now(),
            },
        )

        try:
            driver = device_service.get_driver(self.device_id)
            report = await driver.config_transaction(
                commands=commands,
                verify=[],
                save_on_success=False,
                description=self.task,
            )
        except Exception as exc:  # noqa: BLE001
            yield (
                "tool_output",
                build_tool_output(
                    tool="config.apply",
                    policy="APPROVAL_REQUIRED",
                    evidence="live_command_output",
                    target={"device_id": self.device_id, "hostname": self.hostname},
                    summary=f"Config transaction failed: {exc}",
                    data={"commands": commands},
                    error=str(exc),
                ),
            )
            yield (
                "verification",
                {
                    "id": f"verify-{uuid.uuid4().hex[:10]}",
                    "taskId": self.task_id,
                    "devices": [self.hostname],
                    "status": "failed",
                    "message": f"Gagal menerapkan konfigurasi: {exc}",
                    "checks": ["config_transaction"],
                    "createdAt": _now(),
                },
            )
            yield ("text", {"text": f"Konfigurasi gagal diterapkan: {exc}"})
            return

        status = str(report.get("status", "")).lower()
        tool_event = build_tool_output(
            tool="config.apply",
            policy="APPROVAL_REQUIRED",
            evidence="live_command_output",
            target={"device_id": self.device_id, "hostname": self.hostname},
            summary=f"config_transaction status={status}",
            data={"commands": commands, "status": status, "steps": report.get("steps", []), "reason": report.get("reason")},
            error=None if status == "committed" else report.get("reason"),
        )
        tool_event["taskId"] = self.task_id
        yield ("tool_output", tool_event)

        if status == "committed":
            yield (
                "verification",
                {
                    "id": f"verify-{uuid.uuid4().hex[:10]}",
                    "taskId": self.task_id,
                    "devices": [self.hostname],
                    "status": "passed",
                    "message": "Konfigurasi berhasil diterapkan dan diverifikasi.",
                    "checks": ["backup", "apply", "verify"],
                    "createdAt": _now(),
                },
            )
            yield (
                "text",
                {
                    "text": (
                        f"Konfigurasi pada {self.hostname} berhasil diterapkan.\n\n"
                        f"Command yang dijalankan:\n```\n" + "\n".join(commands) + "\n```"
                    )
                },
            )
        elif status == "rolled_back":
            yield (
                "verification",
                {
                    "id": f"verify-{uuid.uuid4().hex[:10]}",
                    "taskId": self.task_id,
                    "devices": [self.hostname],
                    "status": "failed",
                    "message": "Konfigurasi gagal dan sudah di-rollback otomatis.",
                    "checks": ["backup", "apply", "rollback"],
                    "createdAt": _now(),
                },
            )
            yield (
                "text",
                {"text": f"Konfigurasi pada {self.hostname} gagal dan sudah di-rollback otomatis. Reason: {report.get('reason')}"},
            )
        else:
            yield (
                "verification",
                {
                    "id": f"verify-{uuid.uuid4().hex[:10]}",
                    "taskId": self.task_id,
                    "devices": [self.hostname],
                    "status": "failed",
                    "message": f"Konfigurasi gagal: {report.get('reason', 'unknown')}",
                    "checks": ["config_transaction"],
                    "createdAt": _now(),
                },
            )
            yield ("text", {"text": f"Konfigurasi gagal: {report.get('reason', 'unknown')}"})
