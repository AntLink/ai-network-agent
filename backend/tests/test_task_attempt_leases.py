import asyncio
from datetime import datetime, timedelta, timezone

from app.services.task_attempt_leases import TaskAttemptLeaseStore
from app.services.postgres_task_attempt_leases import PostgresTaskAttemptLeaseStore
from app.services.task_attempt_recovery import TaskAttemptRecoveryWorker


def test_lease_renewal_keeps_deadline_separate_and_requires_edge_owner():
    store = TaskAttemptLeaseStore()
    now = datetime.now(timezone.utc)
    asyncio.run(store.create(
        "attempt-1",
        {
            "task_id": "task-1",
            "edge_id": "edge-1",
            "status": "RUNNING",
            "deadline_at": (now + timedelta(minutes=5)).isoformat(),
            "lease_expires_at": (now + timedelta(seconds=30)).isoformat(),
        },
    ))
    renewed = asyncio.run(store.renew("attempt-1", edge_id="edge-1", now=now, lease_seconds=60))
    assert renewed is not None
    assert renewed["deadline_at"] != renewed["lease_expires_at"]
    assert renewed["heartbeat_at"] == now.isoformat()
    assert asyncio.run(store.renew("attempt-1", edge_id="other-edge", now=now)) is None


def test_expired_lease_cannot_be_renewed():
    store = TaskAttemptLeaseStore()
    now = datetime.now(timezone.utc)
    asyncio.run(store.create("attempt-2", {"edge_id": "edge-1", "status": "RUNNING", "lease_expires_at": (now - timedelta(seconds=1)).isoformat()}))
    assert asyncio.run(store.renew("attempt-2", edge_id="edge-1", now=now)) is None


def test_postgres_store_fails_closed_without_dsn():
    try:
        PostgresTaskAttemptLeaseStore("")
    except ValueError as exc:
        assert "DSN" in str(exc)
    else:
        raise AssertionError("empty PostgreSQL DSN must be rejected")


def test_expiry_recovery_fences_attempt_without_replay():
    async def run():
        store = TaskAttemptLeaseStore()
        now = datetime.now(timezone.utc)
        await store.create("attempt-3", {"edge_id": "edge-1", "status": "RUNNING", "lease_expires_at": (now - timedelta(seconds=1)).isoformat()})
        recovered = await store.recover_expired(now=now)
        assert len(recovered) == 1
        assert recovered[0]["status"] == "UNKNOWN_EXECUTION_STATE"
        assert recovered[0]["error_code"] == "LEASE_EXPIRED_UNKNOWN_EXECUTION"
        assert await store.renew("attempt-3", edge_id="edge-1", now=now) is None

    asyncio.run(run())


def test_recovery_worker_runs_once_and_emits_fenced_record():
    async def run():
        store = TaskAttemptLeaseStore()
        now = datetime.now(timezone.utc)
        await store.create("attempt-worker", {"task_id": "task-worker", "edge_id": "edge-1", "status": "RUNNING", "lease_expires_at": (now - timedelta(seconds=1)).isoformat()})
        observed = []
        worker = TaskAttemptRecoveryWorker(store, on_recovered=lambda record: observed.append(record))
        records = await worker.run_once()
        assert len(records) == 1
        assert observed[0]["status"] == "UNKNOWN_EXECUTION_STATE"

    asyncio.run(run())


def test_duplicate_idempotency_key_is_rejected():
    async def run():
        store = TaskAttemptLeaseStore()
        values = {
            "task_id": "task-idempotency",
            "edge_id": "edge-1",
            "status": "QUEUED",
            "retry_class": "SAFE_RETRY",
            "idempotency_key": "same-operation",
            "lease_expires_at": "2099-01-01T00:00:00+00:00",
        }
        await store.create("attempt-one", values)
        try:
            await store.create("attempt-two", values)
        except ValueError as exc:
            return str(exc)
        return None

    assert asyncio.run(run()) == "idempotency key already exists"


def test_dispatch_claim_is_atomic_and_single_use():
    async def run():
        store = TaskAttemptLeaseStore()
        now = datetime.now(timezone.utc)
        await store.create("attempt-claim", {
            "task_id": "task-claim",
            "edge_id": "edge-1",
            "status": "QUEUED",
            "execution_status": "NOT_DISPATCHED",
            "deadline_at": (now + timedelta(minutes=5)).isoformat(),
            "lease_expires_at": (now + timedelta(seconds=60)).isoformat(),
        })
        claimed = await store.claim_for_dispatch("attempt-claim", edge_id="edge-1", now=now)
        assert claimed is not None
        assert claimed["status"] == "DISPATCHING"
        assert claimed["started_at"] == now.isoformat()
        assert await store.claim_for_dispatch("attempt-claim", edge_id="edge-1", now=now) is None

    asyncio.run(run())
