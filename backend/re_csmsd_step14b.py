import asyncio
import base64
import struct
import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step14b_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    settings.SSH_COMMAND_TIMEOUT = 30

    res = await transport.run("base64 /tmp/sweep_out.bin; true")
    data = base64.b64decode(res.strip())
    out(f"response bytes: {len(data)}")

    types = list(range(0, 512))
    n = len(data) // 20
    buckets = {}
    order = []
    for i in range(n):
        chunk = data[i * 20:(i + 1) * 20]
        msg_type = struct.unpack_from("<H", chunk, 8)[0]
        status = struct.unpack_from("<I", chunk, 12)[0]
        bodylen = struct.unpack_from("<I", chunk, 16)[0]
        req_type = types[i] if i < len(types) else -1
        key = (msg_type, status, bodylen)
        buckets.setdefault(key, []).append(req_type)
        order.append((req_type, msg_type, status, bodylen))

    out("\nsequential responses (reqType -> respType, err, bodyLen):")
    for row in order:
        marker = "  <<<" if row[2] != 5 else ""
        out(f"  type {row[0]:4d} -> resp={row[1]:#06x} err={row[2]} bodyLen={row[3]}{marker}")

    out("\nbuckets:")
    for k, v in sorted(buckets.items()):
        out(f"  {k}: {v[:30]}{'...' if len(v) > 30 else ''}")


if __name__ == "__main__":
    asyncio.run(main())
