import asyncio
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

LOG = open("re_csmsd_step16b_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("=" * 70)
    out("  STEP 16b: SFTP UPLOAD + DETACHED SWEEP")
    out("=" * 70)

    lines = ["#!/bin/sh", "mkdir -p /tmp/sweep2", "cd /tmp/sweep2", "rm -f t*.txt done.marker"]
    for t in range(0, 128):
        esc = hdr_hex(t, 1)
        lines.append(
            f"printf '{esc}\\n' | nc -w 1 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > t{t}.txt"
        )
    lines.append("touch done.marker")
    script = "\n".join(lines) + "\n"

    local_script = os.path.join(os.path.dirname(__file__), "sweep2.sh")
    with open(local_script, "w", newline="\n") as f:
        f.write(script)

    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_script, "/tmp/sweep2.sh")
        out("script uploaded")

        settings.SSH_COMMAND_TIMEOUT = 20
        r = await conn.run("chmod +x /tmp/sweep2.sh && head -3 /tmp/sweep2.sh && wc -l /tmp/sweep2.sh; true")
        out(r.stdout)

        r = await conn.run(
            "setsid sh -c 'sh /tmp/sweep2.sh >/tmp/sweep2.out 2>&1 </dev/null &'; echo LAUNCHED; true"
        )
        out(r.stdout.strip())

        done = False
        for attempt in range(40):
            await asyncio.sleep(10)
            try:
                r = await conn.run("ls /tmp/sweep2/done.marker >/dev/null 2>&1 && echo DONE || echo WAITING; true")
                out(f"poll {attempt}: {(r.stdout or '').strip()}")
                if "DONE" in (r.stdout or ""):
                    done = True
                    break
            except Exception as e:
                out(f"poll error: {type(e).__name__}")

        if not done:
            out("sweep did not finish in time")

        # compact summary via device-side processing
        r = await conn.run(
            'cd /tmp/sweep2 && for f in $(ls -v t*.txt 2>/dev/null); do '
            't=$(echo $f | tr -dc "0-9"); resp=$(cat $f); '
            'if [ ${#resp} -ge 32 ]; then '
            'b6=$(echo $resp | cut -c25-26); b7=$(echo $resp | cut -c27-28); '
            'err=$(( 16#$b7$b6 )); echo "$t ERR=$err LEN=$(( ${#resp} / 2 ))"; '
            'else echo "$t NORESP"; fi; done; true'
        )
        out("\nRESULTS:")
        interesting = []
        for line in (r.stdout or "").splitlines():
            out(f"  {line}")
            if "ERR=" in line and "ERR=5" not in line and "NORESP" not in line:
                interesting.append(line)

        out("\nINTERESTING (err != 5):")
        for l in interesting:
            out(f"  {l}")

        r = await conn.run("pidof csmsd.elf || echo dead; true")
        out(f"\nhealth: {(r.stdout or '').strip()}")

    out("=" * 70)
    out("  STEP 16b COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
