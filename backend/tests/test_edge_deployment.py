"""Milestone 4: Edge binary rollout/deployment service + endpoint."""
import pytest

from app.services.edge_updates import EdgeRelease
from app.services.edge_deployment import (
    DeploymentError,
    _deployment_registry,
    default_current_ring,
    get_deployment,
    list_deployments,
    plan_rollout,
)


@pytest.fixture(autouse=True)
def _clear_registry():
    _deployment_registry._records.clear()
    yield


def _release(version="1.1.0", digest=None, sig="sig", **kw):
    return EdgeRelease(
        version=version,
        digest_sha256=digest or ("0" * 64),
        signature=sig,
        **kw,
    )


def test_plan_rollout_records_deployment_and_tracks_ring():
    plan = plan_rollout(
        _release(version="1.1.0"),
        current_version="1.0.0",
        target_ring="canary",
        health_gate_ok=True,
    )
    assert plan["deployment_id"]
    assert plan["rolled_out_to"] == "canary"
    # subsequent default current ring reflects the promotion
    assert default_current_ring() == "canary"


def test_plan_rollout_rejects_ring_skip_without_gate():
    with pytest.raises(DeploymentError, match="health gate"):
        plan_rollout(
            _release(version="1.1.0"),
            current_version="1.0.0",
            current_ring="local",
            target_ring="100%",
            health_gate_ok=False,
        )


def test_plan_rollout_rejects_unknown_ring():
    with pytest.raises(DeploymentError, match="unknown rollout ring"):
        plan_rollout(
            _release(version="1.1.0"),
            current_version="1.0.0",
            target_ring="not-a-ring",
            health_gate_ok=True,
        )


def test_get_and_list_deployments():
    plan1 = plan_rollout(_release(version="1.1.0"), current_version="1.0.0", target_ring="canary", health_gate_ok=True)
    plan2 = plan_rollout(_release(version="1.2.0"), current_version="1.1.0", target_ring="25%", health_gate_ok=True)
    # list returns newest first
    listing = list_deployments(limit=20)
    assert listing[0]["version"] == "1.2.0"
    # get a specific deployment
    rec = get_deployment(plan2["deployment_id"])
    assert rec is not None
    assert rec.to_ring == "25%"


def test_plan_rollout_previous_release_keeps_rollback():
    prev = _release(version="1.0.0")
    plan = plan_rollout(
        _release(version="1.1.0"),
        current_version="1.0.0",
        previous_release=prev,
    )
    assert plan["rollback"]["available"] is True
    assert plan["rollback"]["version"] == "1.0.0"
