"""Ruijie RGOS driver (RG-NSE Router / Switch V1.06).

RGOS is Cisco-IOS-like over the Telnet/SSh console. Pager disabled with
`terminal length 0`; `enable` on the console has no password; config mode is
`configure terminal`.
"""
import asyncio
import re
import time

from app.core.audit import log_event
from app.drivers.base import BaseDriver
from app.drivers.ruijie.base import get_credentials
from app.drivers.ruijie.parser import RuijieParser
from app.transports.ssh import SSHTransport
from app.transports.console import ConsoleTransport

_DEVICE_LOCKS: dict[tuple[int, str], asyncio.Lock] = {}

_RUIJIE_ERROR_RE = re.compile(
    r"(?im)(Invalid input|Incomplete command|Ambiguous command|"
    r"Unknown command|Unrecognized command|%( )?Error|%( )?Failed|Not a valid)"
)


def raise_for_ruijie_error(output: str, command: str) -> None:
    if not output or not _RUIJIE_ERROR_RE.search(output):
        return
    detail = "\n".join(
        line.strip() for line in output.splitlines() if line.strip().startswith("%") or line.strip() == "^"
    ).strip() or output.strip()
    raise RuntimeError(f"RGOS command failed: {command}\n{detail[:500]}")


def _device_lock(device_id: str) -> asyncio.Lock:
    key = (id(asyncio.get_running_loop()), device_id)
    lock = _DEVICE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _DEVICE_LOCKS[key] = lock
    return lock


class RuijieDriver(BaseDriver):
    """Async RGOS driver over Telnet console (SSH optional)."""

    @property
    def _prefer_console(self) -> bool:
        return (self.device.get("transport") or "").lower() in ("console", "telnet")

    def _credentials(self):
        return get_credentials(self.device)

    def _transport(self):
        username, password = self._credentials()
        port = int(self.device.get("management_port") or 22)
        return SSHTransport(self.device["management_address"], username, password, port=port)

    def _console_transport(self) -> ConsoleTransport | None:
        host = self.device.get("console_host")
        port = self.device.get("console_port")
        if not host or not port:
            return None
        return ConsoleTransport(
            host,
            int(port),
            username=None,
            password=None,
            enable_password=None,
            allow_empty_password=True,
            enable=True,
            device_id=self.device["id"],
            pager_off_command="terminal length 0",
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

    async def _exec(self, command: str) -> str:
        async with _device_lock(self.device["id"]):
            if self._prefer_console:
                con = self._console_transport()
                if con:
                    out = (await con.run(command)).strip()
                    raise_for_ruijie_error(out, command)
                    return out
            out = (await self._transport().run(command)).strip()
            raise_for_ruijie_error(out, command)
            return out

    async def exec_logged(self, command: str) -> str:
        return await self._logged("EXEC", command, lambda: self._exec(command))

    async def _configure(self, lines: list[str]) -> str:
        async with _device_lock(self.device["id"]):
            if self._prefer_console:
                con = self._console_transport()
                if con:
                    out = await con.run_config(lines)
                    raise_for_ruijie_error(out, "; ".join(lines))
                    return out
            raise RuntimeError("RGOS config over SSH not wired up for this lab device yet")

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def identify(self):
        raw = await self.exec_logged("show version")
        return {"vendor": "ruijie", "platform": "rgos", "data": RuijieParser.parse_version(raw), "raw": raw}

    async def get_facts(self):
        raw = await self.exec_logged("show version")
        return {"data": RuijieParser.parse_version(raw), "raw": raw}

    async def get_interfaces(self):
        raw = await self.exec_logged("show ip interface brief")
        parsed = RuijieParser.parse_interfaces(raw)
        if not parsed:
            raw2 = await self.exec_logged("show interface status")
            return {"data": RuijieParser.parse_interface_status(raw2), "raw": raw2}
        return {"data": parsed, "raw": raw}

    async def get_interfaces_detail(self):
        raw = await self.exec_logged("show interface")
        return {"data": raw, "raw": raw}

    async def get_routes(self):
        raw = await self.exec_logged("show ip route")
        return {"data": RuijieParser.parse_routes(raw), "raw": raw}

    async def get_arp(self):
        raw = await self.exec_logged("show arp")
        return {"data": RuijieParser.parse_arp(raw), "raw": raw}

    async def get_vlans(self):
        raw = await self.exec_logged("show vlan")
        return {"data": RuijieParser.parse_vlans(raw), "raw": raw}

    async def get_config(self):
        raw = await self.exec_logged("show running-config")
        return {"data": RuijieParser.parse_running_config(raw), "raw": raw}

    async def backup(self):
        raw = await self.exec_logged("show running-config")
        return {"data": raw, "raw": raw}

    # ------------------------------------------------------------------
    # Health / save / tools
    # ------------------------------------------------------------------

    async def health(self):
        result = {"device_id": self.device["id"]}
        host = self.device.get("console_host") or self.device.get("management_address", "").split("/")[0]
        port = int(self.device.get("console_port") or (self.device.get("management_port") or 22))
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3.0)
            writer.close()
            result["console_reachable"] = True
        except Exception as e:
            result.update(reachable=False, reason=str(e))
            return result
        try:
            raw = await self.exec_logged("show version")
            result.update(reachable=True, data=RuijieParser.parse_version(raw))
        except Exception as e:
            result.update(reachable=False, reason=str(e))
        return result

    async def save_config(self):
        out = await self._logged("SAVE", "write memory", lambda: self._exec("write memory"))
        return {"saved": True, "verified": True, "output": out}

    async def ping_tool(self, address: str, repeat: int = 3, timeout: int = 2):
        cmd = f"ping {address} repeat {repeat} timeout {timeout}"

        def _run():
            return self._exec(cmd)

        out = await self._logged("PING", f"{address} x{repeat}", _run)
        m = re.search(r"(\d+) packets transmitted, (\d+) received", out)
        loss = 100
        if m:
            sent, recv = int(m.group(1)), int(m.group(2))
            loss = 100 - int(recv * 100 / sent) if sent else 100
        return {"raw": out, "loss_percent": loss}

    async def traceroute_tool(self, address: str, timeout: int = 2, probes: int = 2):
        cmd = f"traceroute {address} timeout {timeout} probe {probes}"

        def _run():
            return self._exec(cmd)

        out = await self._logged("TRACEROUTE", address, _run)
        return {"raw": out}

    # ------------------------------------------------------------------
    # Config (write)
    # ------------------------------------------------------------------

    async def apply(self, commands: list[str]):
        out = await self._configure(commands)
        return {"success": True, "outputs": [out]}

    async def _txn_backup(self) -> bool:
        try:
            raw = await self.exec_logged("show running-config")
            self._txn_config_snapshot = raw
            return bool(raw and raw.strip())
        except Exception as e:
            log_event(self.device["id"], "TXN-BACKUP", "snapshot failed", status="FAIL", error=str(e))
            return False

    async def _txn_rollback(self) -> dict:
        snapshot = getattr(self, "_txn_config_snapshot", None)
        if not snapshot:
            return {"status": "FAIL", "output": "no pre-change snapshot"}
        lines = [
            ln.strip()
            for ln in snapshot.replace("\r", "").splitlines()
            if ln.strip() and not ln.strip().startswith("!")
            and not ln.strip().lower().startswith("building configuration")
            and not ln.strip().lower().startswith("current configuration")
        ]
        try:
            await self._configure(lines)
            return {"status": "OK", "output": f"replayed {len(lines)} config lines"}
        except Exception as e:
            return {"status": "FAIL", "output": str(e)[:300]}

    async def config_transaction(self, commands, verify=None, save_on_success=False, description=""):
        verify = verify or []
        report = {"description": description, "steps": []}
        if not await self._txn_backup():
            report.update(status="failed_preapply", reason="running-config snapshot failed")
            return report
        try:
            await self._logged("TXN-APPLY", "; ".join(commands), lambda: self._configure(commands))
            report["steps"].append({"phase": "apply", "status": "OK"})
        except Exception as e:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", reason=f"apply failed: {e}", rollback=rb)
            return report

        failures = []
        for chk in verify:
            command = chk.get("command", "")
            expect = chk.get("expect")
            try:
                out = await self.exec_logged(command)
                if expect and expect.lower() not in out.lower():
                    failures.append({"command": command, "reason": f"'{expect}' not found"})
            except Exception as e:
                failures.append({"command": command, "reason": str(e)})
        if failures:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", verify_failures=failures, rollback=rb)
            return report

        report["steps"].append({"phase": "verify", "status": "OK", "checks": len(verify)})
        if save_on_success:
            await self.save_config()
            report["steps"].append({"phase": "save", "status": "OK"})
        report["status"] = "committed"
        return report

    async def set_hostname(self, name: str):
        out = await self._logged("CONFIG", f"hostname {name}", lambda: self._configure([f"hostname {name}"]))
        return {"status": "applied", "output": out}

    async def interface_set_state(self, interface: str, up: bool):
        line = "no shutdown" if up else "shutdown"
        out = await self._logged("CONFIG", f"interface {interface}; {line}",
                                 lambda: self._configure([f"interface {interface}", line]))
        return {"status": "applied", "output": out}

    async def interface_set_description(self, interface: str, description: str):
        line = f"description {description}" if description.strip() else "no description"
        out = await self._logged("CONFIG", f"interface {interface}; {line}",
                                 lambda: self._configure([f"interface {interface}", line]))
        return {"status": "applied", "output": out}

    async def interface_remove_address(self, interface: str):
        out = await self._logged(
            "CONFIG", f"interface {interface}; no ip address",
            lambda: self._configure([f"interface {interface}", "no ip address"]),
        )
        return {"status": "applied", "output": out}

    async def interface_set_address(self, interface: str, address: str):
        if "/" in address:
            ip, bits = address.split("/", 1)
            mask = ".".join(
                str(((0xFFFFFFFF << (32 - int(bits))) >> shift) & 0xFF)
                for shift in (24, 16, 8, 0)
            )
        else:
            parts = address.split()
            if len(parts) != 2:
                raise ValueError("address must be CIDR (a.b.c.d/nn) or 'a.b.c.d mask'")
            ip, mask = parts
        out = await self._logged(
            "CONFIG", f"interface {interface}; ip address {ip} {mask}",
            lambda: self._configure([f"interface {interface}", f"ip address {ip} {mask}"]),
        )
        return {"status": "applied", "output": out}

    async def create_vlan(self, vlan_id: int, name: str | None = None):
        lines = [f"vlan {vlan_id}"]
        if name:
            lines.append(f"name {name}")
        out = await self._logged("CONFIG", f"vlan {vlan_id}", lambda: self._configure(lines))
        return {"status": "applied", "output": out}

    async def delete_vlan(self, vlan_id: int):
        out = await self._logged("CONFIG", f"no vlan {vlan_id}", lambda: self._configure([f"no vlan {vlan_id}"]))
        return {"status": "applied", "output": out}

    async def set_access_port(self, interface: str, vlan_id: int):
        lines = [f"interface {interface}", "switchport mode access", f"switchport access vlan {vlan_id}"]
        out = await self._logged("CONFIG", f"access {interface} vlan {vlan_id}", lambda: self._configure(lines))
        return {"status": "applied", "output": out}

    async def set_trunk_port(self, interface: str, allowed_vlans: str = "all"):
        value = "all" if allowed_vlans.strip().lower() == "all" else allowed_vlans
        lines = [f"interface {interface}", "switchport mode trunk", f"switchport trunk allowed vlan {value}"]
        out = await self._logged("CONFIG", f"trunk {interface} allow {value}", lambda: self._configure(lines))
        return {"status": "applied", "output": out}

    async def add_static_route(self, prefix: str, gateway: str, distance: int | None = None):
        line = f"ip route {prefix} {gateway}"
        if distance is not None:
            line += f" {distance}"
        out = await self._logged("CONFIG", line, lambda: self._configure([line]))
        return {"status": "applied", "output": out}

    async def remove_static_route(self, prefix: str, gateway: str):
        line = f"no ip route {prefix} {gateway}"
        out = await self._logged("CONFIG", line, lambda: self._configure([line]))
        return {"status": "applied", "output": out}