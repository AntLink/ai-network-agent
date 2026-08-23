import asyncio

import asyncssh


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)
    async with conn:
        cmd = (
            "rm -f /tmp/cf_launcher.saved /tmp/cf_initd.saved /tmp/cf_block.sh /tmp/ifplugdnet.sh.new; "
            "echo cleaned; "
            'echo "--- struktur akhir ifplugdnet.sh ---"; '
            'grep -n -E "cloudflared|S99csmsd" /media/TCI/ifplugdnet.sh | head -14; '
            "echo '--- proses tunnel ---'; pidof cloudflared-linux-arm && echo ALIVE"
        )
        r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=30)
        print(r.stdout)


asyncio.run(main())
