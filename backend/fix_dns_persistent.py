import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USERNAME = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
PASSWORD = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")


DNS_INIT_SCRIPT = """#!/bin/sh
### BEGIN INIT INFO
# Provides:          dns-setup
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Setup DNS resolv.conf
### END INIT INFO

RESOLV_FILE="/etc/resolv.conf"

if [ -f "$RESOLV_FILE" ]; then
    cp $RESOLV_FILE ${RESOLV_FILE}.bak
fi

cat > $RESOLV_FILE << 'DNS'
nameserver 1.1.1.1
nameserver 8.8.8.8
nameserver 192.168.162.1
DNS

echo "DNS configured: $(cat $RESOLV_FILE)"
"""

IF_PRE_UP_SCRIPT = """#!/bin/sh
echo "nameserver 1.1.1.1" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
echo "nameserver 192.168.162.1" >> /etc/resolv.conf
"""


async def run_cmd(ssh, label, cmd):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    try:
        output = await ssh.run(cmd)
        print(output)
        return True
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return False
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return False


async def write_file(ssh, label, remote_path, content):
    escaped = content.replace("'", "'\\''")
    return await run_cmd(ssh, label, f"cat > {remote_path} << 'PYEOF'\n{content}\nPYEOF")


async def main():
    ssh = SSHTransport(host=HOST, username=USERNAME, password=PASSWORD)
    print(f"Connected to {HOST} as {USERNAME}")

    # Step 1: Create /etc/init.d/dns-setup
    escaped_init = DNS_INIT_SCRIPT.replace("'", "'\\''")
    await run_cmd(ssh, "Step 1: Create /etc/init.d/dns-setup",
                  f"cat > /etc/init.d/dns-setup << 'EOF'\n{DNS_INIT_SCRIPT}\nEOF")

    # Step 2: chmod +x
    await run_cmd(ssh, "Step 2: chmod +x /etc/init.d/dns-setup",
                  "chmod +x /etc/init.d/dns-setup")

    # Step 3: Symlink rc5.d
    await run_cmd(ssh, "Step 3: Symlink /etc/rc5.d/S10dns-setup",
                  "mkdir -p /etc/rc5.d && ln -sf /etc/init.d/dns-setup /etc/rc5.d/S10dns-setup")

    # Step 4: Symlink rcS.d
    await run_cmd(ssh, "Step 4: Symlink /etc/rcS.d/S10dns-setup",
                  "mkdir -p /etc/rcS.d && ln -sf /etc/init.d/dns-setup /etc/rcS.d/S10dns-setup")

    # Step 5: Verify init.d and symlinks
    await run_cmd(ssh, "Step 5: Verify init.d and symlinks",
                  "ls -la /etc/init.d/dns-setup; ls -la /etc/rc5.d/S10dns-setup; ls -la /etc/rcS.d/S10dns-setup")

    # Step 6: Check /etc/network/interfaces
    await run_cmd(ssh, "Step 6: /etc/network/interfaces",
                  "cat /etc/network/interfaces")

    # Step 7: Check resolv.conf type
    await run_cmd(ssh, "Step 7: resolv.conf type",
                  "ls -la /etc/resolv.conf")

    # Step 8: Create if-pre-up.d/fix-dns
    await run_cmd(ssh, "Step 8: Create /etc/network/if-pre-up.d/fix-dns",
                  f"mkdir -p /etc/network/if-pre-up.d && cat > /etc/network/if-pre-up.d/fix-dns << 'INNEREOF'\n{IF_PRE_UP_SCRIPT}\nINNEREOF && chmod +x /etc/network/if-pre-up.d/fix-dns")

    # Step 9: Final verification
    await run_cmd(ssh, "Step 9a: /etc/init.d/dns-setup contents",
                  "cat /etc/init.d/dns-setup")
    await run_cmd(ssh, "Step 9b: rc5.d S10 symlinks",
                  "ls -la /etc/rc5.d/S10*")
    await run_cmd(ssh, "Step 9c: rcS.d S10 symlinks",
                  "ls -la /etc/rcS.d/S10*")
    await run_cmd(ssh, "Step 9d: if-pre-up.d/fix-dns",
                  "ls -la /etc/network/if-pre-up.d/fix-dns")
    await run_cmd(ssh, "Step 9e: Current /etc/resolv.conf",
                  "cat /etc/resolv.conf")

    print(f"\n{'='*60}")
    print("  DONE: DNS persistence configuration complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
