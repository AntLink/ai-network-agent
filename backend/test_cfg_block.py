import asyncio

import asyncssh

OUT = open("cfg_block_test_out.txt", "w", encoding="utf-8", errors="replace")


def p(s=""):
    OUT.write(str(s) + "\n")


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)

    async with conn:
        # ekstrak blok config jadi script terpisah
        r = await asyncio.wait_for(conn.run(
            'sed -n "/=== Config auto-restore/,/end config block/p" '
            "/media/TCI/ifplugdnet.sh > /tmp/cfg_block.sh; "
            "chmod +x /tmp/cfg_block.sh; wc -l /tmp/cfg_block.sh", check=False), timeout=30)
        p(f"[extract] {r.stdout.strip()}")

        p("\n=== TEST: jalankan blok config (fix-dns harus dibuat) ===")
        r = await asyncio.wait_for(conn.run("sh /tmp/cfg_block.sh 2>&1"), timeout=60)
        p(r.stdout or "(no output)")

        p("\n=== verifikasi fix-dns ===")
        r = await asyncio.wait_for(conn.run(
            "ls -la /etc/network/if-pre-up.d/fix-dns && cat /etc/network/if-pre-up.d/fix-dns",
            check=False), timeout=30)
        p(r.stdout or "")

        p("\n=== uji eksekusi fix-dns manual ===")
        r = await asyncio.wait_for(conn.run(
            "sh /etc/network/if-pre-up.d/fix-dns && cat /etc/resolv.conf", check=False), timeout=30)
        p(r.stdout or "")

        p("\n=== pastikan passwd/group tidak tersentuh (masih ada) ===")
        r = await asyncio.wait_for(conn.run(
            "wc -l /etc/passwd /etc/group; pidof cloudflared-linux-arm && echo TUNNEL_ALIVE",
            check=False), timeout=30)
        p(r.stdout or "")

    OUT.close()
    print("written")


asyncio.run(main())
