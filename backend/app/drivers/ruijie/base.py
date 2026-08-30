"""Base utilities for Ruijie RGOS drivers (single source of truth)."""
import os
from typing import Tuple


def get_credentials(device: dict) -> Tuple[str, str]:
    """Get device credentials from environment variables.

    Priority:
    1. Device-specific env vars: {DEVICE_ID}_USERNAME, {DEVICE_ID}_PASSWORD
    2. Global env vars: NETWORK_USERNAME, NETWORK_PASSWORD
    3. Fallback: username='admin', password=''

    The RGOS telnet console typically needs no login (enable has no secret),
    so these are mainly used by the SSH transport path.
    """
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    return username, password