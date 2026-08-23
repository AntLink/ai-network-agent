import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env"))

sys.path.insert(0, str(Path(__file__).parent))

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

SEP = "=" * 70
LINE = "-" * 70

COMMANDS = [
    ("Find all cloudflared files (regular)", "find / -name '*cloudflared*' -type f 2>/dev/null"),
    ("Find all cloudflared files (symlinks)", "find / -name '*cloudflared*' -type l 2>/dev/null"),
    ("Check /etc/cloudflared/", "ls -la /etc/cloudflared/ 2>/dev/null || echo 'directory not found'"),
    ("Check /root/.cloudflared/", "ls -la /root/.cloudflared/ 2>/dev/null || echo 'directory not found'"),
    ("Check /media/cloudflared/", "ls -la /media/cloudflared/ 2>/dev/null || echo 'directory not found'"),
    ("Check the CGI script", "cat /media/httpd/cgi-bin/cloudflared 2>/dev/null || echo 'file not found'"),
    ("Check init.d script", "cat /etc/init.d/cloudflared 2>/dev/null || echo 'file not found'"),
    ("Check running process and its command line",
     "ps aux | grep cloudflared; "
     "cat /proc/$(pidof cloudflared 2>/dev/null || echo 0)/cmdline 2>/dev/null | tr '\\0' ' ' || echo 'process not found'"),
    ("Find YAML/JSON configs mentioning cloud",
     "find / -name '*.yml' -o -name '*.yaml' -o -name '*.json' 2>/dev/null | grep -i cloud"),
    ("Check /media/backup/init.d/",
     "cat /media/backup/configs/*/init.d/cloudflared.txt 2>/dev/null || echo 'no backup found'"),
]


async def main():
    transport = SSHTransport(host=HOST, username=USER, password=PASS)

    print(SEP)
    print("  CLOUDFLARED CONFIG DISCOVERY -- 192.168.162.20")
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
    print("  DISCOVERY COMPLETE")
    print(SEP)


if __name__ == "__main__":
    asyncio.run(main())
