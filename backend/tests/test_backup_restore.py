"""Milestone 4: backup restore planning and safety."""
import shutil
import tempfile
from pathlib import Path

import pytest

from app.services.backup_restore import RestoreError, plan_restore


class _ApplyingDriver:
    async def apply(self, commands):
        return None


class _NoApplyDriver:
    pass


def _device(vendor="cisco", device_id="r1"):
    return {"id": device_id, "hostname": "R1", "vendor": vendor}


@pytest.fixture
def tmpdir():
    d = Path(tempfile.mkdtemp(prefix="br_test_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_plan_restore_produces_expected_plan(tmpdir):
    bp = tmpdir / "backup-r1-20260904.cfg"
    bp.write_text("hostname R1\ninterface g0/1\n ip address 10.0.0.1 255.255.255.0\n", encoding="utf-8")
    plan = plan_restore(
        backup_id="backup-r1-20260904", backup_path=bp,
        device=_device(), driver=_ApplyingDriver(),
    )
    assert plan.device_id == "r1"
    assert plan.action == "apply"
    assert plan.lines == 3


def test_plan_restore_rejects_missing_backup(tmpdir):
    with pytest.raises(RestoreError, match="does not exist"):
        plan_restore(backup_id="x", backup_path=tmpdir / "missing.cfg",
                     device=_device(), driver=_ApplyingDriver())


def test_plan_restore_rejects_unknown_device(tmpdir):
    bp = tmpdir / "backup.cfg"
    bp.write_text("hostname R1\n", encoding="utf-8")
    with pytest.raises(RestoreError, match="device is unknown"):
        plan_restore(backup_id="b", backup_path=bp, device=None, driver=_ApplyingDriver())


def test_plan_restore_rejects_driver_without_apply(tmpdir):
    bp = tmpdir / "backup.cfg"
    bp.write_text("hostname R1\n", encoding="utf-8")
    with pytest.raises(RestoreError, match="cannot apply"):
        plan_restore(backup_id="b", backup_path=bp, device=_device(), driver=_NoApplyDriver())


def test_plan_restore_rejects_empty_backup(tmpdir):
    bp = tmpdir / "backup.cfg"
    bp.write_text("   \n", encoding="utf-8")
    with pytest.raises(RestoreError, match="empty"):
        plan_restore(backup_id="b", backup_path=bp, device=_device(), driver=_ApplyingDriver())


def test_plan_restore_rejects_missing_backup_id(tmpdir):
    bp = tmpdir / "b.cfg"
    bp.write_text("x\n", encoding="utf-8")
    with pytest.raises(RestoreError, match="backup_id is required"):
        plan_restore(backup_id="", backup_path=bp, device=_device(), driver=_ApplyingDriver())