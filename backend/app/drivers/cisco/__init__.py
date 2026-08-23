"""High-level Cisco IOS/IOS-XE router API (MikroTik-like)."""
from .connection import IOSConnection
from .models import Interface, StaticRoute, OSPFConfig
from .parser import IOSParser
from typing import List, Optional


class CiscoIOSRouter:
    """
    High-level API for managing Cisco IOS/IOS-XE devices.
    Mirrors MikroTik API style: typed objects, context manager, auto save.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        secret: Optional[str] = None,
        device_id: Optional[str] = None,
    ):
        self.device = {
            "id": device_id or host,
            "management_address": host,
        }
        self._conn = IOSConnection(self.device)
        self._conn._get_connection_params = lambda: {
            "device_type": "cisco_ios",
            "host": host,
            "username": username,
            "password": password,
            "secret": secret or password,
            "timeout": 30,
            "global_delay_factor": 2,
        }
        self.parser = IOSParser()

    def __enter__(self):
        self._conn.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.disconnect()

    # ==================== INTERFACE ====================

    def get_interfaces(self) -> List[Interface]:
        """Get all interfaces with status."""
        raw = self._conn.send_show("show ip interface brief", use_textfsm=True)
        return self.parser.parse_interfaces(raw)

    def get_interface(self, name: str) -> Optional[Interface]:
        """Get single interface by name."""
        for intf in self.get_interfaces():
            if intf.name == name:
                return intf
        return None

    def set_interface(self, interface: Interface) -> str:
        """Configure or update an interface."""
        return self._conn.send_config(interface.to_config_commands())

    def delete_interface(self, name: str) -> str:
        """Remove interface from config (loopback/sub-interface)."""
        return self._conn.send_config([f"no interface {name}"])

    # ==================== STATIC ROUTE ====================

    def add_static_route(self, route: StaticRoute) -> str:
        """Add a static route."""
        return self._conn.send_config(route.to_config_commands())

    def remove_static_route(self, destination: str, mask: str, next_hop: str) -> str:
        """Remove a static route."""
        cmd = f"no ip route {destination} {mask} {next_hop}"
        return self._conn.send_config([cmd])

    def get_static_routes(self) -> List[StaticRoute]:
        """Get all static routes."""
        raw = self._conn.send_show("show ip route static", use_textfsm=False)
        return self.parser.parse_static_routes(raw)

    # ==================== OSPF ====================

    def configure_ospf(self, config: OSPFConfig) -> str:
        """Configure OSPF process."""
        return self._conn.send_config(config.to_config_commands())

    def remove_ospf(self, process_id: int) -> str:
        """Remove OSPF process."""
        return self._conn.send_config([f"no router ospf {process_id}"])

    # ==================== SYSTEM ====================

    def save_config(self) -> str:
        """Save running config to startup (write memory)."""
        return self._conn.save_config()

    def reload(self, in_minutes: int = 1) -> str:
        """Schedule reload."""
        return self._conn.send_show(f"reload in {in_minutes}", use_textfsm=False)

    def get_hostname(self) -> str:
        """Get device hostname."""
        output = self._conn.send_show("show running-config | include hostname", use_textfsm=False)
        parts = output.split()
        return parts[-1] if parts else "Unknown"

    def get_version(self) -> dict:
        """Get IOS version info."""
        output = self._conn.send_show("show version", use_textfsm=False)
        version_line = next((l for l in output.split("\n") if "Cisco IOS" in l), "")
        return {"version": version_line.strip(), "raw": output}