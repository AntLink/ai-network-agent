import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

OUT = open("re_csmsd_step30_out.txt", "w", encoding="utf-8", errors="replace")


def out(s):
    OUT.write(str(s) + "\n")
    OUT.flush()
    print(s)


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 50

    # official restart via helper script
    r = await t.run("/tmp/csmsd-restart.sh; sleep 5; pidof csmsd.elf || echo dead; true")
    out(f"restart: {r}")

    # patient poll: up to 4 min, also track process
    up = False
    for i in range(16):
        await asyncio.sleep(15)
        settings.SSH_COMMAND_TIMEOUT = 25
        r = await t.run(
            f"echo \"t={((i+1)*15)}s alive=$(pidof csmsd.elf | wc -w) listen=$(netstat -tlnp 2>/dev/null | grep -c csmsd)\"; true"
        )
        out((r or "").strip())
        if "listen=3" in r:
            up = True
            break

    if not up:
        settings.SSH_COMMAND_TIMEOUT = 30
        r = await t.run("pidof csmsd.elf || echo dead; tail -12 /tmp/csmsd_run.log 2>/dev/null; true")
        out(f"NOT UP. state:\n{r}")
        OUT.close()
        return

    # greeting probe on officially-launched daemon
    pkt = struct.pack("<IIHBBII", 0xD001, 0, 8565, 0, 0, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    settings.SSH_COMMAND_TIMEOUT = 70
    r = await t.run(
        f"""sleep 20
( printf '{esc}\\n'; sleep 6 ) | nc -w 10 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin
echo "reply $(wc -c < /tmp/reply.bin)B"; od -A x -t x1z /tmp/reply.bin | head -6
grep -aE "GREETING|MEASUREMENT" /media/tci/csms/log/*.log /tmp/csmsd_run.log 2>/dev/null | tail -6
true"""
    )
    out(f"greeting probe on official daemon:\n{r}")

    OUT.close()


asyncio.run(main())
