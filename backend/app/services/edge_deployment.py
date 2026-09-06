"""Edge binary deployment / rollout orchestration (Milestone 4).

Wires the release-safety core (`edge_updates.py`) into a deployable rollout plan:
- validates a release (digest + compatibility + rings) via `plan_update`,
- records a deterministic deployment attempt with ring target,
- tracks a small in-memory deployment registry (canary/rollback source of truth).
Pure logic + in-memory state (no I/O) so it is unit-testable. Actual binary
distribution/install remains a deployment executor step.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.edge_updates import (
    EdgeRelease,
    EdgeUpdateError,
    plan_update,
    ring_index,
)


class DeploymentError(RuntimeError):
    pass


@dataclass
class DeploymentRecord:
    deployment_id: str
    version: str
    from_version: str
    from_ring: str
    to_ring: str
    health_gate_ok: bool
    promotion: str
    created_at: str
    notes: str = ""


@dataclass
class DeploymentRegistry:
    _records: dict[str, DeploymentRecord] = field(default_factory=dict)

    def add(self, record: DeploymentRecord) -> DeploymentRecord:
        self._records[record.deployment_id] = record
        return record

    def get(self, deployment_id: str) -> DeploymentRecord | None:
        return self._records.get(deployment_id)

    def latest(self) -> DeploymentRecord | None:
        if not self._records:
            return None
        # highest ring index = most promoted
        return max(self._records.values(), key=lambda r: ring_index(r.to_ring))


_deployment_registry = DeploymentRegistry()


def default_current_ring() -> str:
    latest = _deployment_registry.latest()
    return latest.to_ring if latest else "local"


def plan_rollout(
    release: EdgeRelease,
    *,
    package: bytes | None = None,
    current_version: str,
    target_ring: str | None = None,
    current_ring: str | None = None,
    health_gate_ok: bool = False,
    pending_task: bool = False,
    previous_release: EdgeRelease | None = None,
    operator: str = "system",
) -> dict[str, Any]:
    """Return a rollout plan (via edge_updates.plan_update) and persist it."""
    cur_ring = current_ring or default_current_ring()
    try:
        plan = plan_update(
            release,
            package=package,
            current_version=current_version,
            current_ring=cur_ring,
            target_ring=target_ring,
            health_gate_ok=health_gate_ok,
            pending_task=pending_task,
            previous_release=previous_release,
        )
    except EdgeUpdateError as exc:
        raise DeploymentError(str(exc)) from exc

    record = DeploymentRecord(
        deployment_id="deploy-" + uuid.uuid4().hex[:12],
        version=release.version,
        from_version=current_version,
        from_ring=cur_ring,
        to_ring=plan["rolled_out_to"],
        health_gate_ok=health_gate_ok,
        promotion=plan["promotion"],
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=plan.get("notes", "") or "",
    )
    _deployment_registry.add(record)
    plan["deployment_id"] = record.deployment_id
    plan["operator"] = operator
    return plan


def get_deployment(deployment_id: str) -> DeploymentRecord | None:
    return _deployment_registry.get(deployment_id)


def list_deployments(limit: int = 20) -> list[dict[str, Any]]:
    records = sorted(_deployment_registry._records.values(), key=lambda r: r.created_at, reverse=True)
    return [
        {
            "deployment_id": r.deployment_id,
            "version": r.version,
            "from_ring": r.from_ring,
            "to_ring": r.to_ring,
            "promotion": r.promotion,
            "created_at": r.created_at,
        }
        for r in records[:limit]
    ]
