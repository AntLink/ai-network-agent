"""Fix all configurations on the embedded Linux system and get cloudflared tunnel working."""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.transports.ssh import SSHTransport
from app.core import config

COMMAND_TIMEOUT = 120
config.settings.SSH_COMMAND_TIMEOUT = COMMAND_TIMEOUT

HOST = "192.168.162.20"
USERNAME = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
PASSWORD = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")


async def main():
    ssh = SSHTransport(HOST, USERNAME, PASSWORD)

    cmd = r"""
echo "=========================================="
echo "  FIXING ALL CONFIGURATIONS"
echo "=========================================="

# Step 1: Fix DNS
echo ""
echo "=== Step 1: Fix DNS ==="
echo "nameserver 1.1.1.1" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
echo "nameserver 192.168.162.1" >> /etc/resolv.conf
cat /etc/resolv.conf
ping -c 1 cloudflared.com && echo "DNS: OK" || echo "DNS: FAILED"

# Step 2: Restore shadow
echo ""
echo "=== Step 2: Restore Password ==="
if [ -f /media/backup/system/shadow ]; then
  cp /media/backup/system/shadow /etc/shadow
  cp /media/backup/system/passwd /etc/passwd
  cp /media/backup/system/group /etc/group
  chmod 640 /etc/shadow
  chmod 644 /etc/passwd /etc/group
  echo "Password restored: $(cat /etc/shadow | grep root | cut -d: -f1)"
else
  echo "No shadow backup found!"
fi

# Step 3: Copy all scripts from SD card to /etc/init.d
echo ""
echo "=== Step 3: Copy Scripts from SD Card ==="
if [ -d /media/scripts/init.d ]; then
  for script in /media/scripts/init.d/*; do
    name=$(basename $script)
    cp $script /etc/init.d/$name
    chmod +x /etc/init.d/$name
    echo "Copied: $name"
  done
else
  echo "No scripts on SD card! Creating them..."
  mkdir -p /media/scripts/init.d
  
  # Create setup-boot
  printf '#!/bin/sh\necho "Boot setup from SD"\n' > /media/scripts/init.d/setup-boot
  chmod +x /media/scripts/init.d/setup-boot
fi

# Step 4: Create symlinks
echo ""
echo "=== Step 4: Create Boot Symlinks ==="
ln -sf /etc/init.d/setup-boot /etc/rcS.d/S01setup-boot
ln -sf /etc/init.d/restore-shadow /etc/rcS.d/S05restore-shadow
ln -sf /etc/init.d/dns-setup /etc/rcS.d/S10dns-setup
ln -sf /etc/init.d/cloudflared /etc/rcS.d/S99cloudflared
ln -sf /etc/init.d/setup-boot /etc/rc5.d/S01setup-boot
ln -sf /etc/init.d/restore-shadow /etc/rc5.d/S05restore-shadow
ln -sf /etc/init.d/dns-setup /etc/rc5.d/S10dns-setup
ln -sf /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared
echo "Symlinks created"

# Step 5: Stop any existing cloudflared
echo ""
echo "=== Step 5: Stop Existing Cloudflared ==="
/media/httpd/cgi-bin/cloudflared stop 2>/dev/null
sleep 2
rm -f /var/run/cloudflared.pid
echo "Stopped"

# Step 6: Start cloudflared
echo ""
echo "=== Step 6: Start Cloudflared ==="
/media/httpd/cgi-bin/cloudflared start
sleep 5

# Step 7: Verify
echo ""
echo "=== Step 7: Verification ==="
echo "--- DNS ---"
cat /etc/resolv.conf
echo ""
echo "--- Password ---"
cat /etc/shadow | grep root
echo ""
echo "--- Init Scripts ---"
ls -la /etc/init.d/restore-shadow /etc/init.d/dns-setup /etc/init.d/cloudflared /etc/init.d/setup-boot 2>/dev/null
echo ""
echo "--- Boot Symlinks ---"
ls -la /etc/rcS.d/S0* /etc/rcS.d/S1* /etc/rcS.d/S9* 2>/dev/null
echo ""
echo "--- Cloudflared Process ---"
ps aux | grep cloudflared | grep -v grep
echo ""
echo "--- Cloudflared Ports ---"
netstat -tlnp 2>/dev/null | grep -E "cloudflared|7844|20241" || echo "checking..."
echo ""
echo "--- SD Card Scripts ---"
ls -la /media/scripts/init.d/
echo ""
echo "--- Test Tunnel ---"
ping -c 1 1.1.1.1 && echo "Internet: OK" || echo "Internet: FAILED"

echo ""
echo "=========================================="
echo "  DONE"
echo "=========================================="
""".strip()

    print(f"Connecting to {HOST} as {USERNAME}...")
    print(f"Command timeout: {COMMAND_TIMEOUT}s\n")

    try:
        output = await ssh.run(cmd)
        print(output)
    except RuntimeError as e:
        print(f"ERROR (non-zero exit): {e}")
        sys.exit(1)
    except Exception as e:
        print(f"CONNECTION/EXECUTION ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
