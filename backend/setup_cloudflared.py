import asyncio
import sys
import os
from pathlib import Path

# Load .env from backend directory
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.transports.ssh import SSHTransport


INIT_SCRIPT_LINES = [
    "#!/bin/sh",
    "### BEGIN INIT INFO",
    "# Provides:          cloudflared",
    "# Required-Start:    $network",
    "# Required-Stop:     $network",
    "# Default-Start:     2 3 4 5",
    "# Default-Stop:      0 1 6",
    "# Short-Description: Cloudflare Tunnel",
    "### END INIT INFO",
    "",
    "CLOUDFLARED=/media/httpd/cgi-bin/cloudflared",
    "",
    'case "$1" in',
    "  start)",
    '    echo "Starting cloudflared tunnel..."',
    '    if [ -x "$CLOUDFLARED" ]; then',
    '      $CLOUDFLARED start',
    '      echo "Cloudflared started"',
    "    else",
    '      echo "cloudflared not found at $CLOUDFLARED"',
    "      exit 1",
    "    fi",
    "    ;;",
    "  stop)",
    '    echo "Stopping cloudflared tunnel..."',
    '    $CLOUDFLARED stop',
    "    ;;",
    "  restart)",
    "    $0 stop",
    "    sleep 1",
    "    $0 start",
    "    ;;",
    "  status)",
    '    $CLOUDFLARED status',
    "    ;;",
    "  *)",
    '    echo "Usage: $0 {start|stop|restart|status}"',
    "    exit 1",
    "    ;;",
    "esac",
    "exit 0",
]


def _build_printf_cmd(lines: list[str], dest: str) -> str:
    """Build a printf command that writes lines to dest without using heredoc."""
    payload = "\\n".join(lines)
    return f"printf '%b\\n' '{payload}' > {dest}"


LOG_PATH = Path(__file__).parent / "setup_cloudflared.log"
_log_lines: list[str] = []


def _log(msg: str):
    print(msg)
    _log_lines.append(msg)


async def run_cmd(transport: SSHTransport, label: str, cmd: str) -> str:
    """Run a command via SSHTransport and print output."""
    _log(f"\n--- {label} ---")
    _log(f"$ {cmd[:300]}{'...' if len(cmd) > 300 else ''}")
    try:
        output = await transport.run(cmd)
        txt = output.strip()
        _log(txt)
        return txt
    except RuntimeError as e:
        _log(f"[ERROR] {e}")
        return ""


async def main():
    host = "192.168.162.20"
    username = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
    password = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")

    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)

    # --- Step 1: Test connectivity ---
    await run_cmd(transport, "Connectivity check", "uname -a")

    # --- Step 2: Check /etc writability ---
    etc_output = await run_cmd(
        transport,
        "Check /etc writability",
        'touch /etc/test_write 2>/dev/null && rm /etc/test_write 2>/dev/null && echo "writable" || echo "read-only"',
    )

    # --- Step 3: Check /media writability ---
    media_output = await run_cmd(
        transport,
        "Check /media writability",
        'touch /media/test_write 2>/dev/null && rm /media/test_write 2>/dev/null && echo "writable" || echo "read-only"',
    )

    etc_writable = "writable" in etc_output
    media_writable = "writable" in media_output

    print(f"\n=== Writability Results ===")
    print(f"/etc: {'WRITABLE' if etc_writable else 'READ-ONLY'}")
    print(f"/media: {'WRITABLE' if media_writable else 'READ-ONLY'}")

    # --- Step 4: Choose approach ---
    if etc_writable:
        print("\n>>> /etc is writable - using init.d approach")

        create_cmd = _build_printf_cmd(INIT_SCRIPT_LINES, "/etc/init.d/cloudflared")
        await run_cmd(transport, "Create /etc/init.d/cloudflared", create_cmd)

        await run_cmd(transport, "chmod +x /etc/init.d/cloudflared", "chmod +x /etc/init.d/cloudflared")
        await run_cmd(transport, "Create rc5.d symlink", "ln -sf /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared")
        await run_cmd(transport, "Start cloudflared", "/etc/init.d/cloudflared start")
        await run_cmd(transport, "Check cloudflared status", "/etc/init.d/cloudflared status")

        print("\n=== RESULT: cloudflared installed via /etc/init.d, will start on boot (rc5.d) ===")

    elif media_writable:
        print("\n>>> /etc is read-only, /media is writable - using /media/httpd approach")

        create_cmd = _build_printf_cmd(INIT_SCRIPT_LINES, "/media/httpd/cgi-bin/cloudflared-service.sh")
        await run_cmd(transport, "Create cloudflared-service.sh", create_cmd)
        await run_cmd(transport, "chmod +x cloudflared-service.sh", "chmod +x /media/httpd/cgi-bin/cloudflared-service.sh")

        await run_cmd(transport, "Check existing boot scripts", "ls -la /media/httpd/cgi-bin/*.sh 2>/dev/null | head -20")

        find_boot = await run_cmd(
            transport,
            "Find boot-trigger scripts",
            "grep -rl 'cloudflared\\|S99\\|rc\\.d\\|init\\.d' /media/httpd/cgi-bin/ 2>/dev/null || echo 'no existing boot scripts found'",
        )

        wrapper_path = "/media/httpd/cgi-bin/cloudflared-wrapper.sh"
        wrapper_lines = [
            "#!/bin/sh",
            "# Auto-start cloudflared tunnel",
            "/media/httpd/cgi-bin/cloudflared-service.sh start",
        ]
        create_wrapper = _build_printf_cmd(wrapper_lines, wrapper_path)
        await run_cmd(transport, "Create wrapper script", create_wrapper)
        await run_cmd(transport, "chmod +x wrapper", f"chmod +x {wrapper_path}")

        await run_cmd(transport, "Start cloudflared", f"{wrapper_path}")
        await run_cmd(transport, "Check cloudflared status", "/media/httpd/cgi-bin/cloudflared-service.sh status")

        print("\n=== RESULT: cloudflared installed via /media/httpd, wrapper created ===")
        print("NOTE: You may need to add the wrapper to your device's boot sequence manually.")

    else:
        print("\n>>> Both /etc and /media are READ-ONLY")
        print("=== RESULT: Cannot make cloudflared persistent automatically ===")
        print("You would need to remount filesystems read-write or use a different approach.")

    LOG_PATH.write_text("\n".join(_log_lines), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
