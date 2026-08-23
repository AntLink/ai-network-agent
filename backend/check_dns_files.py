import asyncio

import asyncssh

OUT = open("cf_dns_detail_out.txt", "w", encoding="utf-8", errors="replace")


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)
    async with conn:
        cmd = r"""BK=/media/backup/configs/20260820-191015
echo "=== backup: fix-dns.txt ==="
cat $BK/network/fix-dns.txt
echo ""
echo "=== backup: dns-setup.txt ==="
cat $BK/init.d/dns-setup.txt
echo ""
echo "=== current dns-setup (full) ==="
cat /etc/init.d/dns-setup
echo ""
echo "=== rc link untuk dns-setup ==="
ls -la /etc/rc5.d/ | grep -i dns || echo "tidak ada link dns-setup di rc5.d"
true"""
        r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=40)
        OUT.write(r.stdout or "")
    OUT.close()
    print("written")


asyncio.run(main())
