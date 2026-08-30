"""Base utilities for Aruba AOS-CX drivers (single source of truth)."""
import os
from typing import Optional, Tuple


def get_credentials(device: dict) -> Tuple[str, str]:
    """Get device credentials from environment variables.

    Priority:
    1. Device-specific env vars: {DEVICE_ID}_USERNAME, {DEVICE_ID}_PASSWORD
    2. Global env vars: NETWORK_USERNAME, NETWORK_PASSWORD
    3. Fallback: username='admin', password=''

    AOS-CX does not use an enable secret pre-18.04-style; console login is
    username+password only.

    Args:
        device: Dictionary containing device configuration with 'id' key

    Returns:
        Tuple of (username, password)
    """
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    return username, password