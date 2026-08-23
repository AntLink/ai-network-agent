import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")

import asyncssh

COMMANDS = r"""
echo "=== Check /etc/passwd ==="
cat /etc/passwd | grep root

echo ""
echo "=== Check /etc/shadow ==="
cat /etc/shadow 2>/dev/null | grep root || echo "no shadow file or no access"

echo ""
echo "=== Check if /etc/passwd is symlink ==="
ls -la /etc/passwd
ls -la /etc/shadow 2>/dev/null || echo "no shadow"

echo ""
echo "=== Check /etc is on which filesystem ==="
df -h /etc
mount | grep -E "etc|rootfs"

echo ""
echo "=== Check the pass.cgi script ==="
cat /media/httpd/cgi-bin/pass.cgi

echo ""
echo "=== Check if there's a password backup ==="
find /media -name "*pass*" -o -name "*shadow*" 2>/dev/null

echo ""
echo "=== Check /var/run for volatile files ==="
ls -la /var/run/ | head -20

echo ""
echo "=== Check init.d for password scripts ==="
ls /etc/init.d/ | grep -i pass
"""


async def main():
    print("Connecting to 192.168.162.20 ...")
    try:
        async with asyncssh.connect(
            "192.168.162.20",
            port=22,
            username="root",
            password="815m1ll4h",
            known_hosts=None,
            connect_timeout=10,
        ) as conn:
            result = await asyncio.wait_for(
                conn.run(COMMANDS, check=False),
                timeout=30,
            )
            print("STDOUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            print(f"EXIT STATUS: {result.exit_status}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
