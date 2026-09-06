"""Cisco ASA (ASAv) driver - console-based.

ASAv in GNS3 often ships without working SSH, so the reliable path is the
telnet console (console_host / console_port in inventory). This driver uses the
shared ConsoleTransport (prompt-synced telnet) and disables the ASA pager
(`terminal pager 0`) on every session before sending a command.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

from app.drivers.base import BaseDriver
from app.drivers.cisco.base import get_credentials
from app.drivers.cisco.cli import clean_cli_output, PROMPT_RE, CiscoCLIError, raise_for_ios_error
from app.transports.console import ConsoleTransport
from app.core.audit import log_event


def _netmask(bits: int) -> str:
    """Convert a CIDR prefix length to a dotted netmask (e.g. 24 -> 255.255.255.0)."""
    if not 0 <= bits <= 32:
        raise ValueError(f"invalid prefix length: {bits}")
    mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF if bits > 0 else 0
    return ".".join(str((mask >> shift) & 0xFF) for shift in (24, 16, 8, 0))


class AsaDriver(BaseDriver):
    """Cisco ASA / ASAv driver speaking ASA IOS syntax over the telnet console."""

    def _console(self) -> ConsoleTransport:
        host = self.device.get("console_host") or (
            self.device.get("management_address") or ""
        ).split("/")[0]
        port = int(self.device.get("console_port") or 5004)
        username, password, secret = get_credentials(self.device)
        return ConsoleTransport(
            host,
            port,
            password=password or None,
            enable_password=secret or None,
            username=username or None,
            allow_empty_password=True,
            enable=True,
            device_id=self.device.get("id", ""),
            login_timeout=25,
            pager_off_command="terminal pager 0",
        )

    def _console_transport(self) -> ConsoleTransport:
        """Alias for the recovery path (device_service.console_exec)."""
        return self._console()

    async def _logged(self, action: str, detail: str, fn):
        """Run an operation with timed OK/FAIL audit logging."""
        device_id = self.device.get("id", "asa")
        import time as _time
        t0 = _time.perf_counter()
        try:
            out = await fn()
            duration = round((_time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="OK", duration_ms=duration)
            return out
        except Exception as e:
            duration = round((_time.perf_counter() - t0) * 1000)
            log_event(
                device_id, action, detail,
                status="FAIL", duration_ms=duration, error=str(e),
            )
            raise

    async def exec_logged(self, command: str) -> str:
        """Run one read-only EXEC command over the ASA console.

        Makes net_run_command('show ...') use the exec path instead of being
        mis-routed into config mode via apply().
        """
        return await self._logged("EXEC", command, lambda: self._console_exec(command))

    async def _drain_until_prompt(self, proc, max_wait: float = 30.0) -> str:
        """Read until an exec/config prompt, answering the ASA `--More--` pager."""
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
            if "<--- More --->" in buf or "--More--" in buf or "---- More ----" in buf:
                proc.stdin.write(" ")
                await asyncio.sleep(0.06)
                buf = buf.replace("<--- More --->", "").replace("--More--", "").replace("---- More ----", "")
                continue
            if PROMPT_RE.search(buf):
                break
        return buf

    async def _console_exec(self, command: str) -> str:
        """Run one EXEC (read) command over an interactive console session."""
        async with self._console().interactive() as proc:
            await self._drain_until_prompt(proc, max_wait=4.0)
            # login sudah naik ke privileged (#) via ConsoleTransport._enter_enable
            proc.stdin.write("terminal pager 0\n")
            await self._drain_until_prompt(proc, max_wait=4.0)
            proc.stdin.write(command + "\n")
            raw = await self._drain_until_prompt(proc, max_wait=40.0)
        cleaned = clean_cli_output(raw, command)
        self._raise_asa_error(cleaned, command)
        return cleaned

    async def _console_config(self, lines: list[str]) -> str:
        """Apply config commands in one `configure terminal ... end` session."""
        outputs: list[str] = []
        async with self._console().interactive() as proc:
            await self._drain_until_prompt(proc, max_wait=4.0)
            proc.stdin.write("terminal pager 0\n")
            await self._drain_until_prompt(proc, max_wait=4.0)
            proc.stdin.write("configure terminal\n")
            await self._drain_until_prompt(proc, max_wait=8.0)
            for line in lines:
                proc.stdin.write(line + "\n")
                cleaned = clean_cli_output(await self._drain_until_prompt(proc, max_wait=10.0), line)
                self._raise_asa_error(cleaned, line)
                if cleaned:
                    outputs.append(cleaned)
            proc.stdin.write("end\n")
            await self._drain_until_prompt(proc, max_wait=8.0)
        return "\n".join(outputs).strip()

    # -- read ----------------------------------------------------------------

    async def identify(self):
        raw = await self._console_exec("show version")
        return {"vendor": "cisco", "platform": "asa", "data": self._parse_version(raw), "raw": raw}

    async def get_facts(self):
        raw = await self._console_exec("show version")
        return {"data": self._parse_version(raw), "raw": raw}

    async def get_interfaces(self):
        raw = await self._console_exec("show interface ip brief")
        return {"data": self._parse_interfaces(raw), "raw": raw}

    async def get_interfaces_detail(self):
        raw = await self._console_exec("show interface")
        return {"data": raw, "raw": raw}

    async def get_routes(self):
        raw = await self._console_exec("show route")
        return {"data": self._parse_routes(raw), "raw": raw}

    async def get_config(self):
        raw = await self._console_exec("show running-config")
        return {"data": raw, "raw": raw}

    async def get_acls(self):
        raw = await self._console_exec("show access-list")
        return {"data": raw, "raw": raw}

    async def get_arp(self):
        raw = await self._console_exec("show arp")
        return {"data": raw, "raw": raw}

    async def get_cpu_memory(self):
        raw = await self._console_exec("show resource usage")
        return {"data": raw, "raw": raw}

    async def backup(self):
        raw = await self._console_exec("show running-config")
        return {"data": raw, "raw": raw}

    # -- write ---------------------------------------------------------------

    async def apply(self, commands: list[str]):
        await self._console_config(commands)
        return {"success": True}

    async def save_config(self):
        out = await self._console_exec("write memory")
        return {"saved": True, "output": out}

    @staticmethod
    def _contains_asa_error(output: str) -> bool:
        return bool(re.search(r"%\s*(Invalid|Incomplete|Ambiguous|Unknown|Error|Failed)", output or ""))

    def _raise_asa_error(self, output: str, command: str) -> None:
        """Raise CiscoCLIError on IOS-style (`% ...`) OR ASA-style (`ERROR: % ...`) errors."""
        if not output:
            return
        try:
            raise_for_ios_error(output, command)  # handles IOS `% ...` at line start
        except CiscoCLIError:
            raise
        # ASA format: "ERROR: % Invalid input ..." is not matched by the ^% anchor.
        if self._contains_asa_error(output):
            raise CiscoCLIError(f"Cisco ASA command failed: {command}\n{output.strip()[:400]}")

    async def config_transaction(
        self,
        commands: list[str],
        verify: list[dict] | None = None,
        save_on_success: bool = False,
        description: str = "",
    ) -> dict:
        """Safe config transaction: backup -> apply -> verify -> commit.

        ASA rollback of arbitrary commands is not guaranteed to be reproducible,
        so on any failure the transaction reports `rolled_back` and carries the
        full running-config backup in `report["backup"]` for manual/system restore.
        """
        verify = verify or []
        report: dict[str, Any] = {"description": description, "steps": []}

        try:
            backup_cfg = (await self.get_config()).get("raw", "")
            report["steps"].append({"phase": "backup", "status": "OK"})
        except Exception as e:  # noqa: BLE001
            report["status"] = "failed_preapply"
            report["reason"] = f"backup failed: {e}"
            return report
        report["backup"] = backup_cfg

        try:
            out = await self._console_config(list(commands))
            if self._contains_asa_error(out):
                report["steps"].append({"phase": "apply", "status": "FAILED", "detail": out[:300]})
                report["status"] = "rolled_back"
                report["reason"] = f"config rejected by ASA:\n{out[:500]}"
                return report
            report["steps"].append({"phase": "apply", "status": "OK"})
        except Exception as e:  # noqa: BLE001
            report["status"] = "rolled_back"
            report["reason"] = f"apply failed: {e}"
            return report

        failures: list[dict[str, str]] = []
        for chk in verify:
            command = str(chk.get("command", ""))
            expect = chk.get("expect")
            try:
                check_out = await self._console_exec(command)
                if expect and expect.lower() not in check_out.lower():
                    failures.append({"command": command, "reason": f"'{expect}' not found"})
            except Exception as e:  # noqa: BLE001
                failures.append({"command": command, "reason": str(e)[:200]})
        if failures:
            report["steps"].append({"phase": "verify", "status": "FAILED", "failures": failures})
            report["status"] = "rolled_back"
            report["verify_failures"] = failures
            return report

        if save_on_success:
            await self.save_config()
            report["steps"].append({"phase": "save", "status": "OK"})

        report["status"] = "committed"
        return report

    async def set_interface_address(self, interface: str, address: str, mask: str | None = None):
        if "/" in address:
            ip, prefix = address.split("/", 1)
            try:
                mask = _netmask(int(prefix))
            except (ValueError, TypeError):
                raise ValueError("prefix length must be an integer (e.g. /24)")
        elif mask:
            ip = address
        else:
            raise ValueError("address must be CIDR (a.b.c.d/nn) or provide netmask")
        lines = ["interface " + interface, f"ip address {ip} {mask}", "no shutdown"]
        out = await self._console_config(lines)
        return {"status": "applied", "output": out}

    async def add_nat(self, real_ip: str, mapped_ip: str, interface: str = "outside"):
        lines = [f"nat (inside,{interface}) source static {real_ip} {mapped_ip}"]
        out = await self._console_config(lines)
        return {"status": "applied", "output": out}

    async def add_acl(self, name: str, rule: str):
        out = await self._console_config([f"access-list {name} extended {rule}"])
        return {"status": "applied", "output": out}

    # -- Cisco-compatible write methods (route + ACL) -------------------------

    @staticmethod
    def _asa_route_target(prefix: str) -> tuple[str, str]:
        """Split a prefix into (dest, mask) for ASA `route <iface> <dest> <mask> <gw>`."""
        if "/" in prefix:
            dest, bits = prefix.split("/", 1)
            mask = _netmask(int(bits))
            return dest, mask
        parts = prefix.split()
        if len(parts) == 2:
            return parts[0], parts[1]
        return prefix, "255.255.255.0"

    async def add_static_route(
        self,
        prefix: str,
        gateway: str,
        distance: int | None = None,
        interface: str = "inside",
    ):
        dest, mask = self._asa_route_target(prefix)
        line = f"route {interface} {dest} {mask} {gateway}"
        if distance is not None:
            line += f" {distance}"
        out = await self._console_config([line])
        return {"status": "applied", "output": out}

    async def remove_static_route(self, prefix: str, gateway: str, interface: str = "inside"):
        dest, mask = self._asa_route_target(prefix)
        out = await self._console_config([f"no route {interface} {dest} {mask} {gateway}"])
        return {"status": "applied", "output": out}

    async def acl_create(self, name: str, acl_type: str, rules: list[str]):
        acl_type = (acl_type or "extended").lower()
        if acl_type not in ("standard", "extended"):
            raise ValueError("acl_type must be standard|extended")
        lines = [f"access-list {name} {acl_type} {rule}" for rule in rules]
        out = await self._console_config(lines)
        return {"status": "applied", "output": out}

    async def acl_delete(self, name: str, acl_type: str):
        # ASA removes a whole named ACL via `clear configure access-list` in CONFIG mode.
        out = await self._console_config([f"clear configure access-list {name}"])
        return {"status": "applied", "output": out}

    async def acl_apply(self, name: str, interface: str, direction: str):
        direction = (direction or "in").lower()
        if direction not in ("in", "out"):
            raise ValueError("direction must be in|out")
        out = await self._console_config([f"access-group {name} {direction} interface {interface}"])
        return {"status": "applied", "output": out}

    async def acl_unapply(self, name: str, interface: str, direction: str):
        direction = (direction or "in").lower()
        if direction not in ("in", "out"):
            raise ValueError("direction must be in|out")
        out = await self._console_config([f"no access-group {name} {direction} interface {interface}"])
        return {"status": "applied", "output": out}

    # -- health --------------------------------------------------------------

    async def health(self):
        result: dict[str, Any] = {"device_id": self.device.get("id")}
        host = self.device.get("console_host") or (
            self.device.get("management_address") or ""
        ).split("/")[0]
        port = int(self.device.get("console_port") or 5004)
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2.0)
            writer.close()
        except Exception as e:
            result.update(reachable=False, reason=f"console unreachable: {e}")
            return result
        try:
            ver = await self._console_exec("show version")
            result.update(reachable=True, data=self._parse_version(ver))
        except Exception as e:
            result.update(reachable=False, reason=str(e))
        return result

    # -- parsing -------------------------------------------------------------

    @staticmethod
    def _parse_version(out: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        m = re.search(r"Cisco Adaptive Security Appliance Software Version\s+([\d.\d()]+)", out)
        if m:
            result["version"] = m.group(1)
        m = re.search(r"Firepower.*?Version\s+([\d.()]+)", out)
        if m:
            result["firepower_version"] = m.group(1)
        m = re.search(r"Hardware:\s+(.+)$", out, re.M)
        if m:
            result["hardware"] = m.group(1).strip()
        m = re.search(r"Serial Number:\s+(\S+)", out)
        if m:
            result["serial"] = m.group(1)
        if not result:
            result["raw"] = out[:600]
        return result

    @staticmethod
    def _parse_interfaces(out: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                rows.append(
                    {"interface": parts[0], "ip": parts[1], "method": parts[2], "status": " ".join(parts[3:])}
                )
        return rows

    @staticmethod
    def _parse_routes(out: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                rows.append(
                    {
                        "protocol": parts[0],
                        "destination": parts[1],
                        "gateway": parts[2],
                        "metric": parts[3],
                    }
                )
        return rows
