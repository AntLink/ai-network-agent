"""Milestone 4: Edge binary update / rollout / rollback safety."""
import pytest

from app.services.edge_updates import (
    EdgeRelease,
    EdgeUpdateError,
    can_rollback,
    plan_update,
    verify_digest,
)


def _release(version="1.1.0", digest=None, sig="sig", **kw):
    return EdgeRelease(
        version=version,
        digest_sha256=digest or ("0" * 64),
        signature=sig,
        **kw,
    )


def _valid_digest_release(version="1.1.0", **kw):
    return EdgeRelease(
        version=version,
        digest_sha256=sha_for(b"new-edge"),
        signature="sig",
        **kw,
    )


def sha_for(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def test_verify_digest_matches():
    release = _valid_digest_release()
    assert verify_digest(release, b"new-edge") is True


def test_verify_digest_rejects_corrupt_package():
    release = _valid_digest_release()
    assert verify_digest(release, b"tampered-edge") is False


def test_verify_digest_rejects_non_hex_digest():
    release = _release(digest="not-a-hex-digest")
    assert verify_digest(release, b"new-edge") is False


def test_compatibility_range():
    release = EdgeRelease(
        version="1.1.0", digest_sha256="0"*64, signature="s",
        min_protocol_version=1, max_protocol_version=2, min_driver_capability_version=1,
    )
    from app.services.edge_updates import compatibility_ok
    assert compatibility_ok(release, protocol_version=1, driver_capability_version=1)
    assert compatibility_ok(release, protocol_version=2, driver_capability_version=3)
    assert not compatibility_ok(release, protocol_version=3, driver_capability_version=1)


def test_plan_update_accepts_promote_with_health_gate():
    plan = plan_update(
        _valid_digest_release(),
        package=b"new-edge",
        current_version="1.0.0",
        current_ring="canary",
        target_ring="5%",
        health_gate_ok=True,
    )
    assert plan["action"] == "update"
    assert plan["promotion"] == "promote"
    assert plan["rolled_out_to"] == "5%"


def test_plan_update_rejects_digest_mismatch():
    with pytest.raises(EdgeUpdateError, match="digest mismatch"):
        plan_update(
            _valid_digest_release(),
            package=b"different-content",
            current_version="1.0.0",
        )


def test_plan_update_rejects_protocol_incompatibility():
    release = _valid_digest_release(min_protocol_version=3, max_protocol_version=4)
    with pytest.raises(EdgeUpdateError, match="incompatibility"):
        plan_update(
            release,
            package=b"new-edge",
            current_version="1.0.0",
            current_protocol=1,
        )


def test_plan_update_rejects_downgrade_below_security_floor():
    release = _valid_digest_release(version="0.5.0", security_min_version="0.9.0")
    with pytest.raises(EdgeUpdateError, match="security minimum"):
        plan_update(release, package=b"new-edge", current_version="1.0.0")


def test_plan_update_rejects_ring_skip_without_health_gate():
    with pytest.raises(EdgeUpdateError, match="health gate"):
        plan_update(
            _valid_digest_release(),
            package=b"new-edge",
            current_version="1.0.0",
            current_ring="local",
            target_ring="100%",
            health_gate_ok=False,
        )


def test_plan_update_blocks_on_pending_task():
    with pytest.raises(EdgeUpdateError, match="non-interruptible task"):
        plan_update(
            _valid_digest_release(),
            package=b"new-edge",
            current_version="1.0.0",
            pending_task=True,
        )


def test_plan_update_preserves_rollback_release():
    prev = _valid_digest_release(version="1.0.0")
    plan = plan_update(
        _valid_digest_release(version="1.1.0"),
        package=b"new-edge",
        current_version="1.0.0",
        previous_release=prev,
    )
    assert plan["rollback"]["available"] is True
    assert plan["rollback"]["version"] == "1.0.0"


def test_can_rollback_with_known_good():
    prev = _valid_digest_release(version="1.0.0")
    res = can_rollback(previous_release=prev)
    assert res["allowed"] is True
    assert res["version"] == "1.0.0"


def test_can_rollback_fails_without_known_good():
    res = can_rollback(previous_release=None)
    assert res["allowed"] is False


def test_can_rollback_blocks_on_pending_task():
    prev = _valid_digest_release(version="1.0.0")
    res = can_rollback(previous_release=prev, pending_task=True)
    assert res["allowed"] is False