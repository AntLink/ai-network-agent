import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

OUT = open("re_csmsd_step31_out.txt", "w", encoding="utf-8", errors="replace")


def out(s):
    OUT.write(str(s) + "\n")
    OUT.flush()
    print(s)


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")

    settings.SSH_COMMAND_TIMEOUT = 40
    r = await t.run(
        """killall -9 csmsd.elf 2>/dev/null; sleep 1
rm -f /media/tci/csms/csmsd.pid /tmp/csmsd_run.log
cd /
setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
echo relaunched-from-root-cwd
true"""
    )
    out(f"{r}")

    up = False
    for i in range(10):
        await asyncio.sleep(15)
        settings.SSH_COMMAND_TIMEOUT = 25
        r = await t.run("netstat -tlnp 2>/dev/null | grep -c csmsd; true")
        n = int((r or "0").strip() or 0)
        out(f"t={(i+1)*15}s listeners={n}")
        if n >= 3:
            up = True
            break

    if not up:
        out("never came up")
        OUT.close()
        return

    # EXTRA settle time
    out("waiting extra 240s for full init...")
    await asyncio.sleep(240)

    pkt = struct.pack("<IIHBBII", 0xE001, 0, 8565, 0, 0, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    settings.SSH_COMMAND_TIMEOUT = 60
    r = await t.run(
        f"""( printf '{esc}\\n'; sleep 6 ) | nc -w 10 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin
echo "reply $(wc -c < /tmp/reply.bin)B"; od -A x -t x1z /tmp/reply.bin | head -8
grep -aE "GREETING|MEASUREMENT|priority" /tmp/csmsd_run.log | tail -6
true"""
    )
    out(f"greeting after long settle:\n{r}")
    OUT.close()


asyncio.run(main())
