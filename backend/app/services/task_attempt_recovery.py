"""Periodic fail-safe TaskAttempt lease recovery."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any


class TaskAttemptRecoveryWorker:
    def __init__(self, store: Any, *, interval_seconds: float = 30.0, on_recovered: Callable[[dict[str, Any]], Awaitable[None] | None] | None = None) -> None:
        if interval_seconds <= 0:
            raise ValueError("recovery interval must be positive")
        self.store = store
        self.interval_seconds = interval_seconds
        self.on_recovered = on_recovered
        self._task: asyncio.Task[None] | None = None

    async def run_once(self) -> list[dict[str, Any]]:
        records = await self.store.recover_expired(now=datetime.now(timezone.utc))
        for record in records:
            if self.on_recovered is not None:
                result = self.on_recovered(record)
                if result is not None:
                    await result
        return records

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run(self) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(self.interval_seconds)
