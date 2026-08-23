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

LOG = open("re_csmsd_step16_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


def hdr_hex(msg_type, ver):
    import struct
    b = struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, 0, 0)
    return "\\x" + "\\x".join(f"{x:02x}" for x in b)


SWEEP_SCRIPT = """#!/bin/sh
# generic sweep: $1=port $2=ver $3=maxtype $4=outprefix
PORT=$1; VER=$2; MAXT=$3; PFX=$4
i=0
while [ $i -le $MAXT ]; do
  case $i in
    0) H="0000000000000000000000000000000000000000";;
    *)
      # build header via printf with computed type is hard in sh; use pre-generated file
      ;;
  esac
  i=$((i+1))
done
echo PLACEHOLDER
"""


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    settings.SSH_COMMAND_TIMEOUT = 30

    out("=" * 70)
    out("  STEP 16: BACKGROUND SWEEP via uploaded script")
    out("=" * 70)

    # generate per-type commands locally, upload as one script
    lines = ["#!/bin/sh", "mkdir -p /tmp/sweep2", "cd /tmp/sweep2", "rm -f t*.txt done.marker"]
    for t in range(0, 128):
        esc = hdr_hex(t, 1)
        lines.append(
            f"printf '{esc}\\n' | nc -w 1 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > t{t}.txt"
        )
    lines.append("touch done.marker")
    script = "\n".join(lines) + "\n"

    # upload via base64 through stdin (small enough: ~10KB)
    import base64
    b64 = base64.b64encode(script.encode()).decode()
    # chunk b64 into lines to avoid huge single line issues (~14KB total ok)
    r = await transport.run(f"echo {b64} | base64 -d > /tmp/sweep2.sh && chmod +x /tmp/sweep2.sh && echo UPLOADED; true")
    out(r)

    # launch detached
    r = await transport.run(
        "setsid sh -c 'sh /tmp/sweep2.sh >/tmp/sweep2.out 2>&1 </dev/null &'; echo LAUNCHED; true"
    )
    out(r)

    # poll for done marker
    for attempt in range(30):
        await asyncio.sleep(10)
        try:
            r = await transport.run("ls /tmp/sweep2/done.marker 2>/dev/null && echo DONE || echo WAITING; true")
            out(f"poll {attempt}: {r.strip()}")
            if "DONE" in r:
                break
        except Exception as e:
            out(f"poll {attempt} error: {e}")

    # summarize on device (compact)
    r = await transport.run(
        'cd /tmp/sweep2 && for f in $(ls -v t*.txt 2>/dev/null); do '
        't=$(echo $f | tr -dc "0-9"); resp=$(cat $f); '
        'if [ ${#resp} -ge 32 ]; then '
        'b6=$(echo $resp | cut -c25-26); b7=$(echo $resp | cut -c27-28); '
        'err=$(( 16#$b7$b6 )); echo "$t ERR=$err LEN=$(( ${#resp} / 2 ))"; '
        'else echo "$t NORESP ${#resp}"; fi; done; true'
    )
    out("\nRESULTS:")
    interesting = []
    for line in (r or "").splitlines():
        out(f"  {line}")
        if "ERR=" in line and "ERR=5" not in line:
            interesting.append(line)

    out("\nINTERESTING (err != 5):")
    for l in interesting:
        out(f"  {l}")

    r = await transport.run("pidof csmsd.elf || echo dead; true")
    out(f"\nhealth: {r.strip()}")
    out("=" * 70)
    out("  STEP 16 COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
