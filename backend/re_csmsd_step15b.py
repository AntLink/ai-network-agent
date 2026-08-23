import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step15b_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


def hdr_hex(msg_type, ver):
    import struct
    b = struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, 0, 0)
    return "\\x" + "\\x".join(f"{x:02x}" for x in b)


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    settings.SSH_COMMAND_TIMEOUT = 45

    out("=" * 70)
    out("  STEP 15b: CHUNKED SWEEP types 0..127 ver=1 (16/chunk)")
    out("=" * 70)

    results = {}

    for chunk_start in range(0, 128, 16):
        lines = ["mkdir -p /tmp/sweep2", "cd /tmp/sweep2"]
        for t in range(chunk_start, chunk_start + 16):
            esc = hdr_hex(t, 1)
            # sequential, nc -w 2 max ~2s each -> worst 32s per chunk
            lines.append(
                f"printf '{esc}\\n' | nc -w 2 127.0.0.1 3302 2>/dev/null "
                f"| od -A n -t x1 | tr -d ' \\n' > t{t}.txt"
            )
        lines.append("echo CHUNKDONE")
        cmd = "\n".join(lines)
        try:
            r = await transport.run(cmd)
            if "CHUNKDONE" not in (r or ""):
                out(f"chunk {chunk_start}: no done marker: {(r or '')[:100]}")
        except Exception as e:
            out(f"chunk {chunk_start} ERROR: {type(e).__name__}: {e}")
            await asyncio.sleep(3)
            try:
                transport = SSHTransport(HOST, USER, PASS)
            except Exception:
                pass

    # collect summary
    try:
        summ = await transport.run(
            'cd /tmp/sweep2 && for f in $(ls -v *.txt); do t=${f%.txt}; '
            'resp=$(cat $f); echo "$t $resp"; done; true'
        )
        out("\nRAW RESULTS (type hexdata):")
        for line in (summ or "").splitlines():
            parts = line.split()
            if len(parts) == 2:
                t = int(parts[0])
                h = parts[1]
                if len(h) >= 32:
                    err = int(h[24:32], 16)
                    results[t] = (err, len(h) // 2)
                    mark = " <<< INTERESTING" if err != 5 else ""
                    out(f"  type {t:3d}: err={err} bytes={len(h)//2}{mark}")
                else:
                    results[t] = ("NORESP", len(h) // 2)
                    out(f"  type {t:3d}: NO RESPONSE ({len(h)//2} bytes)")
    except Exception as e:
        out(f"summary ERROR: {e}")

    out("\nINTERESTING TYPES (err != 5):")
    for t, v in sorted(results.items()):
        if v[0] != 5:
            out(f"  type {t}: {v}")

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)
    out("\n" + "=" * 70)
    out("  STEP 15b COMPLETE")
    out("=" * 70)


async def run(transport, label, cmd, timeout=30):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
