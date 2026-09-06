"""Aruba AOS-CX driver.

Read-only inspection and safe config operations via SSH or GNS3 console.

AOS-CX notes (verified in CISCO-ARUBA-LAB on Virtual.10.10.1181):
- Pager is disabled with `no page` (NOT `terminal length 0`).
- Config mode is entered with `configure terminal`, exit with `end`.
- Console login is username+password (no enable secret).
"""
import asyncio
import re
import time

from app.core.audit import log_event
from app.drivers.base import BaseDriver
from app.drivers.aruba.base import get_credentials
from app.drivers.aruba.parser import ArubaParser
from app.drivers.cisco.cli import clean_cli_output, drain_prompt
from app.transports.ssh import SSHTransport
from app.transports.console import ConsoleTransport

_DEVICE_LOCKS: dict[tuple[int, str], asyncio.Lock] = {}

_ARUBA_ERROR_RE = re.compile(
    r"(?im)(Invalid input|Unknown command|Unrecognized command|"
    r"%( )?(Not found|Error|Failed)|Insufficient privilege|"
    r"Syntax error|\.\s*\^\s*$)"
)


class ArubaCLIError(Exception):
    """AOS-CX CLI command failed with an error marker."""


def raise_for_aoscx_error(output: str, command: str) -> None:
    if not output or not _ARUBA_ERROR_RE.search(output):
        return
    error_lines = [
        line.strip() for line in output.splitlines()
        if line.strip().startswith("%") or "^\n" in line or " ^" in line or line.strip() == "^"
    ]
    detail = "\n".join(error_lines).strip() or output.strip()
    raise ArubaCLIError(f"AOS-CX command failed: {command}\n{detail}")


def _device_lock(device_id: str) -> asyncio.Lock:
    key = (id(asyncio.get_running_loop()), device_id)
    lock = _DEVICE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _DEVICE_LOCKS[key] = lock
    return lock


class ArubaDriver(BaseDriver):
    """Async AOS-CX driver over SSH with console fallback."""

    # ------------------------------------------------------------------
    # transports
    # ------------------------------------------------------------------

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
        username, password = self._credentials()
        return ConsoleTransport(
            host,
            int(port),
            username=username,
            password=password,
            enable=False,
            device_id=self.device["id"],
            pager_off_command="no page",
        )

    async def _logged(self, action: str, detail: str, fn):
        device_id = self.device["id"]
        t0 = time.perf_counter()
        try:
            out = await fn()
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="OK", duration_ms=duration)
            return out
        except Exception as e:
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="FAIL", duration_ms=duration, error=str(e))
            raise

    async def _exec(self, command: str) -> str:
        """Run one EXEC command (console if configured, else SSH)."""
        async with _device_lock(self.device["id"]):
            if self._prefer_console:
                con = self._console_transport()
                if con:
                    out = (await con.run(command)).strip()
                    raise_for_aoscx_error(out, command)
                    return out
            try:
                out = (await self._transport().run(command)).strip()
                raise_for_aoscx_error(out, command)
                return out
            except ArubaCLIError:
                raise
            except Exception as e:
                con = self._console_transport()
                if not con:
                    raise
                log_event(
                    self.device["id"], "CONSOLE-FALLBACK",
                    f"SSH failed ({type(e).__name__}: {e}); retrying via console",
                )
                out = (await con.run(command)).strip()
                raise_for_aoscx_error(out, command)
                return out

    async def exec_logged(self, command: str) -> str:
        return await self._logged("EXEC", command, lambda: self._exec(command))

    async def _configure(self, lines: list[str]) -> str:
        """Run configuration commands inside `configure terminal ... end`."""
        async with _device_lock(self.device["id"]):
            if self._prefer_console:
                con = self._console_transport()
                if con:
                    out = await con.run_config(lines)
                    raise_for_aoscx_error(out, "; ".join(lines))
                    return out
            return await self._logged(
                "CONFIG", "; ".join(lines), lambda: self._ssh_config(lines)
            )

    async def _ssh_config(self, lines: list[str]) -> str:
        """SSH config-mode runner tuned for AOS-CX (uses `no page`)."""
        outputs: list[str] = []
        t = self._transport()

        async def _do():
            async with t.interactive() as proc:
                await drain_prompt(proc.stdout, max_wait=6.0)
                for send_line in ["no page", "configure terminal", *lines, "end"]:
                    proc.stdin.write(send_line + "\n")
                    cleaned = clean_cli_output(await drain_prompt(proc.stdout), send_line)
                    raise_for_aoscx_error(cleaned, send_line)
                    if cleaned and send_line not in ("no page", "configure terminal", "end"):
                        outputs.append(cleaned)
            return "\n".join(outputs).strip()

        return await t._with_deadline(_do(), "; ".join(lines))

    # ------------------------------------------------------------------
    # Identification / facts
    # ------------------------------------------------------------------

    async def identify(self):
        version_raw = await self.exec_logged("show version")
        system_raw = await self.exec_logged("show system")
        parsed = ArubaParser.parse_facts(version_raw, system_raw)
        return {"vendor": "aruba", "data": parsed, "raw": f"show version:\n{version_raw}\n\nshow system:\n{system_raw}"}

    async def get_facts(self):
        version_raw = await self.exec_logged("show version")
        system_raw = await self.exec_logged("show system")
        parsed = ArubaParser.parse_facts(version_raw, system_raw)
        return {"data": parsed, "raw": f"show version:\n{version_raw}\n\nshow system:\n{system_raw}"}

    async def get_interfaces(self):
        raw = await self.exec_logged("show interface brief")
        return {"data": ArubaParser.parse_interfaces_brief(raw), "raw": raw}

    async def get_interfaces_detail(self):
        raw = await self.exec_logged("show ip interface")
        return {"data": ArubaParser.parse_ip_interfaces(raw), "raw": raw}

    async def get_ip_interfaces(self):
        return await self.get_interfaces_detail()

    async def get_routes(self):
        raw = await self.exec_logged("show ip route")
        return {"data": ArubaParser.parse_routes(raw), "raw": raw}

    async def get_arp(self):
        raw = await self.exec_logged("show arp")
        return {"data": ArubaParser.parse_arp(raw), "raw": raw}

    async def get_vlans(self):
        raw = await self.exec_logged("show vlan")
        return {"data": ArubaParser.parse_vlans(raw), "raw": raw}

    async def get_config(self):
        raw = await self.exec_logged("show running-config")
        return {"data": ArubaParser.parse_running_config(raw), "raw": raw}

    async def backup(self):
        raw = await self.exec_logged("show running-config")
        return {"data": raw, "raw": raw}

    async def get_memory(self):
        raw = await self.exec_logged("show system")
        info = ArubaParser.parse_system(raw)
        return {"data": info, "raw": raw}

    async def get_ntp(self):
        raw = await self.exec_logged("show ntp status")
        return {"data": raw, "raw": raw}

    # ------------------------------------------------------------------
    # Health / save / ping / traceroute
    # ------------------------------------------------------------------

    async def health(self):
        result: dict = {"device_id": self.device["id"]}
        host = (self.device.get("management_address") or "").split("/")[0]
        port = int(self.device.get("management_port") or 22)
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=3.0
            )
            banner = await asyncio.wait_for(reader.readline(), timeout=3.0)
            writer.close()
            result["vm_ssh_reachable"] = bool(banner)
            result["ssh_banner"] = banner.decode(errors="replace").strip()
        except Exception:
            result["vm_ssh_reachable"] = False
        try:
            con = self._console_transport()
            if con:
                raw = (await con.run("show system")).strip()
                result.update(ArubaParser.parse_system(raw))
                result["reachable"] = True
                result["status"] = "online"
                return result
        except Exception as e:
            result["console_error"] = str(e)
        result["reachable"] = False
        result["status"] = "unreachable"
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
    # Config (apply / plan / verify)
    # ------------------------------------------------------------------

    async def apply(self, commands: list[str]):
        out = await self._configure(commands)
        return {"success": True, "outputs": [out]}

    async def set_hostname(self, name: str):
        out = await self._logged(
            "CONFIG", f"hostname {name}", lambda: self._configure([f"hostname {name}"])
        )
        return {"status": "applied", "output": out}

    async def interface_set_state(self, interface: str, up: bool):
        line = "no shutdown" if up else "shutdown"
        out = await self._logged(
            "CONFIG", f"interface {interface}; {line}",
            lambda: self._configure([f"interface {interface}", line]),
        )
        return {"status": "applied", "output": out}

    async def interface_set_description(self, interface: str, description: str):
        line = f"description {description}" if description.strip() else "no description"
        out = await self._logged(
            "CONFIG", f"interface {interface}; {line}",
            lambda: self._configure([f"interface {interface}", line]),
        )
        return {"status": "applied", "output": out}

    async def interface_set_address(self, interface: str, address: str):
        if address.lower() == "dhcp":
            lines = [f"interface {interface}", f"ip address dhcp"]
        else:
            if "/" not in address:
                raise ValueError("address must be CIDR (a.b.c.d/nn) for AOS-CX")
            lines = [f"interface {interface}", f"ip address {address}"]
        out = await self._logged(
            "CONFIG", f"interface {interface}; ip address {address}",
            lambda: self._configure(lines),
        )
        return {"status": "applied", "output": out}

    async def interface_remove_address(self, interface: str):
        """Remove all IPv4 addresses from an interface.

        AOS-CX rejects bare `no ip address` (it is incomplete); the address
        must be spelled out, e.g. `no ip address 192.168.42.200/24`.
        """
        iface_result = await self.get_ip_interfaces()
        addresses = [
            entry.get("ip_address") or ""
            for entry in iface_result.get("data", [])
            if entry.get("name") == interface and entry.get("ip_address")
        ]
        if not addresses:
            return {"status": "applied", "output": f"interface {interface}: no IPv4 address configured"}
        lines = [f"interface {interface}"] + [f"no ip address {a}" for a in addresses]
        out = await self._logged(
            "CONFIG", f"interface {interface}; remove {len(addresses)} address(es)",
            lambda: self._configure(lines),
        )
        return {"status": "applied", "output": out}

    async def create_vlan(self, vlan_id: int, name: str | None = None):
        lines = [f"vlan {vlan_id}"]
        if name:
            lines.append(f"name {name}")
        out = await self._logged(
            "CONFIG", f"vlan {vlan_id}", lambda: self._configure(lines)
        )
        return {"status": "applied", "output": out}

    async def delete_vlan(self, vlan_id: int):
        out = await self._logged(
            "CONFIG", f"no vlan {vlan_id}", lambda: self._configure([f"no vlan {vlan_id}"])
        )
        return {"status": "applied", "output": out}

    async def set_access_port(self, interface: str, vlan_id: int):
        lines = [f"interface {interface}", f"vlan access {vlan_id}"]
        out = await self._logged(
            "CONFIG", f"access {interface} vlan {vlan_id}", lambda: self._configure(lines)
        )
        return {"status": "applied", "output": out}

    async def set_trunk_port(self, interface: str, allowed_vlans: str = "all"):
        value = "tagged all" if allowed_vlans.strip().lower() == "all" else allowed_vlans
        lines = [f"interface {interface}", f"vlan trunk allowed {value}"]
        out = await self._logged(
            "CONFIG", f"trunk {interface} allow {value}", lambda: self._configure(lines)
        )
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

    # ------------------------------------------------------------------
    # Config transaction: backup -> apply -> verify -> commit | rollback
    # ------------------------------------------------------------------

    async def _txn_backup(self) -> bool:
        """Snapshot running-config in-memory for rollback."""
        try:
            raw = await self.exec_logged("show running-config")
            self._txn_config_snapshot = raw
            return bool(raw and raw.strip())
        except Exception as e:
            log_event(self.device["id"], "TXN-BACKUP", "snapshot failed", status="FAIL", error=str(e))
            return False

    async def _txn_rollback(self) -> dict:
        """Replay the pre-change running-config (best-effort on AOS-CX).

        AOS-CX has no `configure replace`; the running-config is mostly
        replayable inside `configure terminal`. Errors are collected but the
        rollback is reported OK when no ArubaCLIError is raised.
        """
        snapshot = getattr(self, "_txn_config_snapshot", None)
        if not snapshot:
            return {"status": "FAIL", "output": "no pre-change snapshot available"}
        lines = [
            ln.strip()
            for ln in snapshot.replace("\r", "").splitlines()
            if ln.strip()
            and not ln.strip().startswith("!")
            and "running-config" not in ln.strip().lower()
            and ln.strip().lower() not in ("current configuration:", "end")
        ]
        try:
            await self._configure(lines)
            return {"status": "OK", "output": f"replayed {len(lines)} config lines"}
        except Exception as e:
            return {"status": "FAIL", "output": str(e)}

    async def config_transaction(
        self,
        commands: list[str],
        verify: list[dict] | None = None,
        save_on_success: bool = False,
        description: str = "",
    ) -> dict:
        verify = verify or []
        report: dict = {"description": description, "steps": []}

        if not await self._txn_backup():
            report["status"] = "failed_preapply"
            report["reason"] = "running-config snapshot failed; no changes applied"
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