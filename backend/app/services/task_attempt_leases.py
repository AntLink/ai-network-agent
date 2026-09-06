"""Central lease authority for logical task attempts.

This M2 seam is process-local until the repository gains durable persistence.
All attempt mutations go through this service so a PostgreSQL implementation can
replace it without reintroducing endpoint-owned lease state.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any


class TaskAttemptLeaseStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._attempts: dict[str, dict[str, Any]] = {}

    async def create(self, attempt_id: str, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if attempt_id in self._attempts:
                raise ValueError("attempt already exists")
            idempotency_key = values.get("idempotency_key")
            if idempotency_key and any(item.get("idempotency_key") == idempotency_key for item in self._attempts.values()):
                raise ValueError("idempotency key already exists")
            record = deepcopy(values)
            record["attempt_id"] = attempt_id
            self._attempts[attempt_id] = record
            return deepcopy(record)

    async def get(self, attempt_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._attempts.get(attempt_id)
            return deepcopy(record) if record is not None else None

    async def get_by_idempotency(self, idempotency_key: str) -> dict[str, Any] | None:
        with self._lock:
            for record in self._attempts.values():
                if record.get("idempotency_key") == idempotency_key:
                    return deepcopy(record)
        return None

    async def update(self, attempt_id: str, **values: Any) -> dict[str, Any]:
        with self._lock:
            record = self._attempts.get(attempt_id)
            if record is None:
                raise KeyError(attempt_id)
            record.update(deepcopy(values))
            return deepcopy(record)

    async def claim_for_dispatch(self, attempt_id: str, *, edge_id: str, now: datetime | None = None) -> dict[str, Any] | None:
        """Atomically move a queued attempt into dispatching under Central ownership."""
        current_time = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._attempts.get(attempt_id)
            if record is None or record.get("edge_id") != edge_id or record.get("lease_owner", "CENTRAL") != "CENTRAL":
                return None
            if record.get("status") != "QUEUED" or record.get("execution_status") not in {None, "NOT_DISPATCHED"}:
                return None
            deadline = datetime.fromisoformat(str(record["deadline_at"]))
            lease_expiry = datetime.fromisoformat(str(record["lease_expires_at"]))
            if deadline < current_time or lease_expiry < current_time:
                return None
            record.update({"status": "DISPATCHING", "started_at": current_time.isoformat()})
            return deepcopy(record)

    async def renew(self, attempt_id: str, *, edge_id: str, lease_seconds: int = 60, now: datetime | None = None) -> dict[str, Any] | None:
        """Renew only an owned, active attempt; Central remains the authority."""
        current_time = now or datetime.now(timezone.utc)
        with self._lock:
            record = self._attempts.get(attempt_id)
            if record is None or record.get("edge_id") != edge_id or record.get("status") not in {"QUEUED", "DISPATCHING", "RUNNING"}:
                return None
            current_expiry = datetime.fromisoformat(record["lease_expires_at"])
            if current_time > current_expiry:
                return None
            record["heartbeat_at"] = current_time.isoformat()
            record["lease_expires_at"] = (current_time + timedelta(seconds=lease_seconds)).isoformat()
            return deepcopy(record)

    async def recover_expired(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        """Fence expired attempts without automatically replaying device actions."""
        current_time = now or datetime.now(timezone.utc)
        recovered: list[dict[str, Any]] = []
        with self._lock:
            for record in self._attempts.values():
                expiry = datetime.fromisoformat(record["lease_expires_at"])
                if record.get("status") in {"QUEUED", "DISPATCHING", "RUNNING"} and expiry < current_time:
                    record.update({"status": "UNKNOWN_EXECUTION_STATE", "error_code": "LEASE_EXPIRED_UNKNOWN_EXECUTION"})
                    recovered.append(deepcopy(record))
        return recovered


def build_task_attempt_lease_store(*, backend: str, postgres_dsn: str):
    normalized = backend.strip().lower()
    if normalized == "memory":
        return TaskAttemptLeaseStore()
    if normalized == "postgres":
        from app.services.postgres_task_attempt_leases import PostgresTaskAttemptLeaseStore

        return PostgresTaskAttemptLeaseStore(postgres_dsn)
    raise ValueError(f"unsupported TaskAttempt backend: {backend}")


from app.core.config import settings

task_attempt_lease_store = build_task_attempt_lease_store(
    backend=settings.TASK_ATTEMPT_BACKEND,
    postgres_dsn=settings.POSTGRES_DSN,
)
