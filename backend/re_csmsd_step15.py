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

LOG = open("re_csmsd_step15_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=60):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except asyncio.TimeoutError:
        out(f"(TIMEOUT after {timeout}s)")
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def hdr_hex(msg_type, ver):
    import struct
    b = struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, 0, 0)
    return "\\x" + "\\x".join(f"{x:02x}" for x in b)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 15: PARALLEL FRESH-CONNECTION SWEEP types 0..127 ver=1")
    out("=" * 70)

    # generate script on device: for each type, fresh nc, save od output
    lines = ["mkdir -p /tmp/sweep2", "cd /tmp/sweep2", "rm -f *"]
    MAX = 128
    PAR = 4
    for start in range(0, MAX, PAR):
        batch = []
        for t in range(start, start + PAR):
            esc = hdr_hex(t, 1)
            batch.append(
                f"(printf '{esc}\\n' | nc -w 2 127.0.0.1 3302 2>/dev/null "
                f"| od -A n -t x1 | tr -d ' \\n' > t{t}.txt) &"
            )
        lines.extend(batch)
        lines.append("wait")
        lines.append("sleep 0.3")
    lines.append("echo SWEEPDONE")
    cmd = "\n".join(lines) + "\ntrue"

    await run(transport, "RUN SWEEP (parallel batches)", cmd, timeout=200)

    # summarize
    await run(
        transport,
        "SUMMARIZE",
        """cd /tmp/sweep2
for f in $(ls -v *.txt 2>/dev/null); do
  t=${f%.txt}
  sz=$(wc -c < $f)
  if [ "$sz" -ge 24 ]; then
    resp=$(cat $f)
    # extract err code: bytes 12-15 little endian -> parse hex chars 24..32
    errhex=$(echo $resp | cut -c25-32)
    b6=${errhex:6:2}; b7=${errhex:7:2}
    echo "type=$t err=$((0x$b7$b6)) len=$sz"
  else
    echo "type=$t NORESPONSE len=$sz"
  fi
done
true""",
        timeout=60,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 15 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
