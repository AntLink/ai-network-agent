#!/usr/bin/env python3
"""Project-local, fail-closed production gate.

This is the repository entry point for the V5 gate so a fresh checkout does
not depend on an agent's installed skill directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import subprocess
from pathlib import Path
from typing import Any

PLACEHOLDERS = {"<CONFIGURE>", "<TODO>", "TODO", ""}


def placeholder(value: Any) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and (
        value.strip() in PLACEHOLDERS
        or "<CONFIGURE>" in value
        or "<TODO>" in value
    )


def evidence_exists(root: Path, pattern: str) -> bool:
    if placeholder(pattern):
        return False
    path = Path(pattern)
    target = pattern if path.is_absolute() else str(root / pattern)
    return any(Path(item).exists() for item in glob.glob(target))


def run_gate(root: Path, gate: dict[str, Any], timeout_default: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": gate.get("id", "UNKNOWN"),
        "description": gate.get("description", ""),
        "required": bool(gate.get("required", True)),
        "status": "FAIL",
        "command_status": "NOT_CONFIGURED",
        "evidence_status": "PASS",
        "exit_code": None,
        "output": "",
    }
    command = gate.get("command", [])
    evidence = gate.get("evidence", [])
    if command:
        if any(placeholder(item) for item in command):
            result["command_status"] = "NOT_CONFIGURED"
        else:
            try:
                completed = subprocess.run(
                    command,
                    cwd=root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=int(gate.get("timeout_seconds", timeout_default)),
                    env=os.environ.copy(),
                    check=False,
                )
                result["exit_code"] = completed.returncode
                result["output"] = (completed.stdout or "")[-12000:]
                result["command_status"] = (
                    "PASS" if completed.returncode == 0 else "FAIL"
                )
            except subprocess.TimeoutExpired as exc:
                result["command_status"] = "FAIL"
                result["output"] = f"TIMEOUT: {exc}"
            except Exception as exc:  # noqa: BLE001
                result["command_status"] = "FAIL"
                result["output"] = f"ERROR: {exc}"
    else:
        result["command_status"] = "NOT_REQUIRED" if evidence else "NOT_CONFIGURED"

    missing = [item for item in evidence if not evidence_exists(root, item)]
    if missing:
        result["evidence_status"] = "FAIL"
        result["missing_evidence"] = missing
    result["status"] = (
        "PASS"
        if result["command_status"] in {"PASS", "NOT_REQUIRED"}
        and result["evidence_status"] == "PASS"
        else "FAIL"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed production gate")
    parser.add_argument("--config", default="docs/production/production-gate.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-dir", default="docs/evidence/production-gates")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_arg = Path(args.config)
    config_path = config_arg.resolve() if config_arg.is_absolute() else root / config_arg
    if not config_path.exists():
        print(f"FAIL: production gate config missing: {config_path}")
        return 1

    config = json.loads(config_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    release = config.get("release", {})
    for key, value in release.items():
        if placeholder(value):
            errors.append(f"release.{key} is not configured")

    required_files = []
    for relative in config.get("required_files", []):
        path = root / relative if not placeholder(relative) else None
        ok = path is not None and path.exists()
        reason = ""
        if ok and path is not None:
            try:
                content = path.read_text(encoding="utf-8")
                if "<TODO>" in content or "<CONFIGURE>" in content:
                    ok = False
                    reason = "contains unresolved placeholders"
            except UnicodeDecodeError:
                pass
        required_files.append(
            {"path": relative, "status": "PASS" if ok else "FAIL", "reason": reason}
        )
        if not ok:
            errors.append(f"required file incomplete/missing: {relative}" + (f" ({reason})" if reason else ""))

    gates = [run_gate(root, gate, args.timeout) for gate in config.get("gates", [])]
    for gate in gates:
        if gate["required"] and gate["status"] != "PASS":
            errors.append(f"required gate failed: {gate['id']}")

    now = dt.datetime.now().astimezone()
    overall = "PASS" if not errors else "FAIL"
    report = {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "git_commit": release.get("git_commit"),
        "overall_status": overall,
        "config": str(config_path),
        "release": release,
        "required_files": required_files,
        "gates": gates,
        "errors": errors,
    }
    report_dir = root / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    json_path = report_dir / f"production-gate-{stamp}.json"
    md_path = report_dir / f"production-gate-{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Production Gate Report", "", f"- Generated: `{report['generated_at']}`",
        f"- Overall: **{overall}**", f"- Config: `{config_path}`", "",
        "## Required Files", "", "| Path | Status | Reason |", "|---|---|---|",
    ]
    lines += [f"| `{item['path']}` | {item['status']} | {item['reason']} |" for item in required_files]
    lines += ["", "## Gates", "", "| Gate | Required | Status | Command | Evidence |", "|---|---:|---|---|---|"]
    lines += [f"| {gate['id']} | {gate['required']} | {gate['status']} | {gate['command_status']} | {gate['evidence_status']} |" for gate in gates]
    if errors:
        lines += ["", "## Blocking Errors", ""] + [f"- {error}" for error in errors]
    lines += ["", f"Machine-readable report: `{json_path}`", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{overall}: production gate")
    print(md_path)
    print(json_path)
    for error in errors:
        print("-", error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
