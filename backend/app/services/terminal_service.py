import asyncio
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.audit import log_event
from app.drivers.cisco.driver import IOSV_LEGACY_SSH_OPTIONS
from app.repositories.inventory import inventory_repository
from app.transports.ssh import SSHTransport


PROMPT_RE = re.compile(r"(?m)(?:^|\n)[^\r\n]*(?:[#>]\s?|[)\]]\s?>\s?)$")
CONTROL_U = "\x15"
CONTROL_C = "\x03"


class TerminalSessionError(Exception):
    pass


def _device_credentials(device: dict) -> tuple[str, str | None]:
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    return username, password


def _transport_for_device(device: dict) -> SSHTransport:
    username, password = _device_credentials(device)
    connect_options = IOSV_LEGACY_SSH_OPTIONS if (device.get("vendor") or "").lower() == "cisco" else {}
    port = int(device.get("management_port") or 22)
    return SSHTransport(
        device["management_address"],
        username,
        password,
        port=port,
        connect_options=connect_options,
    )


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", value)


def _split_lines(value: str) -> list[str]:
    cleaned = _strip_ansi(value).replace("--More--", "").replace("\x08", "").replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in cleaned.split("\n") if line.rstrip()]


@dataclass
class TerminalSession:
    session_id: str
    device: dict
    transport: SSHTransport
    conn: Any
    proc: Any
    prompt: str | None = None
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def device_id(self) -> str:
        return self.device["id"]

    @property
    def vendor(self) -> str:
        return (self.device.get("vendor") or "unknown").lower()

    def touch(self) -> None:
        self.last_active_at = time.time()


class TerminalSessionManager:
    def __init__(self):
        self._sessions: dict[str, TerminalSession] = {}
        self._manager_lock = asyncio.Lock()

    async def create(self, device_id: str) -> TerminalSession:
        device = inventory_repository.get_device(device_id)
        if not device:
            raise TerminalSessionError(f"Device '{device_id}' not found")
        if (device.get("transport") or "ssh").lower() != "ssh":
            raise TerminalSessionError("Interactive terminal session requires SSH transport")

        transport = _transport_for_device(device)
        conn = await transport._connect_resilient()
        try:
            proc = await conn.create_process(term_type="dumb", term_size=(160, 40))
            session_id = secrets.token_urlsafe(18)
            session = TerminalSession(session_id, device, transport, conn, proc)
            session.prompt = await self._bootstrap(session)
        except Exception:
            conn.close()
            raise

        async with self._manager_lock:
            self._sessions[session_id] = session

        log_event(device_id, "TERMINAL-SESSION", f"created session={session_id}", status="OK")
        return session

    async def get(self, session_id: str) -> TerminalSession:
        session = self._sessions.get(session_id)
        if not session:
            raise TerminalSessionError(f"Terminal session '{session_id}' not found")
        session.touch()
        return session

    async def close(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        await self._close_session(session)
        log_event(session.device_id, "TERMINAL-SESSION", f"closed session={session_id}", status="OK")

    async def list_sessions(self) -> list[dict]:
        return [self._public_session(session) for session in self._sessions.values()]

    async def execute(self, session_id: str, command: str) -> dict:
        session = await self.get(session_id)
        command = command.strip()
        if not command:
            raise TerminalSessionError("Command is required")

        async with session.lock:
            output = await self._send_and_read(session, f"{command}\n", max_wait=8.0)
            session.prompt = self._extract_prompt(output) or session.prompt

        log_event(session.device_id, "TERMINAL-EXEC", command, status="OK")
        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "command": command,
            "output": _split_lines(output),
            "raw": output,
            "prompt": session.prompt,
        }

    async def suggest(self, session_id: str, partial: str) -> dict:
        session = await self.get(session_id)
        if not partial.strip():
            partial = "?"

        if not partial.strip().replace("?", "") and partial.strip() != "?":
            return {
                "session_id": session.session_id,
                "device_id": session.device_id,
                "partial": partial,
                "suggestions": [],
                "raw": "",
                "source": "device",
            }

        helper = "\t" if session.vendor == "mikrotik" else "?"
        probe = self._normalize_probe(partial, session.vendor)

        async with session.lock:
            # Clear any unfinished CLI input, ask the device for contextual help,
            # then clear the probe so autocomplete cannot accidentally execute it.
            await self._send_and_read(session, CONTROL_C, max_wait=1.5)
            raw = await self._send_and_read(session, f"{CONTROL_U}{probe}{helper}", max_wait=10.0)
            if session.vendor == "mikrotik" and "MikroTik RouterOS" in raw and probe.strip() not in raw:
                raw = await self._send_and_read(session, f"{CONTROL_C}{CONTROL_U}{probe}{helper}", max_wait=10.0)
            await self._send_and_read(session, CONTROL_C, max_wait=1.5)

        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "partial": partial,
            "suggestions": self._parse_suggestions(raw, partial, session.vendor),
            "raw": raw,
            "source": "device",
        }

    async def raw_input(self, session_id: str, data: str) -> dict:
        session = await self.get(session_id)
        async with session.lock:
            output = await self._send_and_read(session, data, max_wait=2.0)
            session.prompt = self._extract_prompt(output) or session.prompt
        return {"type": "output", "session_id": session.session_id, "raw": output, "lines": _split_lines(output)}

    async def cleanup_idle(self, max_idle_seconds: int = 900) -> int:
        now = time.time()
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.last_active_at > max_idle_seconds
        ]
        for session_id in expired:
            await self.close(session_id)
        return len(expired)

    def _public_session(self, session: TerminalSession) -> dict:
        return {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "hostname": session.device.get("hostname"),
            "vendor": session.vendor,
            "management_address": session.device.get("management_address"),
            "prompt": session.prompt,
            "created_at": session.created_at,
            "last_active_at": session.last_active_at,
            "status": "connected",
        }

    async def _bootstrap(self, session: TerminalSession) -> str | None:
        output = await self._read_until_idle(session, max_wait=8.0, idle_wait=0.8)
        if session.vendor == "cisco":
            output += await self._send_and_read(session, "terminal length 0\n", max_wait=3.0)
            output += await self._send_and_read(session, "terminal width 0\n", max_wait=3.0)
        if session.vendor == "mikrotik":
            output += await self._send_and_read(session, "\n", max_wait=4.0)
        return self._extract_prompt(output)

    async def _send_and_read(self, session: TerminalSession, value: str, max_wait: float) -> str:
        session.proc.stdin.write(value)
        session.touch()
        return await self._read_until_idle(session, max_wait=max_wait)

    async def _read_until_idle(self, session: TerminalSession, max_wait: float = 3.0, idle_wait: float = 0.25) -> str:
        output = ""
        started = time.perf_counter()
        last_data = time.perf_counter()

        while time.perf_counter() - started < max_wait:
            try:
                chunk = await asyncio.wait_for(session.proc.stdout.read(4096), timeout=idle_wait)
            except asyncio.TimeoutError:
                if output and time.perf_counter() - last_data >= idle_wait:
                    break
                continue

            if not chunk:
                break
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8", errors="replace")
            output += chunk
            last_data = time.perf_counter()

            if "--More--" in _strip_ansi(chunk):
                session.proc.stdin.write(" ")
                continue

            if PROMPT_RE.search(_strip_ansi(output)) and time.perf_counter() - last_data >= idle_wait:
                break

        return output

    def _extract_prompt(self, output: str) -> str | None:
        lines = _split_lines(output)
        for line in reversed(lines):
            if line.endswith("#") or line.endswith(">"):
                return line.strip()
        return None

    def _parse_suggestions(self, raw: str, partial: str, vendor: str) -> list[dict]:
        lines = _split_lines(raw)
        partial_lower = partial.strip().lower().replace("?", "")
        suggestions: list[dict] = []
        seen: set[str] = set()

        for line in lines:
            clean = line.strip()
            if not clean or clean.lower() == partial_lower:
                continue
            if vendor == "mikrotik" and "] >" in clean:
                continue
            if vendor == "mikrotik" and (
                "MikroTik RouterOS" in clean
                or "https://www.mikrotik.com" in clean
                or clean.startswith("Press F1")
                or set(clean.replace(" ", "")) <= {"M", "K", "T", "I", "R", "O"}
            ):
                continue
            if clean.endswith("#") or clean.endswith(">"):
                continue
            if "% " in clean or clean.lower().startswith("invalid"):
                continue

            if vendor == "mikrotik":
                for token in re.split(r"\s{2,}|\s+", clean):
                    command = token.strip()
                    if not command or command in seen:
                        continue
                    seen.add(command)
                    suggestions.append({"value": command, "description": ""})
                continue

            command = clean
            description = ""
            if vendor == "cisco":
                match = re.match(r"^(\S+)\s{2,}(.+)$", clean)
                if match:
                    command, description = match.group(1), match.group(2)

            if command in seen:
                continue
            seen.add(command)
            suggestions.append({"value": command, "description": description})

        return suggestions[:500]

    def _normalize_probe(self, partial: str, vendor: str) -> str:
        value = partial.replace("?", "")
        if vendor != "mikrotik":
            return value

        stripped = value.strip()
        if not stripped:
            return value
        if stripped.startswith("/"):
            return value.rstrip() + (" " if not value.endswith(" ") else "")

        root_menus = {"interface", "ip", "routing", "system", "log", "tool", "user", "queue", "bridge"}
        first = stripped.split()[0]
        if first in root_menus:
            suffix = stripped[len(first):]
            probe = f"/{first}{suffix}"
            return probe.rstrip() + (" " if not probe.endswith(" ") else "")

        return value.rstrip()

    async def _close_session(self, session: TerminalSession) -> None:
        try:
            session.proc.stdin.write("exit\n")
            await asyncio.wait_for(session.proc.wait(), timeout=2)
        except Exception:
            pass
        finally:
            session.conn.close()


terminal_session_manager = TerminalSessionManager()
