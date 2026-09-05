"""Milestone 5: Redis connection resilience wrapper.

Wraps any `EdgeSessionRegistry` implementation with fail-closed behavior:
- Redis operational → delegate to the primary (Redis) registry.
- Redis connection fails → fall back to the in-memory registry and record the
  degradation. This prevents a Redis outage from crashing the control plane.
- Connection health is checked lazily on the next operation, not proactively.

Also provides a per-session heartbeat rate-limiter to enforce the heartbeat
interval returned by HELLO, preventing overload from misbehaving Edges.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from app.services.edge_sessions import EdgeSession, EdgeSessionRegistry

logger = logging.getLogger(__name__)


class _HeartbeatRateLimiter:
    """Per-session token-bucket-lite: reject heartbeats faster than the interval."""

    def __init__(self, min_interval: float = 15.0):
        self._min_interval = min_interval
        self._last: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def allow(self, session_id: str) -> bool:
        async with self._lock:
            now = time.monotonic()
            last = self._last.get(session_id)
            if last is not None and (now - last) < self._min_interval:
                return False
            self._last[session_id] = now
            return True


class ResilientEdgeSessionRegistry(EdgeSessionRegistry):
    """Wraps a primary registry with Redis-error resilience + heartbeat rate limiting.

    If any primary method raises (e.g. redis.exceptions.ConnectionError), the
    fallback in-memory registry is used transparently and the event is logged.
    """

    def __init__(
        self,
        primary: EdgeSessionRegistry,
        fallback: EdgeSessionRegistry,
        *,
        heartbeat_min_interval: float = 15.0,
    ):
        self._primary = primary
        self._fallback = fallback
        self._rate_limiter = _HeartbeatRateLimiter(min_interval=heartbeat_min_interval)
        self._redis_ok = True

    def _degraded(self, operation: str, err: BaseException) -> None:
        if self._redis_ok:
            logger.warning("Redis %s failed: %s — falling back to in-memory registry", operation, err)
            self._redis_ok = False

    def _promote(self) -> None:
        if not self._redis_ok:
            logger.info("Redis connection recovered; returning to primary registry")
            self._redis_ok = True

    def _call(self, method: str, fn: Any, fallback_fn: Any, *args: Any, **kwargs: Any) -> Any:
        if not self._redis_ok:
            return fallback_fn(*args, **kwargs)
        try:
            result = fn(*args, **kwargs)
            self._promote()
            return result
        except Exception as exc:
            self._degraded(method, exc)
            return fallback_fn(*args, **kwargs)

    async def _acall(self, method: str, fn: Any, fallback_fn: Any, *args: Any, **kwargs: Any) -> Any:
        if not self._redis_ok:
            return await fallback_fn(*args, **kwargs)
        try:
            result = await fn(*args, **kwargs)
            self._promote()
            return result
        except Exception as exc:
            self._degraded(method, exc)
            return await fallback_fn(*args, **kwargs)

    async def create(self, *, edge_id: str, boot_id: str) -> str:
        return await self._acall("create", self._primary.create, self._fallback.create, edge_id=edge_id, boot_id=boot_id)

    async def get(self, session_id: str) -> EdgeSession | None:
        return await self._acall("get", self._primary.get, self._fallback.get, session_id)

    async def mark_ready(self, session_id: str) -> None:
        await self._acall("mark_ready", self._primary.mark_ready, self._fallback.mark_ready, session_id)

    async def touch_presence(self, session_id: str, *, edge_id: str, boot_id: str) -> bool:
        return await self._acall("touch_presence", self._primary.touch_presence, self._fallback.touch_presence, session_id, edge_id=edge_id, boot_id=boot_id)

    async def record_task_heartbeat(self, session_id: str, *, attempt_id: str, sent_at: datetime | None) -> bool:
        # Rate-limit: reject heartbeats faster than the configured interval.
        if not await self._rate_limiter.allow(session_id):
            return False
        return await self._acall("record_task_heartbeat", self._primary.record_task_heartbeat, self._fallback.record_task_heartbeat, session_id, attempt_id=attempt_id, sent_at=sent_at)

    async def revoke_edge(self, edge_id: str) -> int:
        count_primary = await self._acall("revoke_edge_primary", self._primary.revoke_edge, lambda _: 0, edge_id)
        count_fallback = await self._acall("revoke_edge_fallback", self._fallback.revoke_edge, lambda _: 0, edge_id)
        return count_primary + count_fallback
