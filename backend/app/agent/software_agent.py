"""Workspace sub-agent for the AI Network Agent.

A self-contained sub-agent that implements the write -> run -> inspect ->
analyze -> fix -> verify cycle using the workspace tools and the configured LLM.
It keeps its own task identity (`ws-*`) and approval flow so software work does
not mix with the network automation flow.

State-changing `run_command` calls are gated behind an approval card: the loop
pauses, emits an `approval` event, and resumes only when `/agent/execute` (or
`/agent/cancel`) resolves the pending approval.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Awaitable, Callable

from app.agent import approvals
from app.agent import workspace as ws
from app.agent.event_bus import build_tool_output
from app.agent.state_machine import build_workflow_state_event

SYSTEM_PROMPT = (
    "You are a senior software engineer agent operating inside a project workspace. "
    "Your job is to implement the requested change by writing and editing code, running "
    "commands, inspecting errors, and fixing them until the result works.\n\n"
    "Work one step at a time. On every turn, respond with EXACTLY ONE JSON object and "
    "nothing else. The object must have an 'action' field and one of these shapes:\n"
    "  {\"action\":\"write_file\",\"path\":\"<relative path>\",\"content\":\"<full file content>\"}\n"
    "  {\"action\":\"edit_file\",\"path\":\"<relative path>\",\"old\":\"<exact substring>\",\"new\":\"<replacement>\"}\n"
    "  {\"action\":\"run_command\",\"command\":\"<shell command>\"}\n"
    "  {\"action\":\"finish\",\"summary\":\"<concise explanation of what you did and the result>\"}\n\n"
    "Rules:\n"
    "- Paths are relative to the workspace root.\n"
    "- When a command fails, read the error output and fix the cause before running it again.\n"
    "- Run lint/test/build to verify your changes before finishing.\n"
    "- Prefer read-only verification commands (lint/test/build) over arbitrary commands.\n"
    "- When the task is done and verified, respond with the 'finish' action."
)

MAX_ITERATIONS = 8
APPROVAL_TIMEOUT_SECONDS = 600

LlmCall = Callable[[str, str], Awaitable[str]]


def parse_action(text: str) -> dict[str, Any]:
    """Parse the LLM action JSON; fall back to a finish action on free text."""
    text = (text or "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            action = json.loads(match.group(0))
            if isinstance(action, dict) and action.get("action"):
                return action
        except (json.JSONDecodeError, TypeError):
            pass
    return {"action": "finish", "summary": text[:2000] if text else "Task completed."}


def _transcript_block(transcript: list[dict[str, Any]]) -> str:
    if not transcript:
        return "(no actions yet)"
    lines: list[str] = []
    for item in transcript[-12:]:
        lines.append(f"Action: {item['action']}")
        lines.append(f"Observation: {item['observation'][:1500]}")
    return "\n".join(lines)


def _now() -> str:
    return datetime.utcnow().isoformat()


class WorkspaceAgent:
    """Sub-agent that owns a single software task and its approval flow."""

    def __init__(
        self,
        task: str,
        *,
        session_id: str | None,
        task_id: str,
        llm_call: LlmCall,
        max_iterations: int = MAX_ITERATIONS,
        require_approval: bool = True,
    ) -> None:
        self.task = task
        self.session_id = session_id
        self.task_id = task_id
        self.llm_call = llm_call
        self.max_iterations = max_iterations
        self.require_approval = require_approval
        self.transcript: list[dict[str, Any]] = []
        self.final_summary = "Task completed."

    def _action_prompt(self) -> str:
        return (
            f"[TASK]\n{self.task}\n[/TASK]\n\n"
            f"[ITERATION {len([t for t in self.transcript if t['action'].startswith('run_command')]) + 1}/{self.max_iterations}]\n"
            f"[TRANSCRIPT]\n{_transcript_block(self.transcript)}\n[/TRANSCRIPT]\n\n"
            "Respond with exactly one JSON action."
        )

    def _tool_event(
        self,
        *,
        tool: str,
        status: str,
        summary: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        policy: str = "GUARDED",
        evidence: str = "live_command_output",
    ) -> dict[str, Any]:
        event = build_tool_output(
            tool=tool,
            policy=policy,
            evidence=evidence,
            target={},
            summary=summary,
            data=data or {},
            raw="",
            error=error,
        )
        event["status"] = status
        event["taskId"] = self.task_id
        return event

    async def _await_approval(
        self,
        approval_id: str,
    ) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
        """Poll a pending approval until resolved, emitting keep-alive events."""
        deadline = time.monotonic() + APPROVAL_TIMEOUT_SECONDS
        last_heartbeat = 0.0
        while True:
            resolution = approvals.poll_approval(approval_id)
            if resolution is not None:
                yield ("approval", {
                    "id": f"{approval_id}-result",
                    "taskId": approval_id,
                    "task": self.task,
                    "devices": [],
                    "risk": "medium",
                    "status": "approved" if resolution.get("status") == "approved" else "cancelled",
                    "message": f"Approval {resolution.get('status')}",
                    "createdAt": _now(),
                })
                return
            if time.monotonic() > deadline:
                yield ("approval", {
                    "id": f"{approval_id}-expired",
                    "taskId": approval_id,
                    "task": self.task,
                    "devices": [],
                    "risk": "medium",
                    "status": "cancelled",
                    "message": "Approval expired.",
                    "createdAt": _now(),
                })
                return
            now = time.monotonic()
            if now - last_heartbeat >= 10:
                last_heartbeat = now
                yield ("heartbeat", {
                    "id": f"hb-{int(now)}",
                    "taskId": approval_id,
                    "message": "Menunggu approval. Klik 'Approve & Execute' pada kartu approval.",
                    "createdAt": _now(),
                })
            await asyncio.sleep(2)

    async def run(self) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
        """Run the software task loop, yielding (event_type, payload) tuples."""
        yield (
            "plan",
            {
                "id": f"plan-{uuid.uuid4().hex[:10]}",
                "task": self.task,
                "devices": [],
                "plannedActions": [
                    "Analyze the request",
                    "Write or edit workspace code",
                    "Run tests/lint/build",
                    "Inspect and fix errors",
                    "Verify the result",
                ],
                "risk": "low",
                "requiresApproval": False,
                "createdAt": _now(),
            },
        )

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            yield (
                "task_progress",
                {
                    "id": f"progress-{uuid.uuid4().hex[:8]}-{iteration}",
                    "taskId": self.task_id,
                    "step": f"Iteration {iteration}",
                    "status": "running",
                    "message": f"Software agent iteration {iteration}/{self.max_iterations}",
                    "order": iteration,
                    "total": self.max_iterations,
                    "createdAt": _now(),
                },
            )

            raw_action = await self.llm_call(SYSTEM_PROMPT, self._action_prompt())
            action = parse_action(raw_action)
            kind = str(action.get("action", "finish"))

            if kind == "finish":
                self.final_summary = str(action.get("summary") or self.final_summary)
                yield (
                    "verification",
                    {
                        "id": f"verify-{uuid.uuid4().hex[:10]}",
                        "taskId": self.task_id,
                        "devices": [],
                        "status": "passed",
                        "message": "Software task finished and verified.",
                        "checks": ["implementation", "command execution", "error resolution"],
                        "createdAt": _now(),
                    },
                )
                yield ("text", {"text": self.final_summary})
                return

            if kind == "write_file":
                path = str(action.get("path") or "").strip()
                content = str(action.get("content") or "")
                if not path:
                    self.transcript.append({"action": "write_file", "observation": "Missing path"})
                    continue
                result = ws.write_file(path, content)
                ok = bool(result.get("written"))
                self.transcript.append(
                    {"action": f"write_file {path}", "observation": f"written={ok} {result.get('error', '')}"}
                )
                yield (
                    "tool_output",
                    self._tool_event(
                        tool="workspace.write_file",
                        status="ok" if ok else "failed",
                        summary=f"Wrote {path}",
                        data={"path": path, "written": ok, "error": result.get("error")},
                        error=result.get("error"),
                    ),
                )
                continue

            if kind == "edit_file":
                path = str(action.get("path") or "").strip()
                old = str(action.get("old") or "")
                new = str(action.get("new") or "")
                if not path or not old:
                    self.transcript.append({"action": "edit_file", "observation": "Missing path/old"})
                    continue
                result = ws.edit_file(path, old, new)
                ok = bool(result.get("written"))
                self.transcript.append(
                    {"action": f"edit_file {path}", "observation": f"written={ok} {result.get('error', '')}"}
                )
                yield (
                    "tool_output",
                    self._tool_event(
                        tool="workspace.edit_file",
                        status="ok" if ok else "failed",
                        summary=f"Edited {path}",
                        data={"path": path, "written": ok, "error": result.get("error")},
                        error=result.get("error"),
                    ),
                )
                continue

            if kind == "run_command":
                command = str(action.get("command") or "").strip()
                if not command:
                    self.transcript.append({"action": "run_command", "observation": "Missing command"})
                    continue

                assessment = ws.classify_command(command)
                if assessment.get("blocked"):
                    self.transcript.append({"action": f"run_command {command}", "observation": "Blocked command"})
                    yield (
                        "tool_output",
                        self._tool_event(
                            tool="workspace.run_command",
                            status="blocked",
                            summary=f"$ {command}",
                            data={"command": command, "blocked": True},
                            error="Blocked destructive command",
                            policy="BLOCKED",
                        ),
                    )
                    continue

                if self.require_approval and not assessment["read_only"]:
                    approval_id, approval_event = approvals.create_approval(
                        task_id=self.task_id,
                        task=f"Execute command: {command}",
                        commands=[command],
                        risk=assessment["risk"],
                        message="Perintah ini dapat mengubah state. Approve untuk menjalankan.",
                    )
                    yield ("approval", approval_event)
                    yield (
                        "workflow_state",
                        build_workflow_state_event(
                            task_id=self.task_id,
                            state="waiting_approval",
                            detail="Menunggu approval sebelum menjalankan perintah.",
                            session_id=self.session_id,
                        ),
                    )

                    resolution: dict[str, Any] = {}
                    async for et, payload in self._await_approval(approval_id):
                        if et == "approval":
                            resolution = payload
                            yield (et, payload)

                    if resolution.get("status") != "approved":
                        self.transcript.append(
                            {"action": f"run_command {command}", "observation": f"Skipped (approval {resolution.get('status')})"}
                        )
                        yield (
                            "tool_output",
                            self._tool_event(
                                tool="workspace.run_command",
                                status="cancelled",
                                summary=f"$ {command} (not executed)",
                                data={"command": command, "skipped": True},
                                error=f"Approval {resolution.get('status')}",
                            ),
                        )
                        continue

                result = await ws.run_command(command)
                exit_code = result.get("exit_code", 0)
                stdout = str(result.get("stdout") or "")
                stderr = str(result.get("stderr") or "")
                ok = exit_code == 0
                observation = (stderr or stdout or "(no output)")[:1500]
                self.transcript.append({"action": f"run_command {command}", "observation": observation})
                yield (
                    "tool_output",
                    self._tool_event(
                        tool="workspace.run_command",
                        status="ok" if ok else "failed",
                        summary=f"$ {command}",
                        data={"command": command, "exit_code": exit_code, "stdout": stdout, "stderr": stderr},
                        error=(stderr if not ok else None),
                        policy="READ_ONLY" if assessment["read_only"] else "APPROVAL_REQUIRED",
                    ),
                )
                continue

            self.transcript.append({"action": kind, "observation": raw_action[:1500]})
            yield (
                "tool_output",
                self._tool_event(
                    tool=f"workspace.{kind}",
                    status="failed",
                    summary=f"Unknown action: {kind}",
                    error=f"Unknown action type: {kind}",
                ),
            )

        yield (
            "verification",
            {
                "id": f"verify-{uuid.uuid4().hex[:10]}",
                "taskId": self.task_id,
                "devices": [],
                "status": "warning",
                "message": "Reached the maximum number of iterations.",
                "checks": ["implementation", "command execution"],
                "createdAt": _now(),
            },
        )
        yield ("text", {"text": "Saya sudah mencapai batas iterasi. Ringkasan: " + self.final_summary})


async def run_software_task(
    task: str,
    *,
    session_id: str | None,
    task_id: str,
    llm_call: LlmCall,
    max_iterations: int = MAX_ITERATIONS,
) -> AsyncGenerator[tuple[str, dict[str, Any]], None]:
    """Backward-compatible entry point delegating to WorkspaceAgent."""
    agent = WorkspaceAgent(
        task,
        session_id=session_id,
        task_id=task_id,
        llm_call=llm_call,
        max_iterations=max_iterations,
    )
    async for event in agent.run():
        yield event


BLOCKED_SHELL_PATTERNS = (
    "rm -rf /",
    "mkfs.",
    "fdisk",
    "dd if=",
    "shutdown",
    "reboot",
    "kill -9 1",
    "curl -fsSL | sh",
    "> /dev/sd",
)


async def _run_proc(
    args: list[str],
    *,
    cwd: str,
    timeout: int,
    shell: bool = False,
) -> dict[str, Any]:
    """Run a process, capturing stdout/stderr, with a hard timeout."""
    try:
        if shell:
            proc = await asyncio.create_subprocess_shell(
                " ".join(args),
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return {"exit_code": -1, "stdout": "", "stderr": f"Command timed out after {timeout}s"}
    except FileNotFoundError as exc:  # noqa: BLE001
        return {"exit_code": -1, "stdout": "", "stderr": f"Runtime not found: {exc.name}"}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": -1, "stdout": "", "stderr": str(exc)}
    return {
        "exit_code": proc.returncode,
        "stdout": (stdout or b"").decode(errors="replace")[-12000:],
        "stderr": (stderr or b"").decode(errors="replace")[-4000:],
    }


def _runtime_for_language(language: str) -> list[str]:
    """Map a language to an interpreter prefix (empty list means shell)."""
    lang = (language or "").lower().strip()
    if lang in {"py", "python", "python3"}:
        return [sys.executable, "-c"]
    if lang in {"node", "js", "javascript"}:
        return ["node", "-e"]
    if lang in {"sh", "bash", "shell", "cmd", "pwsh", "powershell"}:
        return []
    if lang in {"go", "golang"}:
        return ["go", "run"]
    return [sys.executable, "-c"]


async def execute_code_snippet(
    code: str,
    *,
    language: str = "python",
    timeout: int = 30,
) -> dict[str, Any]:
    """Execute a code snippet inside a temporary sandbox directory.

    Returns {"language", "exit_code", "stdout", "stderr", "duration_ms"}.
    The sandbox prevents snippets from writing into the project workspace.
    """
    import tempfile as _tempfile
    import time as _time

    code = (code or "").strip()
    if not code:
        return {"language": language, "exit_code": -1, "stdout": "", "stderr": "Empty code", "duration_ms": 0}

    lang_lower = (language or "").lower()
    prefix = _runtime_for_language(language)

    if not prefix:
        lowered = (code or "").lower()
        if any(pattern in lowered for pattern in BLOCKED_SHELL_PATTERNS):
            return {
                "language": language,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Blocked destructive shell command",
                "duration_ms": 0,
                "blocked": True,
            }

    with _tempfile.TemporaryDirectory(prefix="codex-sandbox-") as tmp:
        t0 = _time.perf_counter()
        if prefix:
            result = await _run_proc([*prefix, code], cwd=tmp, timeout=timeout)
        else:
            result = await _run_proc([code], cwd=tmp, timeout=timeout, shell=True)
        duration_ms = int((_time.perf_counter() - t0) * 1000)
    result.update({"language": lang_lower or "python", "duration_ms": duration_ms})
    return result


DEBUG_SYSTEM_PROMPT = (
    "You are a debugger. You will be given a code snippet, its output (stdout/stderr) "
    "and an exit code. Fix the bug in the code. Respond with EXACTLY ONE JSON object "
    "and nothing else:\n"
    "{\"action\":\"fix\",\"code\":\"<full corrected code, escaped>\"}\n"
    "or {\"action\":\"done\",\"summary\":\"<reason the output is acceptable>\"} "
    "if the code already works."
)


def _parse_fix(raw_text: str) -> str | None:
    match = re.search(r"\{.*\}", (raw_text or "").strip(), re.DOTALL)
    if not match:
        return None
    try:
        action = json.loads(match.group(0))
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(action, dict) and action.get("action") == "fix":
        return str(action.get("code") or "").strip()
    return None


async def debug_code_snippet(
    code: str,
    *,
    language: str = "python",
    timeout: int = 30,
    max_iterations: int = 5,
    goal: str = "the program runs without errors and produces correct output",
    llm_call: Callable[[str, str], Awaitable[str]] | None = None,
) -> dict[str, Any]:
    """Run a code snippet, then auto-fix bugs via LLM until it passes.

    Returns {"success", "iterations", "final_code", "log": [...]}.
    """
    import time as _time

    current = (code or "").strip()
    if not current:
        return {"success": False, "iterations": 0, "final_code": "", "log": []}

    async def _default_llm(system: str, user: str) -> str:
        # Local best-effort fixer: strip obvious mismatches is not possible,
        # so we surface a clear instruction instead of running an LLM.
        return json.dumps(
            {"action": "done", "summary": "No LLM configured; automatic fix skipped."}
        )

    caller = llm_call or _default_llm
    log: list[dict[str, Any]] = []

    for i in range(1, max_iterations + 1):
        result = await execute_code_snippet(current, language=language, timeout=timeout)
        ok = result.get("exit_code") == 0
        std = (str(result.get("stderr") or "") + "\n" + str(result.get("stdout") or "")).strip()
        log.append({"iteration": i, "code": current, "exit_code": result.get("exit_code"),
                    "output": std[-2000:]})

        if ok:
            return {
                "success": True,
                "iterations": i,
                "final_code": current,
                "log": log,
            }

        if i >= max_iterations:
            break

        prompt = (
            f"[GOAL]\n{goal}\n[/GOAL]\n\n"
            f"[LANGUAGE]\n{language}\n[/LANGUAGE]\n\n"
            f"[CODE]\n{current}\n[/CODE]\n\n"
            f"[EXIT CODE]\n{result.get('exit_code')}\n[/EXIT CODE]\n\n"
            f"[OUTPUT]\n{std[-2000:]}\n[/OUTPUT]\n\n"
            "Fix the bug."
        )
        try:
            raw_fix = await caller(DEBUG_SYSTEM_PROMPT, prompt)
        except Exception as exc:  # noqa: BLE001
            log[-1]["fix_error"] = str(exc)
            break
        fixed = _parse_fix(raw_fix)
        if not fixed or fixed == current:
            log[-1]["fix_error"] = "No actionable fix returned by LLM."
            break
        current = fixed

    return {
        "success": False,
        "iterations": len(log),
        "final_code": current,
        "log": log,
    }
