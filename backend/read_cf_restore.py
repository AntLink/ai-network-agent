import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

OUT = open("cf_restore_out.txt", "w", encoding="utf-8", errors="replace")


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 30

    cmd = r"""echo "=== /media/backup/cloudflared/restore.sh ==="
cat /media/backup/cloudflared/restore.sh
echo ""
echo "=== /media/backup/restore.sh ==="
cat /media/backup/restore.sh
echo ""
echo "=== /media/TCI/ifplugdnet.sh (yang dipakai ifplugd) ==="
cat /media/TCI/ifplugdnet.sh
echo ""
echo "=== cek kelengkapan saat ini ==="
for f in /media/httpd/cgi-bin/cloudflared-linux-arm /media/httpd/cgi-bin/cloudflared /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared; do
  [ -e "$f" ] && echo "OK  $f" || echo "MISSING  $f"
done
[ -f /var/run/cloudflared.pid ] && echo "pidfile: $(cat /var/run/cloudflared.pid)" || echo "pidfile tidak ada"
true"""
    r = await t.run(cmd)
    OUT.write(r or "")
    OUT.close()
    print("written")


asyncio.run(main())
