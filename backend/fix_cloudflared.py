import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from app.transports.ssh import SSHTransport


async def run_cmd(transport: SSHTransport, label: str, cmd: str) -> str:
    """Run a command via SSHTransport, print output, return it."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"$ {cmd}\n")
    try:
        output = await transport.run(cmd)
        txt = output.strip()
        print(txt)
        return txt
    except RuntimeError as e:
        msg = str(e)
        print(f"[STDERR] {msg}")
        return msg


async def main():
    host = "192.168.162.20"
    username = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
    password = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")

    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)

    # Step 1: Fix DNS
    await run_cmd(transport, "Step 1: Fix DNS - Write /etc/resolv.conf", (
        "echo 'nameserver 1.1.1.1' > /etc/resolv.conf && "
        "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf && "
        "echo 'nameserver 192.168.162.1' >> /etc/resolv.conf && "
        "cat /etc/resolv.conf"
    ))

    # Step 2: Verify DNS works
    await run_cmd(transport, "Step 2: Verify DNS works", "ping -c 2 cloudflared.com")

    # Step 3: Stop cloudflared
    await run_cmd(transport, "Step 3: Stop cloudflared", "/etc/init.d/cloudflared stop; sleep 2; echo 'Stop command sent'")

    # Step 4: Clean PID file
    await run_cmd(transport, "Step 4: Remove stale PID file", "rm -f /var/run/cloudflared.pid; echo 'PID file removed'")

    # Step 5: Start cloudflared fresh
    await run_cmd(transport, "Step 5: Start cloudflared fresh", "/etc/init.d/cloudflared start; sleep 3; echo 'Start command sent'")

    # Step 6: Verify it's running
    await run_cmd(transport, "Step 6a: Check running processes", "ps aux | grep cloudflared")
    await run_cmd(transport, "Step 6b: Check cloudflared log", "cat /var/log/cloudflared.log 2>/dev/null | tail -20")

    # Step 7: Check listening ports
    await run_cmd(transport, "Step 7: Check listening ports", "netstat -tlnp 2>/dev/null | head -20")

    print(f"\n{'='*60}")
    print("  ALL STEPS COMPLETED")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
