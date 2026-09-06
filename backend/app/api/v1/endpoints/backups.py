"""Backup inventory, persistence, and download endpoints (file-based).

Backup files disimpan sebagai `backups/<backup_id>.cfg`. Modul ini
dipakai oleh agent tool `backup_config` (lewat `save_backup`) dan oleh
frontend/API.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.audit import log_event
from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver
from app.services.backup_restore import RestoreError, plan_restore

router = APIRouter()

BACKUP_DIR = Path(settings.BACKUP_DIR).resolve()

_ALLOWED_ID_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789._-"
)


def _ensure_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def _base_url() -> str:
    return settings.PUBLIC_BASE_URL.rstrip("/")


def _safe_backup_id(backup_id: str) -> str:
    """Cegah path traversal: hanya karakter aman yang boleh masuk URL."""
    backup_id = (backup_id or "").strip()
    if not backup_id or any(ch not in _ALLOWED_ID_CHARS for ch in backup_id):
        raise HTTPException(status_code=400, detail="Invalid backup id")
    return backup_id


def _list_backup_files() -> list[dict[str, object]]:
    _ensure_dir()
    prefix = f"{settings.API_V1_PREFIX}/backups/download"
    items: list[dict[str, object]] = []
    for f in sorted(BACKUP_DIR.glob("*.cfg"), reverse=True):
        stat = f.stat()
        items.append(
            {
                "id": f.stem,
                "device": f.stem,
                "device_id": "",
                "backup_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": "running",
                "size": stat.st_size,
                "created_by": "system",
                "file": str(f),
                "download_url": f"{_base_url()}{prefix}/{f.stem}",
            }
        )
    return items


def save_backup(device_id: str, content: str, created_by: str = "agent") -> dict[str, object]:
    """Simpan isi konfigurasi sebagai file .cfg dan kembalikan metadatanya.

    Dipanggil dari agent tool `backup_config` dan endpoint POST /backups.
    """
    _ensure_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_id = f"backup-{device_id.strip()}-{ts}"
    path = BACKUP_DIR / f"{backup_id}.cfg"
    path.write_text(content or "", encoding="utf-8")
    return {
        "backup_id": backup_id,
        "device_id": device_id.strip(),
        "file": str(path),
        "size": path.stat().st_size,
        "timestamp": datetime.now().isoformat(),
        "created_by": created_by,
        "download_url": f"{_base_url()}{settings.API_V1_PREFIX}/backups/download/{backup_id}",
    }


@router.get("")
async def list_backups():
    return {"backups": _list_backup_files()}


@router.get("/download/{backup_id}")
async def download_backup(backup_id: str):
    """Unduh file backup sebagai text file (.cfg)."""
    backup_id = _safe_backup_id(backup_id)
    path = BACKUP_DIR / f"{backup_id}.cfg"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Backup '{backup_id}' not found")
    return FileResponse(path, media_type="text/plain", filename=f"{backup_id}.cfg")


@router.post("")
async def create_backup(payload: dict):
    """Simpan backup baru (konten diberikan, mis. dari frontend/script)."""
    device_id = str(payload.get("device_id") or "unspecified").strip() or "unspecified"
    content = str(payload.get("content") or payload.get("config") or "")
    created_by = str(payload.get("created_by") or "system")
    return save_backup(device_id, content, created_by=created_by)


@router.delete("/{backup_id}")
async def delete_backup(backup_id: str):
    backup_id = _safe_backup_id(backup_id)
    path = BACKUP_DIR / f"{backup_id}.cfg"
    if path.exists():
        path.unlink()
    return {"status": "deleted", "backup_id": backup_id}


@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    operator_identity: str | None = Header(default=None, alias="X-Authenticated-Operator"),
    operator_role: str | None = Header(default=None, alias="X-Operator-Role"),
):
    """Plan a config restore from a saved backup to its device (fail-closed).

    Requires a `network-admin` operator identity. Returns the deterministic
    restore plan and records an audit event. Live device application is a
    separate privileged executor step; this endpoint validates eligibility and
    authorization without pushing config in an unverified path.
    """
    if not operator_identity:
        raise HTTPException(status_code=401, detail="authenticated operator identity is required")
    if operator_role != "network-admin":
        raise HTTPException(status_code=403, detail="network-admin role is required")

    backup_id = _safe_backup_id(backup_id)
    path = BACKUP_DIR / f"{backup_id}.cfg"
    device_id = ""
    try:
        # The backup stem is `backup-<device_id>-<timestamp>`; recover device id.
        stem = Path(backup_id).stem
        if stem.startswith("backup-"):
            device_id = stem[len("backup-"):].rsplit("-", 1)[0]
        device = inventory_repository.get_device(device_id) if device_id else None
        driver = get_driver(device) if device else None
        plan = plan_restore(
            backup_id=backup_id,
            backup_path=path,
            device=device,
            driver=driver,
        )
    except RestoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_event(
        device_id=plan.device_id,
        action="BACKUP-RESTORE-PLAN",
        command=f"restore:{backup_id}",
        result="planned",
        user=operator_identity,
        status="PLANNED",
        error=None,
    )
    return {
        "status": "planned",
        "restore": {
            "backup_id": plan.backup_id,
            "device_id": plan.device_id,
            "device_vendor": plan.device_vendor,
            "lines": plan.lines,
            "bytes": plan.bytes,
            "action": plan.action,
            "note": plan.note,
        },
    }