from app.drivers.linux.base import LinuxBaseDriver
from app.core.audit import log_event


class DebianDriver(LinuxBaseDriver):
    """Debian/Ubuntu specific driver with apt package management."""

    async def identify(self):
        result = await super().identify()
        result["distro"] = "debian"
        return result

    async def get_facts(self):
        result = await super().get_facts()
        t = self._transport()
        try:
            log_event(self.device["id"], "get_facts", "apt --version")
            apt_version = await t.run("apt --version 2>/dev/null | head -1 || echo 'apt not found'")
            result["package_manager"] = "apt"
            result["package_manager_version"] = apt_version.strip()
        except Exception:
            result["package_manager"] = "unknown"
        return result

    async def get_services(self):
        t = self._transport()
        log_event(self.device["id"], "get_services", "systemctl + dpkg")
        services = {}
        try:
            output = await t.run("systemctl list-units --type=service --state=running --no-pager 2>/dev/null || echo 'systemctl not available'")
            services["running"] = output
        except Exception:
            services["running"] = "not available"
        try:
            output = await t.run("dpkg -l 2>/dev/null | head -30 || echo 'dpkg not available'")
            services["packages"] = output
        except Exception:
            services["packages"] = "not available"
        return services

    async def get_config(self):
        configs = await super().get_config()
        t = self._transport()
        log_event(self.device["id"], "get_config", "debian specific")
        try:
            configs["apt_sources"] = await t.run("cat /etc/apt/sources.list 2>/dev/null || echo 'not found'")
        except Exception:
            configs["apt_sources"] = "not available"
        try:
            configs["hostname"] = await t.run("cat /etc/hostname 2>/dev/null || echo 'not found'")
        except Exception:
            configs["hostname"] = "not available"
        try:
            configs["hosts"] = await t.run("cat /etc/hosts 2>/dev/null || echo 'not found'")
        except Exception:
            configs["hosts"] = "not available"
        return configs

    async def get_disk(self):
        t = self._transport()
        log_event(self.device["id"], "get_disk", "df + lsblk")
        result = {}
        try:
            result["df"] = await t.run("df -h")
        except Exception:
            result["df"] = "not available"
        try:
            result["lsblk"] = await t.run("lsblk 2>/dev/null || echo 'lsblk not available'")
        except Exception:
            result["lsblk"] = "not available"
        return result

    async def apply(self, commands: list[str]):
        t = self._transport()
        outputs = []
        for command in commands:
            log_event(self.device["id"], "apply", command)
            output = await t.run(command)
            outputs.append(output)
        return {"success": True, "outputs": outputs}
