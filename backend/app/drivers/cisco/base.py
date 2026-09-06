"""Base utilities for Cisco IOS drivers.

This module provides common utilities and constants used by both
CiscoDriver (async) and NetmikoCiscoDriver (sync) to avoid code duplication.
"""
import os
import re
from typing import Optional, Tuple


# Legacy SSH options required by IOSv 15.6
IOSV_LEGACY_SSH_OPTIONS = {
    "kex_algs": ["diffie-hellman-group14-sha1"],
    "server_host_key_algs": ["ssh-rsa"],
    "mac_algs": ["hmac-sha1"],
}

TXN_FLASH_FILE = "flash0:pre-txn.cfg"


def get_credentials(device: dict) -> Tuple[str, str, str]:
    """Get device credentials from environment variables.
    
    Single source of truth for credential management used by both
    CiscoDriver and NetmikoCiscoDriver.
    
    Priority:
    1. Device-specific env vars: {DEVICE_ID}_USERNAME, {DEVICE_ID}_PASSWORD, {DEVICE_ID}_SECRET
    2. Global env vars: NETWORK_USERNAME, NETWORK_PASSWORD, NETWORK_SECRET
    3. Fallback: username='admin', password='', secret=password
    
    Args:
        device: Dictionary containing device configuration with 'id' key
        
    Returns:
        Tuple of (username, password, enable_secret)
    """
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    secret = os.getenv(f"{prefix}_SECRET", os.getenv("NETWORK_SECRET", password))
    return username, password, secret


def prefix_to_mask(address: str) -> Tuple[str, str]:
    """Convert CIDR notation to IP and mask.
    
    Args:
        address: IP address in CIDR format (e.g., '192.168.1.1/24')
        
    Returns:
        Tuple of (ip_address, netmask)
        
    Raises:
        ValueError: If address format is invalid
    """
    import ipaddress
    iface = ipaddress.ip_interface(address)
    return str(iface.ip), str(iface.netmask)


def route_target(prefix: str) -> str:
    """Convert prefix to IOS route format.
    
    Args:
        prefix: Network prefix (e.g., '192.168.1.0/24' or '192.168.1.0 255.255.255.0')
        
    Returns:
        Formatted network and mask for IOS (e.g., '192.168.1.0 255.255.255.0')
    """
    import ipaddress
    if "/" in prefix:
        network = ipaddress.ip_network(prefix, strict=False)
        return f"{network.network_address} {network.netmask}"
    return prefix


def extract_hostname(output: str) -> Optional[str]:
    """Extract hostname from 'show running-config' output.
    
    Args:
        output: CLI output from 'show running-config | include ^hostname'
        
    Returns:
        Hostname string or None if not found
    """
    m = re.search(r"^hostname\s+(\S+)\s*$", output, re.M)
    return m.group(1) if m else None
