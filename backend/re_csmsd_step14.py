import asyncio
import struct
import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

import asyncssh

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step14_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


def hdr(msg_type, ver=0, status=0, bodylen=0):
    return struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, status, bodylen) + b"\n"


async def main():
    out("=" * 70)
    out("  STEP 14: SFTP-BASED FULL TYPE SWEEP ON PORT 3302")
    out("=" * 70)

    # ---- build payload: types 0..511 ----------------------------------------
    types = list(range(0, 512))
    payload = b"".join(hdr(t) for t in types)
    local_bin = os.path.join(os.path.dirname(__file__), "sweep_payload.bin")
    with open(local_bin, "wb") as f:
        f.write(payload)
    out(f"payload built: {len(payload)} bytes for {len(types)} message types")

    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_bin, "/tmp/sweep_payload.bin")
            out("payload uploaded")

        settings.SSH_COMMAND_TIMEOUT = 60
        res = await conn.run(
            "timeout 25 nc 127.0.0.1 3302 < /tmp/sweep_payload.bin > /tmp/sweep_out.bin; "
            "echo rc=$?; wc -c /tmp/sweep_out.bin",
            check=False,
        )
        out(res.stdout)

        await sftp.get("/tmp/sweep_out.bin", os.path.join(os.path.dirname(__file__), "sweep_out.bin"))
        out("output downloaded")

    # ---- parse responses ------------------------------------------------------
    data = open(os.path.join(os.path.dirname(__file__), "sweep_out.bin"), "rb").read()
    out(f"response bytes: {len(data)}")
    n = len(data) // 20
    buckets = {}
    for i in range(n):
        chunk = data[i * 20:(i + 1) * 20]
        if len(chunk) < 20:
            break
        msg_type, status = struct.unpack_from("<H", chunk, 8)[0], struct.unpack_from("<I", chunk, 12)[0]
        bodylen = struct.unpack_from("<I", chunk, 16)[0]
        key = (msg_type, status, bodylen)
        buckets.setdefault(key, []).append(types[i] if i < len(types) else "?")

    out("\nresponse buckets (respType, errorCode, bodyLen): [request types...]")
    for key, reqs in sorted(buckets.items()):
        preview = reqs[:20]
        suffix = f" ... (+{len(reqs)-20} more)" if len(reqs) > 20 else ""
        out(f"  {key}: {preview}{suffix}")

    # non-standard responses deserve attention
    interesting = [(k, v) for k, v in buckets.items() if k[0] != 0x270F or k[1] not in (5,) or k[2] != 0]
    out("\nINTERESTING (non generic-error):")
    for k, v in interesting:
        out(f"  {k}: types {v[:40]}")

    out("\n" + "=" * 70)
    out("  STEP 14 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
