from app.services.edge_identity import EdgeIdentityRegistry, EdgeLifecycleState
from pathlib import Path
import uuid


def test_edge_lifecycle_state_restores_from_atomic_local_file():
    path = Path("backend") / f".test-edge-lifecycle-{uuid.uuid4().hex}.json"
    try:
        first = EdgeIdentityRegistry(str(path))
        assert first.set_state("edge-persisted", EdgeLifecycleState.QUARANTINED) is EdgeLifecycleState.QUARANTINED
        second = EdgeIdentityRegistry(str(path))
        assert second.state("edge-persisted") is EdgeLifecycleState.QUARANTINED
        assert second.clear_quarantine("edge-persisted") is EdgeLifecycleState.ACTIVE
        assert EdgeIdentityRegistry(str(path)).state("edge-persisted") is EdgeLifecycleState.ACTIVE
    finally:
        path.unlink(missing_ok=True)


def test_revoked_identity_cannot_be_reactivated():
    path = Path("backend") / f".test-edge-revoked-{uuid.uuid4().hex}.json"
    try:
        registry = EdgeIdentityRegistry(str(path))
        registry.set_state("edge-revoked", EdgeLifecycleState.REVOKED)
        registry.set_state("edge-revoked", EdgeLifecycleState.ACTIVE)
    except ValueError as exc:
        assert "reactivated" in str(exc)
    else:
        raise AssertionError("revoked identity must not be reactivated")
    finally:
        path.unlink(missing_ok=True)
