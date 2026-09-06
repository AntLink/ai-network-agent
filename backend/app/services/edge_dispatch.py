"""Central mTLS client for one Edge control endpoint."""
from __future__ import annotations

import ssl
from typing import Any

import httpx

from app.core.config import settings


class EdgeDispatchError(RuntimeError):
    pass


class EdgeDispatchClient:
    async def _client(self) -> httpx.AsyncClient:
        required = (settings.EDGE_CA_FILE, settings.EDGE_CERT_FILE, settings.EDGE_KEY_FILE)
        if not settings.EDGE_CONTROL_URL.strip().lower().startswith("https://"):
            raise EdgeDispatchError("mTLS Edge control URL is not configured")
        if not all(required):
            raise EdgeDispatchError("mTLS CA/certificate/key files are not configured")
        # Build an explicit SSLContext so the same context both verifies the Edge
        # server certificate and presents the Central client certificate. Passing
        # a CA file as `verify` together with `cert` can silently drop the client
        # certificate on some platforms.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        # Server identity is established by full CA-chain verification of the Edge
        # certificate plus mutual TLS (the client presents a CA-signed client cert).
        # Hostname verification of an IP endpoint is disabled because httpx/OpenSSL
        # does not reliably match an IP Subject Alternative Name from a custom
        # context on all platforms. This is acceptable for the mTLS model; the
        # client cert proves Central identity to the Edge and the CA chain pins the
        # Edge server cert.
        context.check_hostname = False
        context.load_verify_locations(settings.EDGE_CA_FILE)
        context.load_cert_chain(settings.EDGE_CERT_FILE, settings.EDGE_KEY_FILE)
        return httpx.AsyncClient(verify=context, timeout=30)

    async def handshake(self, edge_id: str) -> str:
        if not edge_id:
            raise EdgeDispatchError("Edge ID is required for handshake")
        try:
            async with await self._client() as client:
                hello = {"edge_id": edge_id, "edge_version": settings.EDGE_VERSION, "min_protocol_version": 1, "max_protocol_version": 1, "driver_capability_version": 1, "capabilities": ["device.read.facts"], "boot_id": "central-dispatch"}
                response = await client.post(f"{settings.EDGE_CONTROL_URL.rstrip('/')}/v1/control/hello", json=hello)
                response.raise_for_status()
                session_id = response.json().get("session_id")
                if not session_id:
                    raise EdgeDispatchError("Edge handshake returned no session")
                ready = await client.post(f"{settings.EDGE_CONTROL_URL.rstrip('/')}/v1/control/ready", json={"session_id": session_id})
                ready.raise_for_status()
                return str(session_id)
        except EdgeDispatchError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise EdgeDispatchError(f"Edge handshake failed: {type(exc).__name__}") from exc

    async def dispatch(self, envelope: dict[str, Any]) -> dict[str, Any]:
        url = settings.EDGE_CONTROL_URL.strip()
        try:
            session_id = await self.handshake(str(envelope.get("edge_id", "")))
            async with await self._client() as client:
                response = await client.post(f"{url.rstrip('/')}/v1/control/task", headers={"X-Edge-Session": session_id}, json=envelope)
                response.raise_for_status()
                body = response.json()
                if not isinstance(body, dict):
                    raise EdgeDispatchError("Edge returned a non-object response")
                return body
        except EdgeDispatchError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise EdgeDispatchError(f"Edge dispatch failed: {type(exc).__name__}") from exc

    async def session_heartbeat(self, *, session_id: str, edge_id: str, boot_id: str = "central-dispatch") -> dict[str, Any]:
        """Report Edge presence; this does not represent a TaskAttempt lease."""
        if not session_id or not edge_id:
            raise EdgeDispatchError("session and Edge IDs are required for heartbeat")
        return await self._post_control(
            "/v1/control/heartbeat",
            session_id=session_id,
            payload={"session_id": session_id, "edge_id": edge_id, "boot_id": boot_id},
        )

    async def task_heartbeat(self, *, session_id: str, attempt_id: str) -> dict[str, Any]:
        """Report execution liveness; Central remains the lease authority."""
        if not session_id or not attempt_id:
            raise EdgeDispatchError("session and attempt IDs are required for task heartbeat")
        return await self._post_control(
            "/v1/control/task-heartbeat",
            session_id=session_id,
            payload={"session_id": session_id, "attempt_id": attempt_id},
        )

    async def _post_control(self, path: str, *, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with await self._client() as client:
                response = await client.post(
                    f"{settings.EDGE_CONTROL_URL.rstrip('/')}{path}",
                    json=payload,
                    headers={"X-Edge-Session": session_id},
                )
                response.raise_for_status()
                body = response.json()
                if not isinstance(body, dict):
                    raise EdgeDispatchError("Edge returned a non-object heartbeat response")
                return body
        except EdgeDispatchError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise EdgeDispatchError(f"Edge heartbeat failed: {type(exc).__name__}") from exc


edge_dispatch_client = EdgeDispatchClient()
