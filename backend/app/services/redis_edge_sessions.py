"""Redis implementation of the Central Edge session registry contract."""
from __future__ import annotations

from datetime import datetime, timezone
import asyncio
from typing import Any
import json

from app.services.edge_sessions import EdgeSession


class RedisEdgeSessionRegistry:
    def __init__(self, redis_url: str, *, ttl_seconds: int = 60, prefix: str = "ainet:edge-session") -> None:
        if not redis_url:
            raise ValueError("redis_url is required")
        if ttl_seconds < 15:
            raise ValueError("session TTL must be at least 15 seconds")
        try:
            from redis import asyncio as redis_asyncio
        except ImportError as exc:
            raise RuntimeError("redis package is required for Redis session registry") from exc
        self.client: Any = redis_asyncio.from_url(redis_url, decode_responses=True)
        self.redis_url = redis_url
        self._redis_asyncio = redis_asyncio
        self._loop_id: int | None = None
        self.ttl_seconds = ttl_seconds
        self.prefix = prefix.rstrip(":")

    async def _client_for_loop(self) -> Any:
        """Keep the lazy Redis pool bound to the active event loop.

        This matters for TestClient and short-lived worker loops; reusing an
        asyncio Redis pool from a closed loop raises ``Event loop is closed``.
        Long-lived ASGI workers normally take the fast path.
        """
        loop_id = id(asyncio.get_running_loop())
        if self._loop_id != loop_id:
            try:
                await self.client.aclose()
            except Exception:
                pass
            self.client = self._redis_asyncio.from_url(self.redis_url, decode_responses=True)
            self._loop_id = loop_id
        return self.client

    def _session_key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"

    def _task_key(self, session_id: str) -> str:
        return f"{self._session_key(session_id)}:tasks"

    def _queue_key(self, edge_id: str) -> str:
        return f"{self.prefix}:queue:{edge_id}"

    def _result_key(self, edge_id: str, attempt_id: str) -> str:
        return f"{self.prefix}:result:{edge_id}:{attempt_id}"

    async def create(self, *, edge_id: str, boot_id: str) -> str:
        import secrets

        session_id = f"session-{secrets.token_urlsafe(18)}"
        now = datetime.now(timezone.utc).isoformat()
        client = await self._client_for_loop()
        await client.hset(self._session_key(session_id), mapping={"edge_id": edge_id, "boot_id": boot_id, "ready": "0", "last_seen": now})
        await client.expire(self._session_key(session_id), self.ttl_seconds)
        return session_id

    async def get(self, session_id: str) -> EdgeSession | None:
        client = await self._client_for_loop()
        data = await client.hgetall(self._session_key(session_id))
        if not data:
            return None
        return EdgeSession(edge_id=str(data["edge_id"]), boot_id=str(data["boot_id"]), ready=data.get("ready") == "1", last_seen=datetime.fromisoformat(str(data["last_seen"])))

    async def mark_ready(self, session_id: str) -> bool:
        key = self._session_key(session_id)
        client = await self._client_for_loop()
        if not await client.exists(key):
            return False
        await client.hset(key, mapping={"ready": "1", "last_seen": datetime.now(timezone.utc).isoformat()})
        await client.expire(key, self.ttl_seconds)
        return True

    async def touch_presence(self, session_id: str, *, edge_id: str, boot_id: str) -> bool:
        key = self._session_key(session_id)
        client = await self._client_for_loop()
        data = await client.hgetall(key)
        if not data or data.get("ready") != "1" or data.get("edge_id") != edge_id or data.get("boot_id") != boot_id:
            return False
        await client.hset(key, "last_seen", datetime.now(timezone.utc).isoformat())
        await client.expire(key, self.ttl_seconds)
        return True

    async def record_task_heartbeat(self, session_id: str, *, attempt_id: str, sent_at: datetime | None) -> bool:
        key = self._session_key(session_id)
        client = await self._client_for_loop()
        data = await client.hgetall(key)
        if not data or data.get("ready") != "1":
            return False
        now = datetime.now(timezone.utc)
        await client.hset(key, "last_seen", now.isoformat())
        await client.expire(key, self.ttl_seconds)
        task_key = self._task_key(session_id)
        await client.hset(task_key, attempt_id, (sent_at or now).isoformat())
        await client.expire(task_key, self.ttl_seconds)
        return True

    async def revoke_edge(self, edge_id: str) -> int:
        removed = 0
        client = await self._client_for_loop()
        async for key in client.scan_iter(match=f"{self.prefix}:*"):
            if str(key).endswith(":tasks"):
                continue
            data = await client.hgetall(key)
            if data.get("edge_id") == edge_id:
                task_key = f"{key}:tasks"
                removed += int(await client.delete(key, task_key) > 0)
        return removed

    async def enqueue_task(self, edge_id: str, envelope: dict) -> bool:
        client = await self._client_for_loop()
        ready = False
        async for key in client.scan_iter(match=f"{self.prefix}:session-*"):
            data = await client.hgetall(key)
            if data.get("edge_id") == edge_id and data.get("ready") == "1":
                ready = True
                break
        if not ready:
            return False
        await client.rpush(self._queue_key(edge_id), json.dumps(envelope, separators=(",", ":")))
        await client.expire(self._queue_key(edge_id), self.ttl_seconds)
        return True

    async def claim_task(self, session_id: str) -> dict | None:
        session = await self.get(session_id)
        if session is None or not session.ready:
            return None
        client = await self._client_for_loop()
        raw = await client.lpop(self._queue_key(session.edge_id))
        return json.loads(raw) if raw else None

    async def submit_task_result(self, session_id: str, attempt_id: str, result: dict) -> bool:
        session = await self.get(session_id)
        if session is None or not session.ready:
            return False
        client = await self._client_for_loop()
        key = self._result_key(session.edge_id, attempt_id)
        await client.set(key, json.dumps(result, separators=(",", ":")), ex=self.ttl_seconds)
        return True

    async def wait_task_result(self, edge_id: str, attempt_id: str, timeout_seconds: int = 60) -> dict | None:
        client = await self._client_for_loop()
        key = self._result_key(edge_id, attempt_id)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            raw = await client.get(key)
            if raw:
                await client.delete(key)
                return json.loads(raw)
            await asyncio.sleep(0.1)
        return None
