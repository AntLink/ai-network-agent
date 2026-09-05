"""Ephemeral Edge session registry contract.

The in-memory implementation is suitable for M1 and tests. A Redis-backed
implementation can satisfy the same operations for multi-node HA without
changing the control endpoint contract.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Protocol


@dataclass
class EdgeSession:
    edge_id: str
    boot_id: str
    ready: bool = False
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_heartbeats: dict[str, datetime] = field(default_factory=dict)


class EdgeSessionRegistry(Protocol):
    async def create(self, *, edge_id: str, boot_id: str) -> str: ...
    async def get(self, session_id: str) -> EdgeSession | None: ...
    async def mark_ready(self, session_id: str) -> bool: ...
    async def touch_presence(self, session_id: str, *, edge_id: str, boot_id: str) -> bool: ...
    async def record_task_heartbeat(self, session_id: str, *, attempt_id: str, sent_at: datetime | None) -> bool: ...
    async def revoke_edge(self, edge_id: str) -> int: ...
    async def enqueue_task(self, edge_id: str, envelope: dict) -> bool: ...
    async def claim_task(self, session_id: str) -> dict | None: ...
    async def submit_task_result(self, session_id: str, attempt_id: str, result: dict) -> bool: ...
    async def wait_task_result(self, edge_id: str, attempt_id: str, timeout_seconds: int = 60) -> dict | None: ...


class InMemoryEdgeSessionRegistry:
    """Thread-safe M1 registry with an interface suitable for Redis later."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, EdgeSession] = {}
        self._tasks: dict[str, list[dict]] = {}
        self._results: dict[tuple[str, str], dict] = {}

    async def create(self, *, edge_id: str, boot_id: str) -> str:
        session_id = f"session-{secrets.token_urlsafe(18)}"
        with self._lock:
            self._sessions[session_id] = EdgeSession(edge_id=edge_id, boot_id=boot_id)
        return session_id

    async def get(self, session_id: str) -> EdgeSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    async def mark_ready(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.ready = True
            session.last_seen = datetime.now(timezone.utc)
            return True

    async def touch_presence(self, session_id: str, *, edge_id: str, boot_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or not session.ready or session.edge_id != edge_id or session.boot_id != boot_id:
                return False
            session.last_seen = datetime.now(timezone.utc)
            return True

    async def record_task_heartbeat(self, session_id: str, *, attempt_id: str, sent_at: datetime | None) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or not session.ready:
                return False
            now = datetime.now(timezone.utc)
            session.last_seen = now
            session.task_heartbeats[attempt_id] = sent_at or now
            return True

    async def revoke_edge(self, edge_id: str) -> int:
        with self._lock:
            session_ids = [session_id for session_id, session in self._sessions.items() if session.edge_id == edge_id]
            for session_id in session_ids:
                del self._sessions[session_id]
            return len(session_ids)

    async def enqueue_task(self, edge_id: str, envelope: dict) -> bool:
        with self._lock:
            if not any(s.edge_id == edge_id and s.ready for s in self._sessions.values()):
                return False
            self._tasks.setdefault(edge_id, []).append(dict(envelope))
            return True

    async def claim_task(self, session_id: str) -> dict | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or not session.ready:
                return None
            queue = self._tasks.get(session.edge_id, [])
            return queue.pop(0) if queue else None

    async def submit_task_result(self, session_id: str, attempt_id: str, result: dict) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or not session.ready:
                return False
            self._results[(session.edge_id, attempt_id)] = dict(result)
            return True

    async def wait_task_result(self, edge_id: str, attempt_id: str, timeout_seconds: int = 60) -> dict | None:
        import asyncio
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            with self._lock:
                result = self._results.pop((edge_id, attempt_id), None)
            if result is not None:
                return result
            await asyncio.sleep(0.1)
        return None


def build_edge_session_registry(*, backend: str, redis_url: str, ttl_seconds: int):
    normalized = backend.strip().lower()
    if normalized == "memory":
        return InMemoryEdgeSessionRegistry()
    if normalized == "redis":
        from app.services.redis_edge_sessions import RedisEdgeSessionRegistry

        return RedisEdgeSessionRegistry(redis_url, ttl_seconds=ttl_seconds)
    raise ValueError(f"unsupported Edge session backend: {backend}")
