"""Netmiko-based Cisco IOS driver with proper enable/config/save flow."""
from netmiko import ConnectHandler
from app.core.audit import log_event

# Import from local base module
from .base import get_credentials, extract_hostname


class NetmikoCiscoDriver:
    """Cisco IOS driver using Netmiko for proper CLI interaction.
    
    Uses common credential utility from base module to avoid duplication.
    """

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

    def _connect(self):
        """Establish connection and enter enable mode."""
        if self._conn is None:
            self._conn = ConnectHandler(**self._get_connection_params())
        if not self._conn.check_enable_mode():
            self._conn.enable()
        return self._conn

    def disconnect(self):
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def run_config(self, commands: list[str]) -> str:
        """Send configuration commands in config mode."""
        conn = self._connect()
        log_event(self.device["id"], "NETMIKO_CONFIG", "; ".join(commands))
        output = conn.send_config_set(commands)
        for marker in ("% Invalid input", "% Incomplete command", "% Ambiguous command"):
            if marker in output:
                raise RuntimeError(output.strip())
        return output

    def run_exec(self, command: str) -> str:
        """Run a single exec command."""
        conn = self._connect()
        log_event(self.device["id"], "NETMIKO_EXEC", command)
        output = conn.send_command(command, expect_string=r"[#>]")
        return output

    def run_batch(self, commands: list[str]) -> list[str]:
        """Run multiple exec commands."""
        conn = self._connect()
        outputs = []
        for cmd in commands:
            log_event(self.device["id"], "NETMIKO_EXEC", cmd)
            out = conn.send_command(cmd, expect_string=r"[#>]")
            outputs.append(out)
        return outputs

    def save_config(self) -> str:
        """Save running config to startup with verification.
        
        Uses the same verification logic as CiscoDriver for consistency.
        """
        conn = self._connect()
        log_event(self.device["id"], "NETMIKO_SAVE", "write memory")
        output = conn.send_command("write memory", expect_string=r"[#>]")
        
        # Verification: check that startup-config matches running-config
        try:
            run_out = conn.send_command("show running-config | include ^hostname", expect_string=r"[#>]")
            start_out = conn.send_command("show startup-config | include ^hostname", expect_string=r"[#>]")
            
            run_host = extract_hostname(run_out)
            start_host = extract_hostname(start_out)
            
            if not (run_host and start_host and run_host == start_host):
                log_event(
                    self.device["id"], "NETMIKO_SAVE_VERIFY",
                    f"running={run_host!r} startup={start_host!r}",
                    status="FAIL"
                )
                return output
            
            log_event(
                self.device["id"], "NETMIKO_SAVE_VERIFY",
                f"running={run_host!r} startup={start_host!r}",
                status="OK"
            )
        except Exception as e:
            log_event(
                self.device["id"], "NETMIKO_SAVE_VERIFY",
                f"Verification failed: {e}",
                status="FAIL"
            )
        
        return output

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
