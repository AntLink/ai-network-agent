from app.drivers.mikrotik.driver import MikroTikDriver
from app.drivers.cisco.driver import CiscoDriver
from app.drivers.cisco.asa import AsaDriver
from app.drivers.aruba.driver import ArubaDriver
from app.drivers.ruijie.driver import RuijieDriver
from app.drivers.fortinet.driver import FortiOSDriver
from app.drivers.linux.debian import DebianDriver
from app.drivers.linux.embedded import EmbeddedLinuxDriver
from app.drivers.linux.rhel import RHELDriver
from app.drivers.linux.base import LinuxBaseDriver
from app.drivers.generic.driver import GenericSSHDriver


def _detect_linux_distro(device: dict):
    """Detect Linux distro from device metadata or SSH probe."""
    platform = (device.get("platform") or "").lower()
    
    if platform in ("debian", "ubuntu", "kali", "linuxmint"):
        return DebianDriver(device)
    if platform in ("rhel", "centos", "fedora", "rocky", "alma"):
        return RHELDriver(device)
    if platform in ("embedded", "arm", "xilinx", "openwrt"):
        return EmbeddedLinuxDriver(device)
    
    # Default: try to detect via SSH
    return LinuxBaseDriver(device)


def get_driver(device: dict):
    vendor = (device.get("vendor") or "").lower()
    
    if vendor == "mikrotik":
        return MikroTikDriver(device)
    if vendor == "cisco":
        platform = (device.get("platform") or "").lower()
        if "asa" in platform or "asav" in platform:
            return AsaDriver(device)
        return CiscoDriver(device)
    if vendor == "aruba":
        return ArubaDriver(device)
    if vendor == "ruijie":
        return RuijieDriver(device)
    if vendor in ("fortinet", "fortigate"):
        return FortiOSDriver(device)
    if vendor == "linux":
        return _detect_linux_distro(device)
    
    return GenericSSHDriver(device)
