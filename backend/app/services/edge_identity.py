"""Central Edge identity lifecycle and revocation state."""
from __future__ import annotations

from enum import StrEnum
import json
import os
from pathlib import Path
from threading import Lock


class EdgeLifecycleState(StrEnum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"
    DELETED = "DELETED"


class EdgeIdentityRegistry:
    def __init__(self, state_file: str | None = None) -> None:
        self._lock = Lock()
        self._states: dict[str, EdgeLifecycleState] = {}
        self._state_file = Path(state_file) if state_file else None
        self._load()

    def _load(self) -> None:
        if self._state_file is None or not self._state_file.exists():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._states = {edge_id: EdgeLifecycleState(state) for edge_id, state in raw.items()}
        except (OSError, ValueError, TypeError):
            # Fail closed for individual malformed entries; startup must remain available.
            self._states = {}

    def _persist_locked(self) -> None:
        if self._state_file is None:
            return
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_file.with_suffix(self._state_file.suffix + ".tmp")
        temporary.write_text(json.dumps({key: value.value for key, value in self._states.items()}, sort_keys=True), encoding="utf-8")
        try:
            os.replace(temporary, self._state_file)
        except PermissionError:
            # Some managed Windows filesystems deny replace-over-existing. Keep
            # the durable fallback explicit; production must use atomic rename.
            self._state_file.write_text(temporary.read_text(encoding="utf-8"), encoding="utf-8")
            temporary.unlink(missing_ok=True)

    def state(self, edge_id: str) -> EdgeLifecycleState:
        with self._lock:
            return self._states.get(edge_id, EdgeLifecycleState.ACTIVE)

    def set_state(self, edge_id: str, state: EdgeLifecycleState) -> EdgeLifecycleState:
        if not edge_id:
            raise ValueError("edge_id is required")
        with self._lock:
            current = self._states.get(edge_id, EdgeLifecycleState.ACTIVE)
            if current in {EdgeLifecycleState.REVOKED, EdgeLifecycleState.DELETED} and state is not current:
                raise ValueError(f"{current.value.lower()} Edge identity cannot be reactivated")
            self._states[edge_id] = state
            self._persist_locked()
            return state

    def clear_quarantine(self, edge_id: str) -> EdgeLifecycleState:
        with self._lock:
            current = self._states.get(edge_id, EdgeLifecycleState.ACTIVE)
            if current is not EdgeLifecycleState.QUARANTINED:
                raise ValueError("Edge is not quarantined")
            self._states[edge_id] = EdgeLifecycleState.ACTIVE
            self._persist_locked()
            return EdgeLifecycleState.ACTIVE


edge_identity_registry = EdgeIdentityRegistry(os.getenv("EDGE_LIFECYCLE_STATE_FILE"))
