import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

OUT = open("cf_check_out.txt", "w", encoding="utf-8", errors="replace")


def p(s=""):
    OUT.write(str(s) + "\n")


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 40

    cmd = r"""echo "=== proses cloudflared ==="
ps | grep -i cloudflared | grep -v grep || echo "TIDAK JALAN"
cat /proc/$(pidof cloudflared-linux-arm)/cmdline 2>/dev/null | tr '\0' ' '; echo ""

echo "=== S99cloudflared ==="
cat /etc/init.d/cloudflared 2>/dev/null || echo "tidak ada"

echo "=== launcher di cgi-bin ==="
head -40 /media/httpd/cgi-bin/cloudflared 2>/dev/null

echo "=== lokasi konfigurasi umum ==="
ls -la /etc/cloudflared/ 2>/dev/null || echo "/etc/cloudflared tidak ada"
ls -la /root/.cloudflared/ 2>/dev/null || echo "/root/.cloudflared tidak ada"
ls -la /media/tci/cloudflared* /media/TCI/cloudflared* 2>/dev/null
find / -name "config.yml" -path "*cloud*" 2>/dev/null | head -5
find / -name "*.pem" -path "*cloud*" 2>/dev/null | head -5

echo "=== /media/backup ==="
ls -laR /media/backup 2>/dev/null | head -60

echo "=== log cloudflared terakhir ==="
grep -i cloudflared /var/volatile/log/messages 2>/dev/null | tail -8"""
    try:
        r = await t.run(cmd)
        p(r)
    except Exception as e:
        p(f"ERROR: {e}")
    OUT.close()
    print("written")


asyncio.run(main())
