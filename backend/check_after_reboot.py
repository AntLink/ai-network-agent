import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")

from app.core.config import settings
from app.transports.ssh import SSHTransport

settings.SSH_COMMAND_TIMEOUT = 120

HOST = "192.168.162.20"
USER = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
PASS = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")

CHECK_COMMANDS = r"""
echo "=========================================="
echo "  POST-REBOOT CONFIGURATION CHECK"
echo "=========================================="

echo ""
echo "=== 1. DNS Configuration ==="
cat /etc/resolv.conf
echo ""
echo "DNS test:"
ping -c 1 1.1.1.1 2>/dev/null && echo "DNS: OK" || echo "DNS: FAILED"

echo ""
echo "=== 2. Password/Shadow ==="
cat /etc/shadow | grep root
echo ""
echo "Shadow backup on SD:"
ls -la /media/backup/system/shadow 2>/dev/null || echo "NO BACKUP!"

echo ""
echo "=== 3. Init Scripts ==="
echo "restore-shadow:"
ls -la /etc/init.d/restore-shadow 2>/dev/null || echo "MISSING!"
ls -la /etc/rcS.d/S05restore-shadow 2>/dev/null || echo "rcS.d MISSING!"
ls -la /etc/rc5.d/S05restore-shadow 2>/dev/null || echo "rc5.d MISSING!"

echo ""
echo "dns-setup:"
ls -la /etc/init.d/dns-setup 2>/dev/null || echo "MISSING!"
ls -la /etc/rcS.d/S10dns-setup 2>/dev/null || echo "rcS.d MISSING!"
ls -la /etc/rc5.d/S10dns-setup 2>/dev/null || echo "rc5.d MISSING!"

echo ""
echo "cloudflared:"
ls -la /etc/init.d/cloudflared 2>/dev/null || echo "MISSING!"
ls -la /etc/rcS.d/S99cloudflared 2>/dev/null || echo "rcS.d MISSING!"
ls -la /etc/rc5.d/S99cloudflared 2>/dev/null || echo "rc5.d MISSING!"

echo ""
echo "=== 4. Cloudflared Tunnel ==="
ps aux | grep cloudflared | grep -v grep
echo ""
echo "Tunnel status:"
/etc/init.d/cloudflared status 2>/dev/null || echo "status check failed"

echo ""
echo "=== 5. pass.cgi ==="
ls -la /media/httpd/cgi-bin/pass.cgi 2>/dev/null || echo "MISSING!"
echo "Has backup logic:"
grep -c "backup" /media/httpd/cgi-bin/pass.cgi 2>/dev/null || echo "NO BACKUP LOGIC"

echo ""
echo "=== 6. Cloudflared Binary ==="
ls -la /media/httpd/cgi-bin/cloudflared-linux-arm 2>/dev/null || echo "MISSING!"
ls -la /media/httpd/cgi-bin/cloudflared 2>/dev/null || echo "Script MISSING!"

echo ""
echo "=== 7. Backup Files ==="
ls -la /media/backup/ 2>/dev/null || echo "NO BACKUP DIR!"
ls -la /media/backup/system/ 2>/dev/null || echo "NO SYSTEM BACKUP!"
ls -la /media/backup/cloudflared/ 2>/dev/null || echo "NO CLOUDFLARED BACKUP!"
ls -la /media/backup/configs/ 2>/dev/null || echo "NO CONFIGS BACKUP!"

echo ""
echo "=== 8. Network Config ==="
hostname
cat /etc/hostname
ip addr show | grep inet
ip route show

echo ""
echo "=== 9. Boot Order ==="
ls /etc/rcS.d/S0* /etc/rcS.d/S1* /etc/rcS.d/S9* 2>/dev/null

echo ""
echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
""".strip()


async def main():
    print(f"Connecting to {HOST} as {USER}...")
    transport = SSHTransport(HOST, USER, PASS)
    try:
        output = await transport.run(CHECK_COMMANDS)
        print(output)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
