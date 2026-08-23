import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

OUT = open("re_csmsd_step29_out.txt", "w", encoding="utf-8", errors="replace")


def out(s):
    OUT.write(str(s) + "\n")
    OUT.flush()
    print(s)


def hdr(msg_type, subtype=0, ver=0, bodylen=0, marker=0):
    return struct.pack("<IIHBBII", marker, 0, msg_type, ver, 0, subtype, bodylen)


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 60

    g0 = hdr(8565)
    p0 = hdr(8563)

    def esc(b):
        h = b.hex()
        return "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))

    # EXP1: exact step26 replication - greet(nobody) + pan(nobody), one conn
    r = await t.run(f"""rm -f /tmp/reply.bin
( printf '{esc(g0)}\\n'; sleep 2; printf '{esc(p0)}\\n'; sleep 9 ) | nc -w 14 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin &
sleep 14
echo "EXP1 reply $(wc -c < /tmp/reply.bin)B:"; od -A x -t x1z /tmp/reply.bin | head -6
echo '--- new log ---'
tail -40 /tmp/csmsd_run.log | grep -aE "GREETING|PAN|version|Metrics"
true""")
    out("=== EXP1: greet+pan one conn ===")
    out(r)

    # EXP2: greet alone nobody
    r = await t.run(f"""rm -f /tmp/reply.bin
( printf '{esc(g0)}\\n'; sleep 9 ) | nc -w 12 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin &
sleep 12
echo "EXP2 reply $(wc -c < /tmp/reply.bin)B:"; od -A x -t x1z /tmp/reply.bin | head -6
echo '--- new log ---'
tail -20 /tmp/csmsd_run.log | grep -aE "GREETING|PAN|version|Metrics"
true""")
    out("\n=== EXP2: greet only ===")
    out(r)

    # historical bad-version grep
    r = await t.run('grep -acE "bad version" /tmp/csmsd_run.log; grep -aE "bad version" /tmp/csmsd_run.log | tail -4; true')
    out("\n=== bad version history ===")
    out(r)

    OUT.close()


asyncio.run(main())
