import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.postgres_task_attempt_leases import PostgresTaskAttemptLeaseStore


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_POSTGRES") != "1",
    reason="live PostgreSQL test requires RUN_LIVE_POSTGRES=1",
)


@pytest.mark.asyncio
async def test_live_postgres_claim_is_single_owner():
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.fail("POSTGRES_DSN is required for live PostgreSQL test")
    store = PostgresTaskAttemptLeaseStore(dsn)
    attempt_id = f"live-{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    await store.create({
        "attempt_id": attempt_id,
        "task_id": f"task-{uuid.uuid4().hex}",
        "idempotency_key": f"idem-{uuid.uuid4().hex}",
        "edge_id": "edge-live",
        "status": "QUEUED",
        "retry_class": "SAFE_RETRY",
        "accepted_at": now,
        "deadline_at": now + timedelta(minutes=5),
        "lease_expires_at": now + timedelta(minutes=5),
        "execution_status": "NOT_DISPATCHED",
    })
    try:
        claims = await asyncio.gather(
            store.claim_for_dispatch(attempt_id, edge_id="edge-live", now=now),
            store.claim_for_dispatch(attempt_id, edge_id="edge-live", now=now),
        )
        assert sum(claim is not None for claim in claims) == 1
    finally:
        await store.pool.execute("DELETE FROM task_attempts WHERE attempt_id = $1", attempt_id)
        await store.close()


@pytest.mark.asyncio
async def test_live_postgres_renewal_and_expiry_recovery():
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.fail("POSTGRES_DSN is required for live PostgreSQL test")
    store = PostgresTaskAttemptLeaseStore(dsn)
    now = datetime.now(timezone.utc)
    renew_id = f"live-renew-{uuid.uuid4().hex}"
    expired_id = f"live-expired-{uuid.uuid4().hex}"
    records = [
        {
            "attempt_id": renew_id,
            "task_id": f"task-{uuid.uuid4().hex}",
            "idempotency_key": f"idem-{uuid.uuid4().hex}",
            "edge_id": "edge-live",
            "status": "RUNNING",
            "retry_class": "SAFE_RETRY",
            "accepted_at": now,
            "deadline_at": now + timedelta(minutes=5),
            "lease_expires_at": now + timedelta(seconds=5),
            "execution_status": "DISPATCHED",
        },
        {
            "attempt_id": expired_id,
            "task_id": f"task-{uuid.uuid4().hex}",
            "idempotency_key": f"idem-{uuid.uuid4().hex}",
            "edge_id": "edge-live",
            "status": "RUNNING",
            "retry_class": "SAFE_RETRY",
            "accepted_at": now - timedelta(minutes=2),
            "deadline_at": now + timedelta(minutes=5),
            "lease_expires_at": now - timedelta(seconds=1),
            "execution_status": "DISPATCHED",
        },
    ]
    try:
        for record in records:
            await store.create(record)
        renewed = await store.renew(renew_id, edge_id="edge-live", lease_seconds=60, now=now)
        assert renewed is not None
        assert renewed["heartbeat_at"] == now
        assert renewed["lease_expires_at"] > now

        recovered = await store.recover_expired(now=now)
        recovered_ids = {row["attempt_id"] for row in recovered}
        assert expired_id in recovered_ids
        assert (await store.get(expired_id))["status"] == "UNKNOWN_EXECUTION_STATE"
    finally:
        await store.pool.execute("DELETE FROM task_attempts WHERE attempt_id = ANY($1::text[])", [renew_id, expired_id])
        await store.close()
