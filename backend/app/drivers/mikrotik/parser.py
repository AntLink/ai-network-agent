"""Parsers for MikroTik RouterOS command output.

Converts raw CLI text into structured JSON data for easier frontend consumption.
"""
import re
from typing import List, Dict, Any


class MikroTikParser:
    """Parser for MikroTik RouterOS structured output."""

    @staticmethod
    def _clean_text(raw_text: str) -> str:
        """Clean MikroTik CLI output by removing \\r and normalizing whitespace."""
        if not raw_text:
            return ""
        # Remove carriage returns and normalize line endings
        return raw_text.replace('\r\n', '\n').replace('\r', '').strip()

    @staticmethod
    def parse_identity(raw_text: str) -> Dict[str, Any]:
        """Parse '/system identity print' output."""
        info = {}
        if not raw_text:
            return info
        
        clean_text = MikroTikParser._clean_text(raw_text)
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 2:
                key = parts[0].strip()
                value = ':'.join(parts[1:]).strip()
                info[key] = value
        
        return info

    @staticmethod
    def parse_resource(raw_text: str) -> Dict[str, Any]:
        """Parse '/system resource print' output into structured JSON.
        
        Converts output like:
            uptime: 11h58m50s
            version: 7.22.1 (stable)
            cpu-load: 3%
            free-memory: 169.9MiB
            total-memory: 384.0MiB
        
        Into:
            {
                "uptime": "11h58m50s",
                "version": "7.22.1 (stable)",
                "cpu_load": "3%",
                "free_memory": "169.9MiB",
                "total_memory": "384.0MiB"
            }
        """
        info = {}
        if not raw_text:
            return info
        
        clean_text = MikroTikParser._clean_text(raw_text)
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 2:
                key = parts[0].strip()
                value = ':'.join(parts[1:]).strip()
                # Clean up value - remove trailing commas and whitespace
                value = value.rstrip(',').strip()
                info[key] = value
        
        return info

    @staticmethod
    def parse_interfaces(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/interface print detail without-paging' output."""
        interfaces = []
        if not raw_text:
            return interfaces
        
        clean_text = MikroTikParser._clean_text(raw_text)
        current_if = None
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Interface header: "0  R ether1 ether 10Gbps-full"
            # or "Flags: X - disabled, R - running"
            if not line.startswith(' ') and line and not line.startswith('Flags:') and not line.startswith('Columns:'):
                if current_if:
                    interfaces.append(current_if)
                # Split by whitespace, but handle variable spacing
                parts = line.split()
                if len(parts) >= 2:
                    current_if = {
                        "name": parts[1] if len(parts) > 1 else "",
                        "type": parts[2] if len(parts) > 2 else "",
                        "mtu": 1500,  # default
                        "status": "up",
                        "rx_packets": 0,
                        "tx_packets": 0,
                        "rx_bytes": 0,
                        "tx_bytes": 0
                    }
            elif current_if:
                # Parse key-value pairs
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "mtu":
                        try:
                            current_if["mtu"] = int(value)
                        except:
                            pass
                    elif key == "status" or key == "running":
                        current_if["status"] = value.lower()
                    elif key == "rx-packet" or key == "packets-received":
                        try:
                            current_if["rx_packets"] = int(value.split()[0])
                        except:
                            pass
                    elif key == "tx-packet" or key == "packets-sent":
                        try:
                            current_if["tx_packets"] = int(value.split()[0])
                        except:
                            pass
                    elif key == "rx-byte" or key == "bytes-received":
                        try:
                            current_if["rx_bytes"] = int(value.split()[0])
                        except:
                            pass
                    elif key == "tx-byte" or key == "bytes-sent":
                        try:
                            current_if["tx_bytes"] = int(value.split()[0])
                        except:
                            pass
                    elif key == "mac-address":
                        current_if["mac_address"] = value
                    elif key == "last-link-up-time" or key == "link-downs":
                        current_if[key.replace('-', '_')] = value
        
        if current_if:
            interfaces.append(current_if)
        return interfaces

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip route print detail without-paging' output."""
        routes = []
        if not raw_text:
            return routes
        
        clean_text = MikroTikParser._clean_text(raw_text)
        current_route = None
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Route header: "0 ADC 192.168.88.0/24 ether1 ether1 0"
            if not line.startswith(' ') and line and not line.startswith('Flags:') and not line.startswith('Columns:'):
                if current_route:
                    routes.append(current_route)
                parts = line.split()
                current_route = {
                    "dst_address": parts[1] if len(parts) > 1 else "",
                    "gateway": parts[3] if len(parts) > 3 else "",
                    "interface": parts[2] if len(parts) > 2 else "",
                    "distance": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                    "type": "static" if len(parts) > 0 and parts[0] == 'S' else parts[0] if len(parts) > 0 else "",
                    "metric": 0
                }
            elif current_route:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "distance":
                        try:
                            current_route["distance"] = int(value)
                        except:
                            pass
                    elif key == "metric" or key == "pref-src":
                        current_route[key.replace('-', '_')] = value
        
        if current_route:
            routes.append(current_route)
        return routes

    @staticmethod
    def parse_ip_addresses(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip address print detail without-paging' output."""
        addresses = []
        if not raw_text:
            return addresses
        
        clean_text = MikroTikParser._clean_text(raw_text)
        current_addr = None
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Address header: "0 192.168.88.1/24 ether1"
            if not line.startswith(' ') and line and not line.startswith('Flags:') and not line.startswith('Columns:'):
                if current_addr:
                    addresses.append(current_addr)
                parts = line.split()
                current_addr = {
                    "address": parts[0] if len(parts) > 0 else "",
                    "interface": parts[2] if len(parts) > 2 else "",
                    "network": "",
                    "broadcast": ""
                }
                # Parse CIDR
                if '/' in current_addr["address"]:
                    addr, prefix = current_addr["address"].split('/')
                    current_addr["address"] = addr
                    current_addr["prefix_length"] = int(prefix)
            elif current_addr:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "network":
                        current_addr["network"] = value
                    elif key == "broadcast":
                        current_addr["broadcast"] = value
        
        if current_addr:
            addresses.append(current_addr)
        return addresses

    @staticmethod
    def parse_config(raw_text: str) -> List[str]:
        """Parse '/export terse' output into list of config commands."""
        lines = []
        if not raw_text:
            return lines
        
        clean_text = MikroTikParser._clean_text(raw_text)
        for line in clean_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        
        return lines

    @staticmethod
    def parse_system_users(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/user print detail without-paging' output."""
        users = []
        if not raw_text:
            return users
        
        clean_text = MikroTikParser._clean_text(raw_text)
        current_user = None
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if not line.startswith(' ') and line and not line.startswith('Flags:') and not line.startswith('Columns:'):
                if current_user:
                    users.append(current_user)
                parts = line.split()
                current_user = {
                    "name": parts[0] if len(parts) > 0 else "",
                    "group": parts[1] if len(parts) > 1 else ""
                }
            elif current_user:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    current_user[key.replace('-', '_')] = value
        
        if current_user:
            users.append(current_user)
        return users

    @staticmethod
    def parse_dhcp_server(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip dhcp-server print detail without-paging' output."""
        servers = []
        if not raw_text:
            return servers
        
        clean_text = MikroTikParser._clean_text(raw_text)
        current_server = None
        for line in clean_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if not line.startswith(' ') and line and not line.startswith('Flags:') and not line.startswith('Columns:'):
                if current_server:
                    servers.append(current_server)
                parts = line.split()
                current_server = {
                    "name": parts[0] if len(parts) > 0 else "",
                    "interface": parts[1] if len(parts) > 1 else ""
                }
            elif current_server:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    current_server[key.replace('-', '_')] = value
        
        if current_server:
            servers.append(current_server)
        return servers
