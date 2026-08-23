import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from app.transports.ssh import SSHTransport


COMMANDS = [
    ("Service status (/etc/init.d)", "/etc/init.d/cloudflared status"),
    ("Process listing", "ps aux | grep cloudflared"),
    ("Last 30 log lines", "cat /var/log/cloudflared.log 2>/dev/null | tail -30"),
    ("Cloudflared binary status", "/media/httpd/cgi-bin/cloudflared status"),
    ("Listening ports", "netstat -tlnp 2>/dev/null || cat /proc/net/tcp"),
    ("Connectivity test", "ping -c 2 1.1.1.1"),
    ("DNS config", "cat /etc/resolv.conf"),
    ("DNS resolution", "nslookup cloudflared.com 2>/dev/null || echo 'nslookup not available'"),
]

SEP = "=" * 70
LINE = "-" * 70


async def main():
    transport = SSHTransport(
        host="192.168.162.20",
        username="root",
        password="815m1ll4h",
    )

    print(SEP)
    print("  CLOUDFLARED TUNNEL DIAGNOSTIC -- 192.168.162.20")
    print(SEP)

    for label, cmd in COMMANDS:
        print(f"\n{LINE}")
        print(f"  >> {label}")
        print(f"  >> Command: {cmd}")
        print(LINE)
        try:
            output = await transport.run(cmd)
            print(output if output.strip() else "(no output)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{SEP}")
    print("  DIAGNOSTIC COMPLETE")
    print(SEP)


if __name__ == "__main__":
    asyncio.run(main())
