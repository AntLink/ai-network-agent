"""Parsers for Cisco IOS show command output."""
import re
import ipaddress
from typing import List, Dict
from .models import Interface, StaticRoute


class IOSParser:
    """Parser for Cisco IOS structured output using TextFSM."""

    @staticmethod
    def parse_interfaces(raw_data: List[Dict]) -> List[Interface]:
        """Convert TextFSM output to list of Interface objects."""
        interfaces = []
        for item in raw_data:
            # Netmiko TextFSM keys for 'show ip interface brief'
            intf_name = item.get("intf") or item.get("interface") or ""
            ip_addr = item.get("ipaddr") or item.get("ip_addr") or item.get("ip_address")
            status = item.get("status", "").lower()
            proto = item.get("proto") or item.get("protocol") or ""
            
            interfaces.append(
                Interface(
                    name=intf_name,
                    ip_address=ip_addr if ip_addr != "unassigned" else None,
                    subnet_mask=None,  # not in brief output
                    description="",
                    is_enabled=status != "administratively down",
                    is_up=status == "up" and proto == "up",
                )
            )
        return interfaces

    @staticmethod
    def parse_static_routes(raw_text: str) -> List[StaticRoute]:
        """Parse plain-text 'show ip route static' output."""
        routes = []
        # S*  0.0.0.0/0 [1/0] via 10.0.0.1   |   S  10.99.0.0 [1/0] via 192.168.200.2
        pat = re.compile(
            r"^\s*S\*?\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?\s+\[\d+/\d+\]\s+via\s+(\S+)",
            re.MULTILINE,
        )
        for net, plen, nh in pat.findall(raw_text or ""):
            if plen is not None:
                mask = str(ipaddress.ip_network(f"0.0.0.0/{plen}").netmask)
            else:
                mask = ""
            routes.append(StaticRoute(destination=net, mask=mask, next_hop=nh))
        return routes