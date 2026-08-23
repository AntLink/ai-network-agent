import asyncio
import ipaddress
import os
import re
import time

from app.core.audit import log_event
from app.drivers.base import BaseDriver
from app.drivers.cisco.cli import (
    CiscoCLIError,
    raise_for_ios_error,
    run_batch,
    run_config_lines,
    send_interactive,
)
from app.transports.ssh import SSHTransport, SSHConnectError, SSHTimeoutError, PromptTimeoutError
from app.transports.console import ConsoleTransport

# Legacy SSH options required by IOSv 15.6
IOSV_LEGACY_SSH_OPTIONS = {
    "kex_algs": ["diffie-hellman-group14-sha1"],
    "server_host_key_algs": ["ssh-rsa"],
    "mac_algs": ["hmac-sha1"],
}

TXN_FLASH_FILE = "flash0:pre-txn.cfg"


def _prefix_to_mask(address: str) -> tuple[str, str]:
    iface = ipaddress.ip_interface(address)
    return str(iface.ip), str(iface.netmask)


def _extract_hostname(output: str) -> str | None:
    m = re.search(r"^hostname\s+(\S+)\s*$", output, re.M)
    return m.group(1) if m else None


def _device_credentials(device: dict) -> tuple[str, str, str]:
    """(username, password, secret) from per-device env or global fallback."""
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    secret = os.getenv(f"{prefix}_SECRET", os.getenv("NETWORK_SECRET", password))
    return username, password, secret


class CiscoDriver(BaseDriver):
    def _transport(self):
        username, password, _ = _device_credentials(self.device)
        return SSHTransport(
            self.device["management_address"],
            username,
            password,
            connect_options=IOSV_LEGACY_SSH_OPTIONS,
        )

    def _console_transport(self) -> ConsoleTransport | None:
        """Console (telnet) fallback path; configured per-device in inventory
        via optional keys: console_host / console_port."""
        host = self.device.get("console_host")
        port = self.device.get("console_port")
        if not host or not port:
            return None
        _, password, secret = _device_credentials(self.device)
        return ConsoleTransport(
            host,
            int(port),
            password=password,
            enable_password=secret,
            device_id=self.device["id"],
        )

    @property
    def _prefer_console(self) -> bool:
        return (self.device.get("transport") or "").lower() == "console"

    async def _logged(self, action: str, detail: str, fn):
        """Run an operation with timed OK/FAIL audit logging."""
        device_id = self.device["id"]
        t0 = time.perf_counter()
        try:
            out = await fn()
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="OK", duration_ms=duration)
            return out
        except Exception as e:
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(
                device_id, action, detail,
                status="FAIL", duration_ms=duration, error=str(e),
            )
            raise

    async def _exec(self, command: str) -> str:
        """Run one EXEC command.

        Transport selection:
        - device.transport == 'console'  -> always console
        - otherwise SSH first; if SSH connection fails and a console is
          configured, retry once over console (auto-fallback, audited).
        """
        if self._prefer_console:
            con = self._console_transport()
            if con:
                out = (await con.run(command)).strip()
                raise_for_ios_error(out, command)
                return out

        try:
            out = (await self._transport().run(command)).strip()
            raise_for_ios_error(out, command)
            return out
        except CiscoCLIError:
            raise  # command reached device and failed; console won't help
        except Exception as e:
            con = self._console_transport()
            if not con:
                raise
            log_event(
                self.device["id"], "CONSOLE-FALLBACK",
                f"SSH failed ({type(e).__name__}: {e}); retrying via console",
            )
            out = (await con.run(command)).strip()
            raise_for_ios_error(out, command)
            return out

    async def exec_logged(self, command: str) -> str:
        return await self._logged("EXEC", command, lambda: self._exec(command))

    async def _configure(self, lines: list[str]) -> str:
        """Run configuration commands with console fallback on SSH failure."""
        if self._prefer_console:
            con = self._console_transport()
            if con:
                return await self._logged("CONFIG", "; ".join(lines), lambda: con.run_config(lines))

        try:
            return await self._logged("CONFIG", "; ".join(lines), lambda: run_config_lines(self._transport(), lines))
        except CiscoCLIError:
            raise
        except Exception as e:
            con = self._console_transport()
            if not con:
                raise
            log_event(
                self.device["id"], "CONSOLE-FALLBACK",
                f"SSH config failed ({type(e).__name__}: {e}); retrying via console",
            )
            return await self._logged("CONFIG", "; ".join(lines), lambda: con.run_config(lines))

    # ------------------------------------------------------------------
    # Read-only (READ)
    # ------------------------------------------------------------------

    async def identify(self):
        return {"vendor": "cisco", "raw": await self.exec_logged("show version")}

    async def get_facts(self):
        return {"raw": await self.exec_logged("show version")}

    async def get_interfaces(self):
        return {"raw": await self.exec_logged("show ip interface brief")}

    async def get_interfaces_detail(self):
        return {"raw": await self.exec_logged("show interfaces")}

    async def get_routes(self):
        return {"raw": await self.exec_logged("show ip route")}

    async def get_arp(self):
        return {"raw": await self.exec_logged("show ip arp")}

    async def get_cpu_memory(self):
        cpu = await self.exec_logged("show processes cpu summary")
        mem = await self.exec_logged("show memory summary")
        return {"cpu": cpu, "memory": mem}

    async def get_acls(self):
        return {"raw": await self.exec_logged("show access-lists")}

    async def get_cdp_neighbors(self):
        return {"raw": await self.exec_logged("show cdp neighbors detail")}

    async def get_nat_translations(self):
        return {"raw": await self.exec_logged("show ip nat translation")}

    async def get_startup_config(self):
        return {"raw": await self.exec_logged("show startup-config")}

    async def get_logs(self):
        return {"raw": await self.exec_logged("show logging")}

    async def get_config(self):
        return {"raw": await self.exec_logged("show running-config")}

    async def backup(self):
        cmd = "show running-config"
        raw = await self._logged("BACKUP", cmd, lambda: self._transport().run(cmd))
        return {"raw": raw}

    # ------------------------------------------------------------------
    # System configuration (CONFIG)
    # ------------------------------------------------------------------

    async def set_hostname(self, name: str):
        return await self._logged(
            "CONFIG", f"hostname {name}", lambda: self._configure([f"hostname {name}"])
        )

    async def set_dns(self, servers: list[str]):
        lines = ["no ip name-server"] + [f"ip name-server {s}" for s in servers]
        return await self._logged("CONFIG", "; ".join(lines), lambda: self._configure(lines))

    async def add_ntp_server(self, server: str):
        return await self._logged(
            "CONFIG", f"ntp server {server}", lambda: self._configure([f"ntp server {server}"])
        )

    async def remove_ntp_server(self, server: str):
        return await self._logged(
            "CONFIG", f"no ntp server {server}", lambda: self._configure([f"no ntp server {server}"])
        )

    async def set_banner_motd(self, text: str):
        return await self._logged(
            "CONFIG", f"banner motd", lambda: self._configure([f"banner motd #{text}#"])
        )

    async def create_local_user(self, username: str, password: str, privilege: int = 1):
        detail = f"username {username} privilege {privilege}"
        return await self._logged(
            "CONFIG", detail,
            lambda: self._configure([f"username {username} privilege {privilege} secret {password}"]),
        )

    async def delete_local_user(self, username: str):
        return await self._logged(
            "CONFIG", f"no username {username}",
            lambda: self._configure([f"no username {username}"]),
        )

    # ------------------------------------------------------------------
    # Interface configuration (CONFIG)
    # ------------------------------------------------------------------

    async def interface_set_description(self, interface: str, description: str):
        line = f"description {description}" if description.strip() else "no description"
        return await self._logged(
            "CONFIG", f"interface {interface}; {line}",
            lambda: self._configure([f"interface {interface}", line]),
        )

    async def interface_set_address(self, interface: str, address: str):
        if address.lower() == "dhcp":
            lines = [f"interface {interface}", "ip address dhcp"]
            detail = f"interface {interface}; ip address dhcp"
        else:
            if "/" in address:
                ip, mask = _prefix_to_mask(address)
            else:
                parts = address.split()
                if len(parts) != 2:
                    raise ValueError("address must be CIDR (a.b.c.d/nn), 'a.b.c.d mask' or 'dhcp'")
                ip, mask = parts
            lines = [f"interface {interface}", f"ip address {ip} {mask}"]
            detail = f"interface {interface}; ip address {ip} {mask}"
        return await self._logged("CONFIG", detail, lambda: self._configure(lines))

    async def interface_remove_address(self, interface: str):
        return await self._logged(
            "CONFIG", f"interface {interface}; no ip address",
            lambda: self._configure([f"interface {interface}", "no ip address"]),
        )

    async def interface_set_mtu(self, interface: str, mtu: int):
        return await self._logged(
            "CONFIG", f"interface {interface}; mtu {mtu}",
            lambda: self._configure([f"interface {interface}", f"mtu {mtu}"]),
        )

    async def interface_set_state(self, interface: str, up: bool):
        line = "no shutdown" if up else "shutdown"
        return await self._logged(
            "CONFIG", f"interface {interface}; {line}",
            lambda: self._configure([f"interface {interface}", line]),
        )

    # ------------------------------------------------------------------
    # Routing (CONFIG)
    # ------------------------------------------------------------------

    @staticmethod
    def _route_target(prefix: str) -> str:
        if "/" in prefix:
            network = ipaddress.ip_network(prefix, strict=False)
            return f"{network.network_address} {network.netmask}"
        return prefix

    async def add_static_route(self, prefix: str, gateway: str, distance: int | None = None):
        target = self._route_target(prefix)
        line = f"ip route {target} {gateway}"
        if distance is not None:
            line += f" {distance}"
        return await self._logged("CONFIG", line, lambda: self._configure([line]))

    async def remove_static_route(self, prefix: str, gateway: str):
        target = self._route_target(prefix)
        line = f"no ip route {target} {gateway}"
        return await self._logged("CONFIG", line, lambda: self._configure([line]))

    # ------------------------------------------------------------------
    # ACLs (CONFIG)
    # ------------------------------------------------------------------

    async def acl_create(self, name: str, acl_type: str, rules: list[str]):
        acl_type = acl_type.lower()
        if acl_type not in ("standard", "extended"):
            raise ValueError("acl_type must be standard|extended")
        lines = [f"ip access-list {acl_type} {name}"] + list(rules)
        return await self._logged(
            "CONFIG", f"ip access-list {acl_type} {name} ({len(rules)} rule)",
            lambda: self._configure(lines),
        )

    async def acl_delete(self, name: str, acl_type: str):
        acl_type = acl_type.lower()
        if acl_type not in ("standard", "extended"):
            raise ValueError("acl_type must be standard|extended")
        line = f"no ip access-list {acl_type} {name}"
        return await self._logged(
            "CONFIG", line,
            lambda: self._configure([line]),
        )

    async def acl_apply(self, name: str, interface: str, direction: str):
        direction = direction.lower()
        if direction not in ("in", "out"):
            raise ValueError("direction must be in|out")
        lines = [f"interface {interface}", f"ip access-group {name} {direction}"]
        return await self._logged(
            "CONFIG", f"ip access-group {name} {direction} on {interface}",
            lambda: self._configure(lines),
        )

    async def acl_unapply(self, name: str, interface: str, direction: str):
        direction = direction.lower()
        if direction not in ("in", "out"):
            raise ValueError("direction must be in|out")
        lines = [f"interface {interface}", f"no ip access-group {name} {direction}"]
        return await self._logged(
            "CONFIG", f"no ip access-group {name} {direction} on {interface}",
            lambda: self._configure(lines),
        )

    # ------------------------------------------------------------------
    # Operations (TEST / CONFIG / AUDIT)
    # ------------------------------------------------------------------

    async def apply(self, commands: list[str]):
        outputs = await self._logged(
            "EXEC", f"batch[{len(commands)}]: {'; '.join(commands)}",
            lambda: run_batch(self._transport(), commands),
        )
        return {"success": True, "outputs": outputs}

    async def save_config(self):
        """Save running-config to startup AND PROVE it persisted.

        Lesson from GNS3 lab (2026-08-23): on broken flash (wrong disk
        interface) `write memory` prints [OK] while saving nothing.
        Trust only a startup-config that contains the same hostname as
        the running config.
        """
        out = await self._logged("SAVE", "write memory", lambda: self._exec("write memory"))

        try:
            run_out = await self._exec("show running-config | include ^hostname")
            start_out = await self._exec("show startup-config | include ^hostname")
        except Exception as e:
            log_event(self.device["id"], "SAVE-VERIFY",
                      "startup verification failed to execute",
                      status="FAIL", error=str(e))
            return {"saved": False, "verified": False,
                    "reason": f"verification commands failed: {e}", "output": out}

        run_host = _extract_hostname(run_out)
        start_host = _extract_hostname(start_out)
        verified = bool(start_host) and start_host == run_host
        log_event(self.device["id"], "SAVE-VERIFY",
                  f"running={run_host!r} startup={start_host!r}",
                  status="OK" if verified else "FAIL")
        if not verified:
            return {"saved": False, "verified": False,
                    "reason": (
                        "startup-config does not match running-config; "
                        "[OK] from write memory was likely false "
                        "(check flash health via /devices/{id}/health)"
                    ),
                    "hostname_running": run_host,
                    "hostname_startup": start_host,
                    "output": out}
        return {"saved": True, "verified": True, "hostname": start_host, "output": out}

    async def health(self):
        """Reachability + flash/NVRAM sanity.

        Broken vIOS flash signature: '0K bytes of ATA System CompactFlash'
        plus %Error opening flash0:/ in logs. Healthy images report the
        real size (e.g. 262144K).
        """
        import socket as _socket

        result: dict = {"device_id": self.device["id"]}
        addr = self.device.get("management_address") or ""
        host = addr.split("/")[0]
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 22), timeout=5.0
            )
            result["reachable"] = True
        except Exception as e:
            result.update(reachable=False, reason=f"TCP/22 unreachable: {e}")
            return result
        try:
            banner = await asyncio.wait_for(reader.readline(), timeout=5.0)
            result["ssh_banner"] = banner.decode(errors="replace").strip()
        except Exception:
            result["ssh_banner"] = None  # slow banner != unreachable
        finally:
            writer.close()

        try:
            version_out = await self.exec_logged("show version")
        except Exception as e:
            result.update(flash_ok=None, reason=f"show version failed: {e}")
            return result

        m = re.search(r"(\S+) bytes of .*[Cc]ompact[Ff]lash", version_out)
        if m:
            size = m.group(1)
            result["flash_size"] = size
            # '0K' or '0' => broken storage (no AHCI driver / bad disk iface)
            result["flash_ok"] = not re.fullmatch(r"0[KkMm]?|0", size)
        else:
            nv = re.search(r"(\S+) bytes of non-volatile", version_out)
            result["flash_size"] = nv.group(1) if nv else None
            result["flash_ok"] = None

        result["flash_broken_hint"] = "%Error opening flash" in version_out
        return result

    # ------------------------------------------------------------------
    # Config transaction: backup -> apply -> verify -> commit | rollback
    # ------------------------------------------------------------------

    async def _txn_backup_to_flash(self) -> bool:
        """Backup running-config to flash with console fallback."""
        async def _do_backup():
            return await send_interactive(
                self._transport(), f"copy running-config {TXN_FLASH_FILE}", max_wait=10.0
            )
        try:
            out = await self._logged("TXN-BACKUP", f"copy running-config {TXN_FLASH_FILE}", _do_backup)
            return "bytes copied" in out
        except CiscoCLIError:
            raise
        except Exception as e:
            con = self._console_transport()
            if not con:
                raise
            log_event(
                self.device["id"], "CONSOLE-FALLBACK",
                f"SSH backup failed ({type(e).__name__}: {e}); retrying via console",
            )
            await con.run(f"copy running-config {TXN_FLASH_FILE}")
            return True

    async def _txn_rollback(self) -> dict:
        """Rollback with console fallback."""
        async def _do_rollback():
            return await self._transport().run(f"configure replace {TXN_FLASH_FILE} force")

        try:
            out = await self._logged("TXN-ROLLBACK", f"configure replace {TXN_FLASH_FILE} force", _do_rollback)
            ok = "rollback" in out.lower() and "error" not in out.lower()
            return {"status": "OK" if ok else "?", "output": out[-300:].strip()}
        except CiscoCLIError:
            raise
        except Exception as e:
            con = self._console_transport()
            if not con:
                return {"status": "FAIL", "output": str(e)}
            log_event(
                self.device["id"], "CONSOLE-FALLBACK",
                f"SSH rollback failed ({type(e).__name__}: {e}); retrying via console",
            )
            out = await con.run(f"configure replace {TXN_FLASH_FILE} force")
            ok = "rollback" in out.lower() and "error" not in out.lower()
            return {"status": "OK" if ok else "?", "output": out[-300:].strip()}
        finally:
            try:
                await self._transport().run(f"delete /force {TXN_FLASH_FILE}")
            except Exception:
                # best effort cleanup
                pass

    async def config_transaction(
        self,
        commands: list[str],
        verify: list[dict] | None = None,
        save_on_success: bool = False,
        description: str = "",
    ) -> dict:
        """Transaksi konfigurasi aman.

        backup flash -> apply (conf t) -> verify (EXEC + expect substring)
        gagal apply/verify -> `configure replace` rollback otomatis.
        """
        verify = verify or []
        report: dict = {"description": description, "steps": []}

        if not await self._txn_backup_to_flash():
            report["status"] = "failed_preapply"
            report["reason"] = "backup ke flash gagal; tidak ada perubahan diterapkan"
            return report

        # APPLY
        try:
            await self._logged(
                "TXN-APPLY", "; ".join(commands),
                lambda: self._configure(commands),
            )
            report["steps"].append({"phase": "apply", "status": "OK"})
        except Exception as e:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", reason=f"apply failed: {e}", rollback=rb)
            return report

        # VERIFY
        failures = []
        for chk in verify:
            command = chk.get("command", "")
            expect = chk.get("expect")
            try:
                output = await self._logged(
                    "TXN-VERIFY", f"{command}" + (f" | expect '{expect}'" if expect else ""),
                    lambda: self._exec(command),
                )
                if expect and expect.lower() not in output.lower():
                    failures.append({"command": command, "reason": f"'{expect}' tidak ditemukan"})
            except Exception as e:
                failures.append({"command": command, "reason": str(e)[:200]})

        if failures:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", verify_failures=failures, rollback=rb)
            return report

        report["steps"].append({"phase": "verify", "status": "OK", "checks": len(verify)})

        # COMMIT (+ optional save)
        if save_on_success:
            await self.save_config()
            report["steps"].append({"phase": "save", "status": "OK"})

        try:
            await self._transport().run(f"delete /force {TXN_FLASH_FILE}")
        except Exception:
            pass

        report["status"] = "committed"
        return report

    # ------------------------------------------------------------------
    # Layer-2 helpers (VLAN / access / trunk / subinterface / SVI)
    # ------------------------------------------------------------------

    async def create_vlan(self, vlan_id: int, name: str | None = None):
        lines = [f"vlan {vlan_id}"]
        if name:
            lines.append(f"name {name}")
        return await self._logged("CONFIG", f"vlan {vlan_id}", lambda: self._configure(lines))

    async def delete_vlan(self, vlan_id: int):
        return await self._logged("CONFIG", f"no vlan {vlan_id}", lambda: self._configure([f"no vlan {vlan_id}"]))

    async def set_access_port(self, interface: str, vlan_id: int):
        lines = [
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "spanning-tree portfast",
        ]
        return await self._logged("CONFIG", f"access {interface} vlan {vlan_id}", lambda: self._configure(lines))

    async def set_trunk_port(self, interface: str, allowed_vlans: str = "all"):
        lines = [
            f"interface {interface}",
            "switchport mode trunk",
            f"switchport trunk allowed vlan {allowed_vlans}",
        ]
        return await self._logged("CONFIG", f"trunk {interface} allow {allowed_vlans}", lambda: self._configure(lines))

    async def create_subinterface(self, parent_interface: str, sub_id: int, vlan_id: int, ip_address: str | None = None):
        """Create L3 subinterface (router-on-a-stick)."""
        lines = [
            f"interface {parent_interface}.{sub_id}",
            f"encapsulation dot1Q {vlan_id}",
        ]
        if ip_address:
            lines.append(f"ip address {ip_address}")
        return await self._logged("CONFIG", f"subif {parent_interface}.{sub_id} vlan {vlan_id}", lambda: self._configure(lines))

    async def set_svi(self, vlan_id: int, ip_address: str | None = None, shutdown: bool = False):
        """Create / modify Switch Virtual Interface."""
        lines = [f"interface vlan {vlan_id}"]
        if ip_address:
            lines.append(f"ip address {ip_address}")
        if shutdown:
            lines.append("shutdown")
        else:
            lines.append("no shutdown")
        return await self._logged("CONFIG", f"svi vlan {vlan_id}", lambda: self._configure(lines))

    async def ping_tool(self, address: str, repeat: int = 3, timeout: int = 2):
        import re

        cmd = f"ping {address} repeat {repeat} timeout {timeout}"
        device_id = self.device["id"]
        t0 = time.perf_counter()
        try:
            out = await self._exec(cmd)
        except Exception as e:
            log_event(
                device_id, "PING", f"{address} x{repeat}",
                status="FAIL", duration_ms=round((time.perf_counter() - t0) * 1000),
                error=str(e),
            )
            raise
        duration = round((time.perf_counter() - t0) * 1000)
        m = re.search(r"Success rate is (\d+) percent", out)
        loss = 100 - int(m.group(1)) if m else -1
        log_event(
            device_id, "PING", f"{address} x{repeat}",
            status=f"OK loss={loss}%", duration_ms=duration,
        )
        return {"raw": out}

    async def traceroute_tool(self, address: str, timeout: int = 2, probes: int = 2):
        cmd = f"traceroute {address} numeric timeout {timeout} probe {probes}"

        def _run():
            return self._exec(cmd)

        out = await self._logged("TRACEROUTE", address, _run)
        return {"raw": out}
