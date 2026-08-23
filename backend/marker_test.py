import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def probe(t, label, pkt):
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    settings.SSH_COMMAND_TIMEOUT = 45
    try:
        r = await t.run(
            f"""rm -f /tmp/reply.bin
( printf '{esc}\\n'; sleep 5 ) | nc -w 9 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin
echo "bytes=$(wc -c < /tmp/reply.bin)"
od -A x -t x1z /tmp/reply.bin | head -6
grep -acE "GREETING|MEASUREMENT_PAN" /tmp/csmsd_run.log
true"""
        )
        print(f"--- {label} ---")
        print(r)
    except Exception as e:
        print(f"--- {label} --- ERROR {e}")


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")

    # A: marker ZERO (exact replica of successful step26-C)
    pktA = struct.pack("<IIHBBII", 0, 0, 8565, 0, 0, 0, 36) + b"\x00" * 36
    await probe(t, "greet marker=0 body=36", pktA)

    # B: marker NONZERO otherwise identical
    pktB = struct.pack("<IIHBBII", 0xDEAD, 0, 8565, 0, 0, 0, 36) + b"\x00" * 36
    await probe(t, "greet marker=0xDEAD body=36", pktB)


asyncio.run(main())
