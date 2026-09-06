import os

import pytest

from app.services.redis_edge_sessions import RedisEdgeSessionRegistry


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_REDIS") != "1",
    reason="live Redis test requires RUN_LIVE_REDIS=1",
)


@pytest.mark.asyncio
async def test_live_redis_edge_session_lifecycle():
    registry = RedisEdgeSessionRegistry(
        os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
        ttl_seconds=60,
        prefix="ainet:live-test",
    )
    session_id = await registry.create(edge_id="edge-live-test", boot_id="boot-live-test")
    try:
        assert await registry.get(session_id)
        assert await registry.mark_ready(session_id)
        current = await registry.get(session_id)
        assert current is not None and current.ready
        assert await registry.revoke_edge("edge-live-test") == 1
        assert await registry.get(session_id) is None
    finally:
        await registry.client.aclose()
