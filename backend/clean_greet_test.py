import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")

    # restart clean
    settings.SSH_COMMAND_TIMEOUT = 40
    r = await t.run(
        """killall -9 csmsd.elf 2>/dev/null; sleep 1
rm -f /media/tci/csms/csmsd.pid /tmp/csmsd_run.log
setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
echo relaunched""",
        check=False,
    ) if False else None

    import struct
    from app.core.config import settings as s

    async def run_cmd(cmd, timeout=40):
        s.SSH_COMMAND_TIMEOUT = timeout
        return await t.run(cmd)

    await run_cmd(
        """killall -9 csmsd.elf 2>/dev/null; sleep 1
rm -f /media/tci/csms/csmsd.pid /tmp/csmsd_run.log
setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
echo relaunched
true"""
    )

    # wait for ports
    for i in range(12):
        await asyncio.sleep(15)
        r = await run_cmd("netstat -tlnp 2>/dev/null | grep -c csmsd; true", timeout=25)
        n = int((r or "0").strip() or 0)
        print(f"t={(i+1)*15}s listeners={n}")
        if n >= 3:
            break

    # clean single greeting: FIRST client ever
    pkt = struct.pack("<IIHBBII", 0xC001, 0, 8565, 0, 1, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    r = await run_cmd(
        f"""sleep 5
grep -a GREETING /tmp/csmsd_run.log | wc -l
( printf '{esc}\\n'; sleep 5 ) | nc -w 10 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
grep -aE "GREETING|priority" /tmp/csmsd_run.log | tail -5
true""",
        timeout=60,
    )
    print(r)


asyncio.run(main())
