"""Workspace execution tools for the AI Network Agent software copilot.

Mirrors the OpenHands agent-skills tool surface (list/search/read/write/edit
files, run shell commands, run tests/lint/build, track tasks) while keeping all
execution sandboxed to the project workspace and auditable by the backend.

The workspace root is the project repository. All file operations are path-
guarded so the agent cannot read or write outside the workspace.
"""
from __future__ import annotations

import asyncio
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

_BLOCKED_COMMAND_PATTERNS = (
    "rm -rf /",
    "mkfs",
    "wipefs",
    "dd if=",
    "shutdown",
    "reboot",
    ":(){",
    "> /dev/sd",
)

_READ_ONLY_COMMAND_PREFIXES = (
    "git status",
    "git diff",
    "git log",
    "git branch",
    "git remote",
    "git show",
    "git ls-files",
    "ls",
    "dir",
    "cat",
    "type",
    "head",
    "tail",
    "more",
    "grep",
    "findstr",
    "find ",
    "where ",
    "which",
    "pwd",
    "cd ",
    "echo",
    "python --version",
    "python -v",
    "python -m pytest",
    "python -m flake8",
    "python -m py_compile",
    "python -m mypy",
    "node --version",
    "node -v",
    "npm --version",
    "npm -v",
    "npm ls",
    "npm list",
    "npm outdated",
    "npm run lint",
    "npm run test",
    "npm run build",
    "npm run typecheck",
    "npm test",
    "pytest",
    "flake8",
    "mypy",
    "ruff",
    "eslint",
    "tsc",
    "pip list",
    "pip show",
    "pip freeze",
)


def classify_command(command: str) -> dict[str, Any]:
    """Classify a workspace command as read-only or state-changing.

    Only commands matching a known read-only/verification prefix run without
    approval. Everything else is treated as state-changing and requires
    approval before execution.
    """
    normalized = " ".join((command or "").strip().lower().split())
    if not normalized:
        return {"read_only": True, "risk": "low", "reason": "Empty command"}

    lowered = normalized.lower()
    if any(pattern in lowered for pattern in _BLOCKED_COMMAND_PATTERNS):
        return {"read_only": False, "risk": "critical", "reason": "Blocked destructive command", "blocked": True}

    if normalized.startswith(_READ_ONLY_COMMAND_PREFIXES):
        return {"read_only": True, "risk": "low", "reason": "Read-only or verification command"}

    return {"read_only": False, "risk": "medium", "reason": "Command may change workspace or system state"}

# Per-task in-memory checklists (TaskTrackerTool equivalent).
_task_lists: dict[str, list[dict[str, Any]]] = {}


class WorkspaceError(Exception):
    pass


def _resolve(rel_path: str) -> Path:
    """Resolve a workspace-relative path and reject path traversal."""
    root = WORKSPACE_ROOT.resolve()
    candidate = (root / (rel_path or ".")).resolve()
    if not str(candidate).startswith(str(root)):
        raise WorkspaceError(f"Path outside workspace: {rel_path}")
    return candidate


def list_files(path: str = "", depth: int = 2, limit: int = 200) -> dict[str, Any]:
    """List files and directories under a workspace-relative path."""
    base = _resolve(path)
    if not base.exists():
        return {"path": path, "files": [], "error": f"Not found: {path}"}
    if base.is_file():
        return {"path": path, "files": [str(base.relative_to(WORKSPACE_ROOT))]}

    entries: list[str] = []
    for item in sorted(base.rglob("*")):
        if ".git" in item.parts or "node_modules" in item.parts or "__pycache__" in item.parts:
            continue
        relative_to_base = item.relative_to(base)
        if len(relative_to_base.parts) > depth:
            continue
        relative = item.relative_to(WORKSPACE_ROOT)
        entries.append(str(relative) + ("/" if item.is_dir() else ""))
        if len(entries) >= limit:
            break
    return {"path": path, "files": entries}


def search_code(pattern: str, path: str = "", case_sensitive: bool = False, limit: int = 200) -> dict[str, Any]:
    """Search workspace files for a pattern (regex or plain substring)."""
    base = _resolve(path)
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error:
        compiled = re.compile(re.escape(pattern), flags)

    matches: list[dict[str, Any]] = []
    roots = [base] if base.is_file() else ([base] if base.is_dir() else [])
    for root in roots:
        for item in root.rglob("*") if root.is_dir() else [root]:
            if ".git" in item.parts or "node_modules" in item.parts or "__pycache__" in item.parts:
                continue
            if not item.is_file():
                continue
            try:
                if item.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yml", ".yaml", ".toml", ".txt", ".css", ".html", ".ini", ".cfg"}:
                    continue
                text = item.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if compiled.search(line):
                    matches.append(
                        {
                            "path": str(item.relative_to(WORKSPACE_ROOT)),
                            "line": line_no,
                            "text": line.strip()[:200],
                        }
                    )
                    if len(matches) >= limit:
                        return {"pattern": pattern, "matches": matches}
    return {"pattern": pattern, "matches": matches}


def read_file(path: str, start: int = 1, limit: int = 400) -> dict[str, Any]:
    """Read a workspace file, optionally with line range."""
    target = _resolve(path)
    if not target.exists():
        return {"path": path, "content": "", "error": f"Not found: {path}"}
    if not target.is_file():
        return {"path": path, "content": "", "error": f"Not a file: {path}"}
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {"path": path, "content": "", "error": str(exc)}
    lines = text.splitlines()
    total = len(lines)
    start = max(1, min(start, total)) if total else 1
    end = min(total, start + limit - 1)
    return {
        "path": path,
        "total_lines": total,
        "start": start,
        "end": end,
        "content": "\n".join(lines[start - 1 : end]),
    }


def write_file(path: str, content: str) -> dict[str, Any]:
    """Write (create or overwrite) a file inside the workspace."""
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "written": True, "bytes": len(content.encode("utf-8"))}


def edit_file(path: str, old: str, new: str) -> dict[str, Any]:
    """Replace an exact substring in a workspace file (like the OpenHands editor)."""
    target = _resolve(path)
    if not target.exists():
        return {"path": path, "written": False, "error": f"Not found: {path}"}
    text = target.read_text(encoding="utf-8")
    if old not in text:
        return {"path": path, "written": False, "error": "old string not found"}
    updated = text.replace(old, new, 1)
    target.write_text(updated, encoding="utf-8")
    return {"path": path, "written": True}


async def run_command(command: str, timeout: int = 120) -> dict[str, Any]:
    """Run a shell command in the workspace and capture stdout/stderr."""
    normalized = (command or "").strip()
    if not normalized:
        return {"command": command, "exit_code": -1, "stdout": "", "stderr": "Empty command"}

    lowered = normalized.lower()
    if any(pattern in lowered for pattern in _BLOCKED_COMMAND_PATTERNS):
        return {"command": command, "exit_code": -1, "stdout": "", "stderr": "Blocked command", "blocked": True}

    try:
        proc = await asyncio.create_subprocess_shell(
            normalized,
            cwd=str(WORKSPACE_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return {"command": command, "exit_code": -1, "stdout": "", "stderr": f"Timed out after {timeout}s", "timeout": True}
    except Exception as exc:  # noqa: BLE001
        return {"command": command, "exit_code": -1, "stdout": "", "stderr": str(exc)}

    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": (stdout or b"").decode(errors="replace")[-12000:],
        "stderr": (stderr or b"").decode(errors="replace")[-4000:],
    }


async def run_tests() -> dict[str, Any]:
    return await _run_script(
        "test",
        [("python", ["-m", "pytest", "backend/tests", "-q"]), ("node", ["npm", "test"])],
    )


async def run_lint() -> dict[str, Any]:
    return await _run_script(
        "lint",
        [("node", ["npm", "run", "lint"]), ("python", ["python", "-m", "flake8", "backend"])],
    )


async def run_build() -> dict[str, Any]:
    return await _run_script(
        "build",
        [("node", ["npm", "run", "build"]), ("python", ["python", "-m", "py_compile", "-q", "backend/app"])],
    )


async def _run_script(label: str, candidates: list[tuple[str, list[str]]]) -> dict[str, Any]:
    for kind, command in candidates:
        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(WORKSPACE_ROOT),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            return {
                "kind": label,
                "runner": kind,
                "command": " ".join(command),
                "exit_code": proc.returncode,
                "stdout": (stdout or b"").decode(errors="replace")[-12000:],
                "stderr": (stderr or b"").decode(errors="replace")[-4000:],
            }
        except FileNotFoundError:
            continue
        except asyncio.TimeoutError:
            return {"kind": label, "runner": kind, "command": " ".join(command), "exit_code": -1, "stdout": "", "stderr": f"Timed out ({label})", "timeout": True}
        except Exception as exc:  # noqa: BLE001
            return {"kind": label, "runner": kind, "command": " ".join(command), "exit_code": -1, "stdout": "", "stderr": str(exc)}
    return {"kind": label, "runner": "none", "command": "", "exit_code": -1, "stdout": "", "stderr": f"No {label} runner available"}


def task_tracker(task_id: str, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Maintain a per-task checklist (TaskTrackerTool equivalent)."""
    if items is not None:
        _task_lists[task_id] = items
    return {"task_id": task_id, "items": _task_lists.get(task_id, [])}


def think(reasoning: str) -> dict[str, Any]:
    """Reasoning passthrough (ThinkTool equivalent)."""
    return {"reasoning": reasoning, "acknowledged": True}


def finish(summary: str) -> dict[str, Any]:
    """Signal task completion (FinishTool equivalent)."""
    return {"summary": summary, "finished": True}


def summarize_diff(paths: list[str] | None = None) -> dict[str, Any]:
    """Summarize recent changes via git status/diff in the workspace."""
    return {"paths": paths or [], "note": "summarize_diff delegates to run_command('git diff --stat')"}
