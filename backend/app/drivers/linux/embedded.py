from app.drivers.linux.base import LinuxBaseDriver
from app.core.audit import log_event


class EmbeddedLinuxDriver(LinuxBaseDriver):
    """Embedded Linux driver for BusyBox-based systems (ARM, Xilinx, CSMS, etc).
    
    BusyBox v1.24.1 available commands include:
    - Network: ifconfig, ip, route, netstat, nslookup, telnet, wget, nc, ping
    - System: ps, top, free, df, mount, uname, uptime, dmesg, sysctl
    - File: ls, cat, cp, mv, rm, mkdir, find, grep, sed, awk, tar, du, sort
    - Process: kill, killall, pidof, nice, renice
    - Storage: fdisk, blkid, fsck, fstrim, mkdosfs, mkfs.vfat
    - Utils: date, hwclock, hexdump, strings, md5sum, sha256sum, sha512sum
    """

    async def identify(self):
        t = self._transport()
        log_event(self.device["id"], "identify", "uname -a")
        uname = await t.run("uname -a")
        log_event(self.device["id"], "identify", "cat /proc/version")
        try:
            proc_version = await t.run("cat /proc/version")
        except Exception:
            proc_version = "not available"
        log_event(self.device["id"], "identify", "busybox --list")
        try:
            busybox_list = await t.run("/bin/busybox --list 2>/dev/null | wc -l")
        except Exception:
            busybox_list = "unknown"
        return {
            "vendor": "linux",
            "platform": "embedded",
            "uname": uname,
            "proc_version": proc_version,
            "busybox_commands": busybox_list,
        }

    async def get_facts(self):
        t = self._transport()
        log_event(self.device["id"], "get_facts", "embedded system info")
        uname = await t.run("uname -a")
        uptime = await t.run("uptime")
        hostname = await t.run("hostname")
        try:
            proc_version = await t.run("cat /proc/version")
        except Exception:
            proc_version = "not available"
        try:
            cpu_info = await t.run("cat /proc/cpuinfo | head -20")
        except Exception:
            cpu_info = "not available"
        try:
            product = await t.run("cat /etc/productversion 2>/dev/null || echo 'not found'")
        except Exception:
            product = "not available"
        return {
            "uname": uname,
            "proc_version": proc_version,
            "uptime": uptime,
            "hostname": hostname,
            "cpu_info": cpu_info,
            "product": product,
        }

    async def get_interfaces(self):
        t = self._transport()
        log_event(self.device["id"], "get_interfaces", "ifconfig / /proc/net/dev")
        try:
            output = await t.run("/bin/busybox ifconfig 2>/dev/null || cat /proc/net/dev")
            return {"raw": output}
        except Exception:
            output = await t.run("cat /proc/net/dev")
            return {"raw": output}

    async def get_routes(self):
        t = self._transport()
        log_event(self.device["id"], "get_routes", "route")
        output = await t.run("/bin/busybox route 2>/dev/null || route -n")
        routes = []
        for line in output.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 8 and parts[0] not in ("Kernel", "Destination", "Iface"):
                routes.append({
                    "destination": parts[0],
                    "gateway": parts[1],
                    "genmask": parts[2],
                    "flags": parts[3],
                    "metric": int(parts[4]) if parts[4].isdigit() else 0,
                    "interface": parts[7],
                })
        return routes

    async def get_config(self):
        t = self._transport()
        log_event(self.device["id"], "get_config", "embedded config")
        configs = {}
        try:
            configs["hostname"] = await t.run("cat /etc/hostname")
        except Exception:
            configs["hostname"] = "not available"
        try:
            configs["hosts"] = await t.run("cat /etc/hosts")
        except Exception:
            configs["hosts"] = "not available"
        try:
            configs["fstab"] = await t.run("cat /etc/fstab")
        except Exception:
            configs["fstab"] = "not available"
        try:
            configs["mounts"] = await t.run("cat /proc/mounts")
        except Exception:
            configs["mounts"] = "not available"
        try:
            configs["inittab"] = await t.run("cat /etc/inittab 2>/dev/null || echo 'not found'")
        except Exception:
            configs["inittab"] = "not available"
        try:
            configs["network_interfaces"] = await t.run("cat /etc/network/interfaces 2>/dev/null || echo 'not found'")
        except Exception:
            configs["network_interfaces"] = "not available"
        return configs

    async def get_services(self):
        t = self._transport()
        log_event(self.device["id"], "get_services", "ps + init scripts")
        services = {}
        try:
            output = await t.run("ps")
            services["processes"] = output
        except Exception:
            services["processes"] = "not available"
        try:
            output = await t.run("ls /etc/init.d/ 2>/dev/null || echo 'not found'")
            services["init_scripts"] = output
        except Exception:
            services["init_scripts"] = "not available"
        return services

    async def get_disk(self):
        t = self._transport()
        log_event(self.device["id"], "get_disk", "df + mount + blkid")
        result = {}
        try:
            result["df"] = await t.run("df -h")
        except Exception:
            result["df"] = "not available"
        try:
            result["mounts"] = await t.run("mount")
        except Exception:
            result["mounts"] = "not available"
        try:
            result["blkid"] = await t.run("blkid 2>/dev/null || echo 'blkid not available'")
        except Exception:
            result["blkid"] = "not available"
        return result

    async def get_memory(self):
        t = self._transport()
        log_event(self.device["id"], "get_memory", "free + meminfo")
        result = {}
        try:
            result["free"] = await t.run("free")
        except Exception:
            result["free"] = "not available"
        try:
            result["meminfo"] = await t.run("cat /proc/meminfo | head -15")
        except Exception:
            result["meminfo"] = "not available"
        return result

    async def get_ntp(self):
        t = self._transport()
        log_event(self.device["id"], "get_ntp", "ntpq + hwclock")
        result = {}
        try:
            result["ntpq"] = await t.run("ntpq -p 2>/dev/null || echo 'ntpq not available'")
        except Exception:
            result["ntpq"] = "not available"
        try:
            result["hwclock"] = await t.run("hwclock 2>/dev/null || echo 'hwclock not available'")
        except Exception:
            result["hwclock"] = "not available"
        return result

    async def get_processes(self):
        t = self._transport()
        log_event(self.device["id"], "get_processes", "ps + top")
        result = {}
        try:
            result["ps"] = await t.run("ps")
        except Exception:
            result["ps"] = "not available"
        try:
            result["top"] = await t.run("top -b -n 1 2>/dev/null | head -20 || echo 'top not available'")
        except Exception:
            result["top"] = "not available"
        return result

    async def get_network_stats(self):
        t = self._transport()
        log_event(self.device["id"], "get_network_stats", "netstat + ifconfig")
        result = {}
        try:
            result["netstat"] = await t.run("netstat -tuln 2>/dev/null || echo 'netstat not available'")
        except Exception:
            result["netstat"] = "not available"
        try:
            result["arp"] = await t.run("cat /proc/net/arp 2>/dev/null || echo 'not available'")
        except Exception:
            result["arp"] = "not available"
        return result

    async def apply(self, commands: list[str]):
        t = self._transport()
        outputs = []
        for command in commands:
            log_event(self.device["id"], "apply", command)
            outputs.append(await t.run(command))
        return {"success": True, "outputs": outputs}
