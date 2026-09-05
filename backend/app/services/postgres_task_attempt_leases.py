"""Async PostgreSQL TaskAttempt lease adapter.

The adapter is intentionally separate from the M1 memory store until the
application's database lifecycle and migration runner are established.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class PostgresTaskAttemptLeaseStore:
    def __init__(self, dsn: str, *, min_size: int = 1, max_size: int = 10) -> None:
        if not dsn:
            raise ValueError("PostgreSQL DSN is required")
        try:
            import asyncpg
        except ImportError as exc:
            raise RuntimeError("asyncpg package is required for PostgreSQL lease store") from exc
        self._asyncpg = asyncpg
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Any = None

    async def connect(self) -> None:
        if self.pool is None:
            self.pool = await self._asyncpg.create_pool(self.dsn, min_size=self.min_size, max_size=self.max_size)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def get(self, attempt_id: str) -> dict[str, Any] | None:
        await self.connect()
        row = await self.pool.fetchrow("SELECT * FROM task_attempts WHERE attempt_id = $1", attempt_id)
        return dict(row) if row else None

    async def get_by_idempotency(self, idempotency_key: str) -> dict[str, Any] | None:
        await self.connect()
        row = await self.pool.fetchrow(
            "SELECT * FROM task_attempts WHERE idempotency_key = $1 ORDER BY accepted_at LIMIT 1",
            idempotency_key,
        )
        return dict(row) if row else None

    async def create(self, attempt_id_or_record: str | dict[str, Any], values: dict[str, Any] | None = None) -> dict[str, Any]:
        await self.connect()
        if values is None:
            record = dict(attempt_id_or_record) if isinstance(attempt_id_or_record, dict) else {"attempt_id": attempt_id_or_record}
        else:
            record = dict(values)
            record["attempt_id"] = str(attempt_id_or_record)
        def timestamp(name: str) -> datetime:
            value = record[name]
            return value if isinstance(value, datetime) else datetime.fromisoformat(value)

        row = await self.pool.fetchrow(
            """INSERT INTO task_attempts
            (attempt_id, task_id, idempotency_key, edge_id, status, retry_class, execution_fingerprint,
             accepted_at, deadline_at, lease_expires_at, result, error_code, device_id, capability, credential_ref, execution_location,
             replay_parent_attempt_id, execution_status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18) RETURNING *""",
            record["attempt_id"], record["task_id"], record["idempotency_key"], record.get("edge_id"), record["status"],
            record["retry_class"], record.get("execution_fingerprint"), timestamp("accepted_at"),
            timestamp("deadline_at"), timestamp("lease_expires_at"), json.dumps(record["result"]) if record.get("result") is not None else None, record.get("error_code"), record.get("device_id"), record.get("capability"), record.get("credential_ref"), record.get("execution_location"), record.get("replay_parent_attempt_id"), record.get("execution_status"),
        )
        return dict(row)

    async def update(self, attempt_id: str, **values: Any) -> dict[str, Any]:
        await self.connect()
        allowed = {"status", "result", "error_code", "started_at", "finished_at", "heartbeat_at", "lease_expires_at", "retry_decision", "retry_reason", "retry_evaluated_at", "retry_operator", "operator_approval_ref", "operator_approval_token_hash", "replay_parent_attempt_id", "execution_status"}
        updates = {key: value for key, value in values.items() if key in allowed}
        if not updates:
            return await self.get(attempt_id) or {}
        columns = list(updates)
        assignments = ", ".join(f"{column} = ${index + 2}" for index, column in enumerate(columns))
        params: list[Any] = [attempt_id]
        for column in columns:
            value = updates[column]
            if column == "result" and value is not None:
                value = json.dumps(value)
            elif column in {"started_at", "finished_at", "heartbeat_at", "lease_expires_at", "retry_evaluated_at"} and isinstance(value, str):
                value = datetime.fromisoformat(value)
            params.append(value)
        row = await self.pool.fetchrow(f"UPDATE task_attempts SET {assignments} WHERE attempt_id = $1 RETURNING *", *params)
        if row is None:
            raise KeyError(attempt_id)
        return dict(row)

    async def claim_for_dispatch(self, attempt_id: str, *, edge_id: str, now: datetime | None = None) -> dict[str, Any] | None:
        """Atomically claim a queued attempt for dispatch under Central ownership."""
        await self.connect()
        current_time = now or datetime.now(timezone.utc)
        row = await self.pool.fetchrow(
            """UPDATE task_attempts
            SET status = 'DISPATCHING', started_at = $3
            WHERE attempt_id = $1
              AND edge_id = $2
              AND lease_owner = 'CENTRAL'
              AND status = 'QUEUED'
              AND (execution_status IS NULL OR execution_status = 'NOT_DISPATCHED')
              AND lease_expires_at >= $3
              AND deadline_at >= $3
            RETURNING *""",
            attempt_id, edge_id, current_time,
        )
        return dict(row) if row else None

    async def renew(self, attempt_id: str, *, edge_id: str, lease_seconds: int = 60, now: datetime | None = None) -> dict[str, Any] | None:
        await self.connect()
        current_time = now or datetime.now(timezone.utc)
        row = await self.pool.fetchrow(
            """UPDATE task_attempts
            SET heartbeat_at = $3,
                lease_expires_at = $3 + ($4 * INTERVAL '1 second')
            WHERE attempt_id = $1
              AND edge_id = $2
              AND lease_owner = 'CENTRAL'
              AND status IN ('QUEUED', 'DISPATCHING', 'RUNNING')
              AND lease_expires_at >= $3
              AND deadline_at >= $3
            RETURNING *""",
            attempt_id, edge_id, current_time, lease_seconds,
        )
        return dict(row) if row else None

    async def recover_expired(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        await self.connect()
        current_time = now or datetime.now(timezone.utc)
        rows = await self.pool.fetch(
            """UPDATE task_attempts
            SET status = 'UNKNOWN_EXECUTION_STATE', error_code = 'LEASE_EXPIRED_UNKNOWN_EXECUTION'
            WHERE status IN ('QUEUED', 'DISPATCHING', 'RUNNING')
              AND (lease_expires_at < $1 OR deadline_at < $1)
            RETURNING *""",
            current_time,
        )
        return [dict(row) for row in rows]
