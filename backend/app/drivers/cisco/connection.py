"""Netmiko connection wrapper for Cisco IOS/IOS-XE."""
from netmiko import ConnectHandler
from app.core.audit import log_event

# Import from local base module to avoid duplication
from .base import get_credentials


class IOSConnection:
    """Netmiko wrapper with proper enable/config/save flow."""

    def __init__(self, device: dict):
        self.device = device
        self._conn = None

    def _get_connection_params(self) -> dict:
        """Get connection parameters using shared credential utility."""
        username, password, secret = get_credentials(self.device)
        return {
            "device_type": "cisco_ios",
            "host": self.device["management_address"],
            "port": int(self.device.get("management_port") or 22),
            "username": username,
            "password": password,
            "secret": secret,
            "timeout": 30,
            "global_delay_factor": 2,
        }

    def connect(self):
        """Establish SSH connection; enter enable mode when possible."""
        if self._conn is None:
            self._conn = ConnectHandler(**self._get_connection_params())
        if not self._conn.check_enable_mode():
            try:
                self._conn.enable()
            except Exception as e:
                # Priv-1 user: show commands masih jalan (read-only)
                log_event(self.device["id"], "NETMIKO_ENABLE_SKIP",
                          f"enable gagal, lanjut read-only: {e}")
        return self._conn

    def disconnect(self):
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def send_config(self, commands: list[str]) -> str:
        """Send configuration commands."""
        conn = self.connect()
        log_event(self.device["id"], "NETMIKO_CONFIG", "; ".join(commands))
        output = conn.send_config_set(commands)
        for marker in ("% Invalid input", "% Incomplete command", "% Ambiguous command"):
            if marker in output:
                raise RuntimeError(output.strip())
        return output

    def send_show(self, command: str, use_textfsm: bool = False) -> str | list[dict]:
        """Run a show command."""
        conn = self.connect()
        log_event(self.device["id"], "NETMIKO_SHOW", command)
        return conn.send_command(command, use_textfsm=use_textfsm)

    def save_config(self) -> str:
        """Save running config to startup (write memory)."""
        conn = self.connect()
        log_event(self.device["id"], "NETMIKO_SAVE", "write memory")
        return conn.send_command("write memory", expect_string=r"[#>]")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()