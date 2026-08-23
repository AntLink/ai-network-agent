import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step28c_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


def hdr(msg_type, subtype=0, ver=0, bodylen=0, marker=0, rver=0):
    return struct.pack("<IIHBBII", marker, 0, msg_type, ver, rver, subtype, bodylen)


async def main():
    transport = None
    settings.SSH_COMMAND_TIMEOUT = 25
    settings.SSH_CONNECT_TIMEOUT = 20

    out("=" * 70)
    out("  STEP 28c: SLOW-PACED GREETING MATRIX (single persistent SSH conn)")
    out("=" * 70)

    from app.transports.ssh import SSHTransport as T
    transport = T(HOST, USER, PASS)

    combos = [(0, 1), (0, 2), (1, 1)]
    for (a, b) in combos:
        marker = 0xA000 + a * 16 + b
        pkt = hdr(8565, ver=a, bodylen=36, marker=marker, rver=b) + b"\x00" * 36
        h = pkt.hex()
        escs = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
        cmd = (
            f"( printf '{escs}\\n'; sleep 4 ) | nc -w 8 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n'"
        )
        try:
            r = await transport.run(cmd)
            resp = (r or "").strip()
            if len(resp) >= 40:
                errh = resp[24:32]
                err = int(errh[6:] + errh[4:6], 16)
                echo = int(resp[0:8], 16)
                mtype = int(resp[16:20], 16)
                out(f"greet A={a} B={b}: {len(resp)//2}B type={mtype} echo=0x{echo:x} err={err}")
            else:
                out(f"greet A={a} B={b}: SILENT")
        except Exception as e:
            out(f"greet A={a} B={b}: ERROR {type(e).__name__}; reconnecting...")
            try:
                transport = T(HOST, USER, PASS)
            except Exception as e2:
                out(f"reconnect failed: {e2}")
                break
        await asyncio.sleep(3)

    # pan after greeting in same connection style: greet then pan sequential same nc
    g = hdr(8565, bodylen=36) + b"\x00" * 36
    p = hdr(8563, ver=0, bodylen=36, marker=0xBEEF) + b"\x00" * 36
    hg, hp = g.hex(), p.hex()
    eg = "\\x" + "\\x".join(hg[i:i+2] for i in range(0, len(hg), 2))
    ep = "\\x" + "\\x".join(hp[i:i+2] for i in range(0, len(hp), 2))
    cmd = (
        f"( printf '{eg}\\n'; sleep 3; printf '{ep}\\n'; sleep 6 ) "
        f"| nc -w 12 127.0.0.1 3302 2>/dev/null > /tmp/seq.bin &"
    )
    settings.SSH_COMMAND_TIMEOUT = 40
    try:
        await transport.run(cmd + "\nsleep 14\nwc -c /tmp/seq.bin; od -A x -t x1z /tmp/seq.bin | head -30; true")
        out("sequence test done (see output above)")
    except Exception as e:
        out(f"seq ERROR: {e}")

    out("\ndone")


if __name__ == "__main__":
    asyncio.run(main())
