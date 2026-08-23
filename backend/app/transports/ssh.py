import asyncio
import time
from contextlib import asynccontextmanager

import asyncssh

from app.core.config import settings


class SSHTransportError(Exception):
    """Base exception for SSH transport errors."""
    pass


class SSHConnectError(SSHTransportError):
    """SSH connection/authentication failed."""
    pass


class SSHTimeoutError(SSHTransportError):
    """Operation timed out."""
    pass


class PromptTimeoutError(SSHTransportError):
    """CLI prompt not detected within timeout."""
    pass


# Old IOS images (15.x and earlier) only speak legacy algorithms.
# Modern servers reject these, so they are used ONLY as a fallback retry
# after a normal negotiation fails. Learned from GNS3 lab 2026-08-23.
LEGACY_SSH_OPTIONS = {
    "kex_algs": ["diffie-hellman-group14-sha1", "diffie-hellman-group1-sha1"],
    "server_host_key_algs": ["ssh-rsa"],
    "encryption_algs": ["aes128-cbc", "aes256-cbc", "aes128-ctr", "aes256-ctr"],
    "mac_algs": ["hmac-sha1"],
}


class SSHTransport:
    """Vendor-neutral SSH transport.

    Handles connections, exec requests, interactive sessions and deadlines.
    All vendor-specific prompt/error parsing belongs in the drivers.

    If the initial connection fails at algorithm-negotiation level, one
    automatic retry is made with legacy (old-IOS) algorithm sets.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str | None = None,
        client_keys=None,
        port: int = 22,
        connect_options: dict | None = None,
        legacy_fallback: bool = True,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.client_keys = client_keys
        self.port = port
        self.connect_options = connect_options or {}
        self.legacy_fallback = legacy_fallback

    def _connect(self):
        return asyncssh.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            client_keys=self.client_keys,
            known_hosts=None,
            connect_timeout=settings.SSH_CONNECT_TIMEOUT,
            **self.connect_options,
        )

    async def _connect_resilient(self):
        """Connect with configured options; on failure retry once with
        legacy algorithm sets merged in (old Cisco IOS images)."""
        try:
            return await self._connect()
        except asyncio.TimeoutError:
            raise
        except Exception:
            if not self.legacy_fallback:
                raise
            merged = dict(self.connect_options)
            for key, values in LEGACY_SSH_OPTIONS.items():
                # caller-supplied lists win; append legacy as extra options
                existing = merged.get(key)
                if isinstance(existing, list):
                    merged[key] = list(existing) + [
                        v for v in values if v not in existing
                    ]
                else:
                    merged[key] = list(values)
            return await asyncssh.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                client_keys=self.client_keys,
                known_hosts=None,
                connect_timeout=settings.SSH_CONNECT_TIMEOUT,
                **merged,
            )

    async def _with_deadline(self, coro, what: str):
        """Fail fast: abort the whole operation if it exceeds the timeout."""
        try:
            return await asyncio.wait_for(
                coro,
                timeout=settings.SSH_COMMAND_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise SSHTimeoutError(
                f"SSH operation timed out after "
                f"{settings.SSH_COMMAND_TIMEOUT}s: {what}"
            )

    async def drain_until(
        self,
        reader,
        prompt_re,
        max_wait: float = 5.0,
    ) -> str:
        """Read until output matches a vendor-supplied prompt regex.

        Raises PromptTimeoutError if prompt not detected within max_wait.
        """
        buf = ""
        started = time.perf_counter()

        while time.perf_counter() - started < max_wait:
            try:
                piece = await asyncio.wait_for(
                    reader.read(4096),
                    timeout=0.3,
                )
            except asyncio.TimeoutError:
                if prompt_re.search(buf):
                    return buf
                continue

            if not piece:
                if prompt_re.search(buf):
                    return buf
                break

            if isinstance(piece, bytes):
                piece = piece.decode("utf-8", errors="replace")

            buf += piece

            if prompt_re.search(buf):
                return buf

        raise PromptTimeoutError(
            f"CLI prompt not detected within {max_wait}s"
        )

    async def run(self, command: str) -> str:
        """Single exec request over a fresh connection. Raw stdout."""

        async def _do() -> str:
            async with await self._connect_resilient() as conn:
                result = await conn.run(command, check=False)

                if result.exit_status not in (0, None):
                    raise RuntimeError(
                        result.stderr.strip()
                        or f"Command failed: {result.exit_status}"
                    )

                output = result.stdout or ""

                if isinstance(output, bytes):
                    output = output.decode("utf-8", errors="replace")

                return output

        return await self._with_deadline(
            _do(),
            command.splitlines()[0],
        )

    @asynccontextmanager
    async def interactive(self, term_size: tuple[int, int] = (511, 24)):
        """Open a long-lived interactive CLI session as async context manager.

        Yields (proc) where proc has stdin/stdout for prompt-driven I/O.
        Connection lifecycle is handled automatically.
        """
        conn = await self._connect_resilient()
        try:
            proc = await conn.create_process(
                term_type="dumb",
                term_size=term_size,
            )
        except Exception:
            conn.close()
            raise
        try:
            yield proc
        finally:
            try:
                proc.stdin.write("exit\n")
                await asyncio.wait_for(proc.wait(), timeout=3)
            except Exception:
                pass
            finally:
                conn.close()