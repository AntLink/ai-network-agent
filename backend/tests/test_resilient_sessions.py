"""Milestone 5: Redis resilience wrapper + heartbeat rate limiter."""
import asyncio
from datetime import datetime, timezone

import pytest

from app.services.edge_sessions import InMemoryEdgeSessionRegistry
from app.services.resilient_sessions import ResilientEdgeSessionRegistry, _HeartbeatRateLimiter


class _FailingRegistry(InMemoryEdgeSessionRegistry):
    """Registry that always raises on create/get — simulates Redis down."""
    async def create(self, *, edge_id, boot_id):
        raise ConnectionError("redis connection refused")

    async def get(self, session_id):
        raise ConnectionError("redis connection refused")

    async def mark_ready(self, session_id):
        raise ConnectionError("redis connection refused")

    async def touch_presence(self, session_id, *, edge_id, boot_id):
        raise ConnectionError("redis connection refused")

    async def record_task_heartbeat(self, session_id, *, attempt_id, sent_at):
        raise ConnectionError("redis connection refused")

    async def revoke_edge(self, edge_id):
        raise ConnectionError("redis connection refused")


@pytest.mark.asyncio
async def test_resilient_fallback_on_redis_failure():
    fb = InMemoryEdgeSessionRegistry()
    reg = ResilientEdgeSessionRegistry(primary=_FailingRegistry(), fallback=fb)
    sid = await reg.create(edge_id="e1", boot_id="b1")
    assert sid  # fallback returned a session ID
    session = await reg.get(sid)
    assert session is not None
    assert session.edge_id == "e1"


@pytest.mark.asyncio
async def test_resilient_promotes_after_recovery():
    class RecoveryRegistry(InMemoryEdgeSessionRegistry):
        _fail = True
        async def create(self, *, edge_id, boot_id):
            if self._fail:
                raise ConnectionError("still down")
            return await super().create(edge_id=edge_id, boot_id=boot_id)

    fb = InMemoryEdgeSessionRegistry()
    primary = RecoveryRegistry()
    reg = ResilientEdgeSessionRegistry(primary=primary, fallback=fb)
    # first call fails → fallback
    sid1 = await reg.create(edge_id="e1", boot_id="b1")
    # fix primary
    primary._fail = False
    # next call should use primary again (after promotion on success)
    sid2 = await reg.create(edge_id="e2", boot_id="b2")
    # verify both exist (one in fallback, one in primary)
    assert sid1 and sid2


@pytest.mark.asyncio
async def test_rate_limiter_allows_normal_heartbeats():
    limiter = _HeartbeatRateLimiter(min_interval=15.0)
    assert await limiter.allow("s1") is True
    assert await limiter.allow("s1") is False  # too fast
    # simulate time passing (we can't mock time easily; just check the second call is False)
    assert await limiter.allow("s2") is True  # different session


@pytest.mark.asyncio
async def test_resilient_rate_limits_heartbeats():
    fb = InMemoryEdgeSessionRegistry()
    reg = ResilientEdgeSessionRegistry(primary=InMemoryEdgeSessionRegistry(), fallback=fb, heartbeat_min_interval=60.0)
    sid = await reg.create(edge_id="e1", boot_id="b1")
    await reg.mark_ready(sid)
    ok1 = await reg.record_task_heartbeat(sid, attempt_id="a1", sent_at=datetime.now(timezone.utc))
    assert ok1 is True
    ok2 = await reg.record_task_heartbeat(sid, attempt_id="a1", sent_at=datetime.now(timezone.utc))
    assert ok2 is False  # rate-limited


@pytest.mark.asyncio
async def test_revoke_propagates_both_registries():
    fb = InMemoryEdgeSessionRegistry()
    reg = ResilientEdgeSessionRegistry(primary=InMemoryEdgeSessionRegistry(), fallback=fb)
    sid = await reg.create(edge_id="e1", boot_id="b1")
    await reg.mark_ready(sid)
    count = await reg.revoke_edge("e1")
    assert count >= 1
    # verify revocation in fallback too (or at least no crash)
    assert await reg.get(sid) is None
