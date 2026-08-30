"""Fortinet FortiOS driver (GNS3 FG1-FORTI, console)."""
import asyncio
import os
import re
import time

from app.core.audit import log_event
from app.drivers.base import BaseDriver
from app.drivers.fortinet.parser import FortiOSParser
from app.transports.console import ConsoleTransport

_DEVICE_LOCKS: dict[tuple[int, str], asyncio.Lock] = {}


def _device_lock(device_id: str) -> asyncio.Lock:
    key = (id(asyncio.get_running_loop()), device_id)
    lock = _DEVICE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _DEVICE_LOCKS[key] = lock
    return lock


class FortiOSDriver(BaseDriver):
    """Async FortiOS driver over telnet console."""

    @property
    def _prefer_console(self) -> bool:
        return (self.device.get("transport") or "").lower() in ("console", "telnet")

    def _credentials(self):
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
        return username, password

    def _console_transport(self) -> ConsoleTransport:
        host = self.device.get("console_host") or self.device.get("management_address", "").split("/")[0]
        port = int(self.device.get("console_port") or 5004)
        username, password = self._credentials()
        return ConsoleTransport(
            host,
            port,
            username=username,
            password=password,
            device_id=self.device["id"],
        )

    async def _logged(self, action: str, detail: str, fn):
        device_id = self.device["id"]
        t0 = time.perf_counter()
        try:
            out = await fn()
            log_event(device_id, action, detail, status="OK",
                      duration_ms=round((time.perf_counter() - t0) * 1000))
            return out
        except Exception as e:
            log_event(device_id, action, detail, status="FAIL", error=str(e),
                      duration_ms=round((time.perf_counter() - t0) * 1000))
            raise

    async def exec_logged(self, command: str) -> str:
        return await self._logged("EXEC", command, lambda: self._exec(command))

    async def _exec(self, command: str) -> str:
        async with _device_lock(self.device["id"]):
            # FortiOS console interplay can (rarely) drop the first command's
            # output for a fresh session; retry a couple of times before giving
            # up so the agent never sees an empty read.
            for attempt in range(6):
                con = self._console_transport()
                out = (await con.run(command)).strip()
                if out:
                    return out
                await asyncio.sleep(0.5)
            return ""

    async def identify(self):
        raw = await self.exec_logged("get system status")
        return {"vendor": "fortinet", "platform": "fortios",
                "data": FortiOSParser.parse_version(raw), "raw": raw}

    async def get_facts(self):
        raw = await self.exec_logged("get system status")
        return {"data": FortiOSParser.parse_version(raw), "raw": raw}

    async def get_interfaces(self):
        raw = await self.exec_logged("get system interface")
        return {"data": FortiOSParser.parse_interfaces(raw), "raw": raw}

    async def get_routes(self):
        raw = await self.exec_logged("get router info routing-table all")
        return {"data": FortiOSParser.parse_routes(raw), "raw": raw}

    async def get_config(self):
        raw = await self.exec_logged("show full-configuration")
        return {"data": raw, "raw": raw}

    async def backup(self):
        raw = await self.exec_logged("show full-configuration")
        return {"data": raw, "raw": raw}

    async def apply(self, commands: list[str]):
        """Apply FortiOS `config ...` lines in one session (no `configure terminal`)."""
        out = await self._config_fortios(commands)
        return {"success": True, "outputs": [out]}

    async def _drain_fortios(self, proc, max_wait=25.0):
        buf = ""
        started = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - started < max_wait:
            piece = ""
            try:
                piece = await asyncio.wait_for(proc.stdout.read(4096), timeout=0.8)
            except Exception:
                pass
            if piece:
                buf += piece
                if "--More--" in buf:
                    proc.stdin.write(" ")
                    buf = buf.replace("--More--", "")
            if re.search(r"#\s*$", buf):
                break
        return buf

    async def _config_fortios(self, lines: list[str]) -> str:
        async with _device_lock(self.device["id"]):
            con = self._console_transport()
            outputs: list[str] = []
            async with con.interactive() as proc:
                await self._drain_fortios(proc)
                for line in lines:
                    proc.stdin.write(line + "\n")
                    out = await self._drain_fortios(proc)
                    if "command fail" in out.lower() or "parse error" in out.lower():
                        raise RuntimeError(f"FortiOS config failed at '{line}': {out[-240:]}")
                    outputs.append(out.strip())
            return "\n".join(outputs)

    async def set_hostname(self, name: str):
        out = await self._config_fortios([
            "config system global",
            f"set hostname {name}",
            "end",
        ])
        return {"status": "applied", "output": out}

    async def set_interface_address(self, interface: str, address: str):
        if "/" in address:
            ip, mask = address.split("/", 1)
            mask = ".".join(str(((0xFFFFFFFF << (32 - int(mask))) >> shift) & 0xFF) for shift in (24, 16, 8, 0))
        else:
            parts = address.split()
            if len(parts) != 2:
                raise ValueError("address must be CIDR (a.b.c.d/nn) or 'a.b.c.d mask'")
            ip, mask = parts
        out = await self._config_fortios([
            "config system interface",
            f"edit {interface}",
            "set mode static",
            f"set ip {ip} {mask}",
            "set status up",
            "next",
            "end",
        ])
        return {"status": "applied", "output": out}

    async def remove_interface_address(self, interface: str):
        out = await self._config_fortios([
            "config system interface",
            f"edit {interface}",
            "set mode dhcp",
            "set ip 0.0.0.0 0.0.0.0",
            "next",
            "end",
        ])
        return {"status": "applied", "output": out}

    async def get_static_routes(self):
        raw = await self.exec_logged("show router static")
        return {"data": FortiOSParser.parse_static_routes(raw), "raw": raw}

    async def add_static_route(self, prefix: str, gateway: str, interface: str = "port1"):
        if "/" in prefix:
            net, mask = prefix.split("/", 1)
            mask = ".".join(str(((0xFFFFFFFF << (32 - int(mask))) >> shift) & 0xFF) for shift in (24, 16, 8, 0))
        else:
            parts = prefix.split()
            if len(parts) != 2:
                raise ValueError("prefix must be CIDR (a.b.c.d/nn) or 'a.b.c.d mask'")
            net, mask = parts
        out = await self._config_fortios([
            "config router static",
            "edit 0",
            f"set dst {net} {mask}",
            f"set gateway {gateway}",
            f"set device {interface}",
            "next",
            "end",
        ])
        return {"status": "applied", "output": out}

    async def delete_static_route(self, route_id: int):
        out = await self._config_fortios([
            "config router static",
            f"delete {int(route_id)}",
            "end",
        ])
        return {"status": "applied", "output": out}

    async def health(self):
        result = {"device_id": self.device["id"]}
        host = self.device.get("console_host") or self.device.get("management_address", "").split("/")[0]
        port = int(self.device.get("console_port") or (self.device.get("management_port") or 22))
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3.0)
            writer.close()
            raw = await self.exec_logged("get system status")
            result.update(reachable=True, data=FortiOSParser.parse_version(raw))
        except Exception as e:
            result.update(reachable=False, reason=str(e))
        return result