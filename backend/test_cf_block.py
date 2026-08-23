import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

import asyncssh

OUT = open("cf_block_test_out.txt", "w", encoding="utf-8", errors="replace")


def p(s=""):
    OUT.write(str(s) + "\n")


async def run(conn, cmd, timeout=60):
    r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=timeout)
    return r.stdout or ""


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)

    async with conn:
        # ekstrak blok cloudflared dari ifplugdnet.sh jadi script test terpisah
        r = await run(conn,
            'sed -n "/=== Cloudflared auto-restore/,/end cloudflared block/p" '
            '/media/TCI/ifplugdnet.sh > /tmp/cf_block.sh; '
            'chmod +x /tmp/cf_block.sh; wc -l /tmp/cf_block.sh')
        p(f"[extract] {r.strip()}")

        p("\n=== TEST 1: kondisi normal (semua ada, tunnel jalan) ===")
        r = await run(conn, "sh -x /tmp/cf_block.sh 2>&1 | tail -12")
        p(r)
        r = await run(conn, "pidof cloudflared-linux-arm && echo TUNNEL_ALIVE || echo TUNNEL_DEAD")
        p(r)

        p("\n=== TEST 2: simulasi hilang - rename launcher+init ===")
        r = await run(conn,
            "mv /media/httpd/cgi-bin/cloudflared /tmp/cf_launcher.saved && "
            "mv /etc/init.d/cloudflared /tmp/cf_initd.saved && "
            "rm -f /etc/rc5.d/S99cloudflared && echo moved")
        p(r)
        r = await run(conn, "sh /tmp/cf_block.sh 2>&1 | tail -12", timeout=90)
        p(r)

        p("=== verifikasi pasca restore ===")
        r = await run(conn,
            """for f in /media/httpd/cgi-bin/cloudflared-linux-arm /media/httpd/cgi-bin/cloudflared /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared; do
  [ -e "$f" ] && echo "OK  $f" || echo "MISSING  $f"
done
sleep 2
pidof cloudflared-linux-arm && echo TUNNEL_ALIVE || echo TUNNEL_DEAD
ls -la /tmp/cf_launcher.saved /tmp/cf_initd.saved""")
        p(r)

    OUT.close()
    print("written")


asyncio.run(main())
