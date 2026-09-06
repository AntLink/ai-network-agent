"""Replaceable overlay control contract.

Business services depend on this interface, never on a vendor controller API.
The ZeroTier implementation is intentionally opt-in and requires an explicit
private controller URL/token; credentials are never included in errors.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class OverlayError(RuntimeError):
    pass


class OverlayProvider(Protocol):
    async def authorize_member(self, *, network_id: str, member_id: str) -> dict[str, Any]: ...
    async def revoke_member(self, *, network_id: str, member_id: str) -> dict[str, Any]: ...
    async def inspect_network(self, *, network_id: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ZeroTierProvider:
    """Minimal private-controller adapter; controller API is never browser-facing."""

    controller_url: str
    api_token: str
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if not self.controller_url or not self.api_token:
            raise ValueError("private overlay controller URL and token are required")

    async def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            async with httpx.AsyncClient(base_url=self.controller_url.rstrip("/"), timeout=self.timeout_seconds) as client:
                response = await client.request(method, path, headers=headers, json=json)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"data": data}
        except (httpx.HTTPError, ValueError) as exc:
            raise OverlayError(f"overlay controller request failed: {type(exc).__name__}") from exc

    async def authorize_member(self, *, network_id: str, member_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/network/{network_id}/member/{member_id}/authorize", json={"authorized": True})

    async def revoke_member(self, *, network_id: str, member_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/network/{network_id}/member/{member_id}/authorize", json={"authorized": False})

    async def inspect_network(self, *, network_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/network/{network_id}")


class NullOverlayProvider:
    """Explicitly unavailable provider used by development and tests."""

    async def authorize_member(self, **_: Any) -> dict[str, Any]:
        raise OverlayError("overlay provider is not configured")

    async def revoke_member(self, **_: Any) -> dict[str, Any]:
        raise OverlayError("overlay provider is not configured")

    async def inspect_network(self, **_: Any) -> dict[str, Any]:
        raise OverlayError("overlay provider is not configured")
