import os
import json
from pathlib import Path
from dotenv import load_dotenv
from app.drivers.base import BaseDriver
from app.transports.ssh import SSHTransport
from app.core.audit import log_event

env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class LinuxBaseDriver(BaseDriver):
    """Base driver for all Linux systems with common functionality."""

    def _prefer_console(self) -> bool:
        return str(self.device.get("transport") or "").lower() in ("console", "telnet")

    def _console_transport(self):
        """Console (telnet) path untuk perangkat GNS3/gang terpencil (mis. VPCS)."""
        host = self.device.get("console_host")
        port = self.device.get("console_port")
        if not host or not port:
            return None
        from app.transports.console import ConsoleTransport
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "root"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
        return ConsoleTransport(
            host, int(port),
            username=username,
            password=password or None,
            allow_empty_password=True,
            device_id=self.device["id"],
        )

    def _transport(self):
        if self._prefer_console():
            con = self._console_transport()
            if con:
                return con
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "root"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
        port = int(os.getenv(f"{prefix}_SSH_PORT", "22"))
        return SSHTransport(self.device["management_address"], username, password, port=port)

    async def identify(self):
        t = self._transport()
        log_event(self.device["id"], "identify", "uname -a")
        uname = await t.run("uname -a")
        log_event(self.device["id"], "identify", "os-release")
        try:
            os_release = await t.run("cat /etc/os-release 2>/dev/null || echo 'no release file'")
        except Exception:
            os_release = "no release file"
        return {"vendor": "linux", "uname": uname, "os_release": os_release}

    async def get_facts(self):
        t = self._transport()
        log_event(self.device["id"], "get_facts", "system info")
        uname = await t.run("uname -a")
        uptime = await t.run("uptime")
        hostname = await t.run("hostname")
        try:
            os_release = await t.run("cat /etc/os-release 2>/dev/null || echo 'no release file'")
        except Exception:
            os_release = "no release file"
        return {
            "uname": uname,
            "os_release": os_release,
            "uptime": uptime,
            "hostname": hostname,
        }

    async def get_interfaces(self):
        t = self._transport()
        log_event(self.device["id"], "get_interfaces", "network interfaces")
        try:
            output = await t.run("ip -json addr show")
            return json.loads(output)
        except Exception:
            try:
                output = await t.run("ifconfig 2>/dev/null || cat /proc/net/dev")
                return {"raw": output}
            except Exception:
                output = await t.run("cat /proc/net/dev")
                return {"raw": output}

    async def get_routes(self):
        t = self._transport()
        log_event(self.device["id"], "get_routes", "routing table")
        try:
            output = await t.run("ip -json route show")
            return json.loads(output)
        except Exception:
            try:
                output = await t.run("route -n 2>/dev/null || cat /proc/net/route")
                return {"raw": output}
            except Exception:
                output = await t.run("cat /proc/net/route")
                return {"raw": output}

    async def get_config(self):
        t = self._transport()
        log_event(self.device["id"], "get_config", "network config")
        configs = {}
        try:
            configs["interfaces"] = await t.run("cat /etc/network/interfaces 2>/dev/null || echo 'not found'")
        except Exception:
            configs["interfaces"] = "not available"
        try:
            configs["sshd_config"] = await t.run("cat /etc/ssh/sshd_config 2>/dev/null | head -50 || echo 'not found'")
        except Exception:
            configs["sshd_config"] = "not available"
        return configs

    async def get_services(self):
        t = self._transport()
        log_event(self.device["id"], "get_services", "systemctl list")
        try:
            output = await t.run("systemctl list-units --type=service --state=running --no-pager 2>/dev/null || echo 'systemctl not available'")
            return {"raw": output}
        except Exception:
            return {"raw": "not available"}

    async def get_disk(self):
        t = self._transport()
        log_event(self.device["id"], "get_disk", "df -h")
        output = await t.run("df -h")
        return {"raw": output}

    async def get_memory(self):
        t = self._transport()
        log_event(self.device["id"], "get_memory", "free -m")
        output = await t.run("free -m")
        return {"raw": output}

    async def backup(self):
        t = self._transport()
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"backup-{timestamp}"
        log_event(self.device["id"], "backup", f"creating backup {backup_name}")
        try:
            await t.run(f"tar czf /tmp/{backup_name}.tar.gz /etc/network /etc/ssh/sshd_config 2>/dev/null || true")
        except Exception:
            pass
        return {"backup_name": backup_name}

    async def apply(self, commands: list[str]):
        t = self._transport()
        outputs = []
        for command in commands:
            log_event(self.device["id"], "apply", command)
            outputs.append(await t.run(command))
        return {"success": True, "outputs": outputs}
