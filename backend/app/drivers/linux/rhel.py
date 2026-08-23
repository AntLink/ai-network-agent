from app.drivers.linux.base import LinuxBaseDriver
from app.core.audit import log_event


class RHELDriver(LinuxBaseDriver):
    """RHEL/CentOS/Fedora specific driver with yum/dnf package management."""

    async def identify(self):
        result = await super().identify()
        result["distro"] = "rhel"
        return result

    async def get_facts(self):
        result = await super().get_facts()
        t = self._transport()
        try:
            log_event(self.device["id"], "get_facts", "dnf/yum version")
            try:
                pkg_version = await t.run("dnf --version 2>/dev/null | head -1 || echo 'dnf not found'")
                result["package_manager"] = "dnf"
            except Exception:
                pkg_version = await t.run("yum --version 2>/dev/null | head -1 || echo 'yum not found'")
                result["package_manager"] = "yum"
            result["package_manager_version"] = pkg_version.strip()
        except Exception:
            result["package_manager"] = "unknown"
        return result

    async def get_services(self):
        t = self._transport()
        log_event(self.device["id"], "get_services", "systemctl + rpm")
        services = {}
        try:
            output = await t.run("systemctl list-units --type=service --state=running --no-pager 2>/dev/null || echo 'systemctl not available'")
            services["running"] = output
        except Exception:
            services["running"] = "not available"
        try:
            output = await t.run("rpm -qa 2>/dev/null | head -30 || echo 'rpm not available'")
            services["packages"] = output
        except Exception:
            services["packages"] = "not available"
        return services

    async def get_config(self):
        configs = await super().get_config()
        t = self._transport()
        log_event(self.device["id"], "get_config", "rhel specific")
        try:
            configs["yum_repos"] = await t.run("ls /etc/yum.repos.d/ 2>/dev/null || echo 'not found'")
        except Exception:
            configs["yum_repos"] = "not available"
        try:
            configs["selinux"] = await t.run("getenforce 2>/dev/null || echo 'not available'")
        except Exception:
            configs["selinux"] = "not available"
        return configs
