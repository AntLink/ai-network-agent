"""Backup restore planning and safety (Milestone 4).

Deterministic, fail-closed decision logic for restoring a saved device
configuration from a file-based backup. Separating the planning logic (pure,
testable) from live device I/O lets us verify safety rules without a live device:

- restore is refused when the backup is missing or empty;
- restore is refused when the target device is unknown;
- restore is refused when the selected driver does not expose an `apply`
  capability (no safe way to push the config);
- a restore plan reports how many lines would be applied and which action the
  driver supports (apply / candidate).

The endpoint adds operator authorization + audit; this module decides eligibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RestoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class RestorePlan:
    backup_id: str
    device_id: str
    device_vendor: str
    lines: int
    bytes: int
    action: str  # "apply" | "candidate" | "preview"
    note: str


def _normalize_device_capabilities(driver: object) -> bool:
    return hasattr(driver, "apply") and callable(getattr(driver, "apply"))


def plan_restore(
    *,
    backup_id: str,
    backup_path: Path,
    device: dict | None,
    driver: object | None,
    backup_content: str | None = None,
) -> RestorePlan:
    """Return a RestorePlan, or raise RestoreError (fail-closed)."""
    if not backup_id:
        raise RestoreError("backup_id is required")
    path = Path(backup_path)
    if not path.is_file():
        raise RestoreError(f"backup '{backup_id}' does not exist")
    if device is None:
        raise RestoreError("target device is unknown")
    if driver is None or not _normalize_device_capabilities(driver):
        raise RestoreError("selected driver cannot apply configuration (no safe restore path)")

    content = backup_content
    if content is None:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise RestoreError(f"backup '{backup_id}' could not be read: {exc}") from exc
    if content is None or not content.strip():
        raise RestoreError("backup is empty; refusing to restore an empty configuration")

    lines = [ln for ln in content.splitlines() if ln.strip()]
    vendor = str(device.get("vendor", "unknown")).lower()
    return RestorePlan(
        backup_id=backup_id,
        device_id=str(device.get("id", device.get("hostname", ""))),
        device_vendor=vendor,
        lines=len(lines),
        bytes=len(content),
        action="apply",
        note="planning only; execution requires a reachable device and operator approval",
    )