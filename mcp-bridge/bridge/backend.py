"""Async HTTP client for the ai-network-agent FastAPI backend."""
from __future__ import annotations

import httpx

from . import config


class BackendError(RuntimeError):
    """Raised when the FastAPI backend returns an error response."""

    def __init__(self, status: int, method: str, path: str, detail: str):
        self.status = status
        self.method = method
        self.path = path
        super().__init__(f"{method} {path} -> HTTP {status}: {detail[:400]}")


class Backend:
    """Thin wrapper around the backend REST API."""

    def __init__(self):
        self._base = f"{config.BACKEND_URL}{config.API_V1_PREFIX}"
        self._timeout = config.REQUEST_TIMEOUT
        self._token = config.API_TOKEN

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"{self._base}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise BackendError(0, method, path, f"connection failed: {exc}") from exc

        if resp.status_code >= 400:
            raise BackendError(resp.status_code, method, path, resp.text)
        return resp.json()

    async def get(self, path: str, **kw) -> dict:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw) -> dict:
        return await self.request("POST", path, **kw)

    async def health(self) -> dict:
        """Hit the backend root /health (outside the v1 prefix)."""
        url = f"{config.BACKEND_URL}/health"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers())
        return resp.json()


backend = Backend()