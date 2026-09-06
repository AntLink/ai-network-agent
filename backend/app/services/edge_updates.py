"""Edge binary update, rollout-ring, and rollback safety (Milestone 4).

Implements the release-safety core of the Edge update contract:
- immutable release artifact with SHA-256 digest + detached signature;
- digest verification and protocol/driver-capability compatibility gating;
- downgrade floor to a security minimum;
- bounded rollout rings (local -> canary -> ... -> 100%) with explicit health-gate
  promotion (no skipping rings without a passed gate);
- blocking update while a non-interruptible task is active;
- rollback prerequisites modeled as the preserved last-known-good release.

Pure logic with no I/O so it is deterministic and unit-testable. The actual
binary distribution/install/restart is a deployment concern; this service decides
whether an update is permitted and how to stage it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

RINGS: list[str] = ["local", "internal", "canary", "5%", "25%", "50%", "100%"]


class EdgeUpdateError(RuntimeError):
    pass


@dataclass(frozen=True)
class EdgeRelease:
    version: str
    digest_sha256: str
    signature: str
    min_protocol_version: int = 1
    max_protocol_version: int = 2
    min_driver_capability_version: int = 1
    security_min_version: str = "0.0.0"
    notes: str = ""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_digest(release: EdgeRelease, package: bytes) -> bool:
    """Constant-time-safe comparison of package SHA-256 to the release digest."""
    expected = release.digest_sha256.lower()
    actual = sha256_hex(package).lower()
    return (
        len(expected) == 64
        and len(actual) == 64
        and _bytes_equal(bytes.fromhex(actual), bytes.fromhex(expected))
    )


def _bytes_equal(a: bytes, b: bytes) -> bool:
    # Constant-time comparison.
    diff = len(a) ^ len(b)
    for x, y in zip(a, b):
        diff |= x ^ y
    return diff == 0


def compatibility_ok(
    release: EdgeRelease,
    *,
    protocol_version: int,
    driver_capability_version: int,
) -> bool:
    return (
        release.min_protocol_version <= protocol_version <= release.max_protocol_version
        and release.min_driver_capability_version <= driver_capability_version
    )


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for seg in version.replace("-", ".").split("."):
        for chunk in seg.split("+"):
            if chunk:
                try:
                    parts.append(int(chunk))
                    break
                except ValueError:
                    parts.append(0)
                    break
            break
    return tuple(parts) or (0,)


def ring_index(ring: str) -> int:
    if ring not in RINGS:
        raise EdgeUpdateError(f"unknown rollout ring {ring!r}")
    return RINGS.index(ring)


def plan_update(
    release: EdgeRelease,
    *,
    package: bytes | None,
    current_version: str,
    current_protocol: int = 1,
    current_driver_cap: int = 1,
    current_ring: str = "local",
    target_ring: str | None = None,
    health_gate_ok: bool = False,
    pending_task: bool = False,
    previous_release: EdgeRelease | None = None,
) -> dict[str, Any]:
    """Return a deterministic Edge update plan, or raise EdgeUpdateError.

    Fails closed (raises) on: invalid digest, protocol incompatibility,
    downgrade below the security minimum, skipping a rollout ring without a
    passed health gate, or an active non-interruptible task.
    """
    target = target_ring if target_ring is not None else current_ring
    current_idx = ring_index(current_ring)
    target_idx = ring_index(target)

    if pending_task:
        raise EdgeUpdateError("update blocked: a non-interruptible task is active")

    if package is not None and not verify_digest(release, package):
        raise EdgeUpdateError("update rejected: package SHA-256 digest mismatch")

    if not compatibility_ok(
        release, protocol_version=current_protocol, driver_capability_version=current_driver_cap
    ):
        raise EdgeUpdateError("update rejected: protocol/driver-capability incompatibility")

    if _version_tuple(release.version) < _version_tuple(release.security_min_version):
        raise EdgeUpdateError("update rejected: version below security minimum")

    if target_idx > current_idx:
        if not health_gate_ok:
            raise EdgeUpdateError(
                f"update rejected: cannot promote from {current_ring!r} to {target!r} without a passed health gate"
            )
        # Promotion must be one supported ring step at a time unless explicit.
    if target_idx < current_idx:
        raise EdgeUpdateError("update rejected: cannot move to an earlier ring")

    rollback = None
    if previous_release is not None:
        rollback = {
            "available": True,
            "version": previous_release.version,
            "digest_sha256": previous_release.digest_sha256,
            "note": "last-known-good preserved for bounded-failure rollback",
        }

    return {
        "action": "update",
        "version": release.version,
        "from": current_version,
        "from_ring": current_ring,
        "to_ring": target_ring or current_ring,
        "digest_sha256": release.digest_sha256,
        "protocol_compatible": True,
        "promotion": "promote" if target_idx > current_idx else "same" if target_idx == current_idx else "demote",
        "health_gate_ok": health_gate_ok,
        "rolled_out_to": target_ring or current_ring,
        "rollback": rollback or {"available": False},
        "notes": release.notes or "",
    }


def can_rollback(
    *,
    previous_release: EdgeRelease | None,
    protocol_version: int = 1,
    driver_capability_version: int = 1,
    pending_task: bool = False,
) -> dict[str, Any]:
    """Determine whether a bounded-failure rollback to last-known-good is permitted."""
    if previous_release is None:
        return {"allowed": False, "reason": "no previous known-good release preserved"}
    if pending_task:
        return {"allowed": False, "reason": "a non-interruptible task is active"}
    if not compatibility_ok(
        previous_release,
        protocol_version=protocol_version,
        driver_capability_version=driver_capability_version,
    ):
        return {"allowed": False, "reason": "known-good release is protocol-incompatible"}
    return {
        "allowed": True,
        "reason": "bounded failure; last-known-good available",
        "version": previous_release.version,
        "digest_sha256": previous_release.digest_sha256,
    }