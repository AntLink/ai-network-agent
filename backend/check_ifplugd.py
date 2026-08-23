import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 30

    cmd = r"""echo "=== isi ifplugdnet.sh ==="
cat /media/httpd/cgi-bin/ifplugdnet.sh
echo ""
echo "=== siapa memanggil ifplugdnet? ==="
grep -rn "ifplugd" /etc/init.d/ /etc/rcS.d/ /etc/rc5.d/ /etc/inittab /etc/profile 2>/dev/null | head -20
echo ""
echo "=== urutan boot rcS.d & rc5.d ==="
ls -la /etc/rcS.d/ 2>/dev/null | head -30
echo "---"
ls -la /etc/rc5.d/ 2>/dev/null | head -30
echo ""
echo "=== proses ifplugd berjalan? ==="
ps | grep -i ifplug | grep -v grep || echo "tidak jalan"
true"""
    r = await t.run(cmd)
    print(r)


asyncio.run(main())
