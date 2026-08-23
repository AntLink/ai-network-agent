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

LOG = open("re_csmsd_step17_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


def hdr_hex(msg_type, ver=0):
    import struct
    b = struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, 0, 0)
    return "\\x" + "\\x".join(f"{x:02x}" for x in b)


async def main():
    out("=" * 70)
    out("  STEP 17: SWEEP v2 - types 0..255, ver=0, fresh connections")
    out("=" * 70)

    lines = ["#!/bin/sh", "mkdir -p /tmp/sweep3", "cd /tmp/sweep3", "rm -f t*.txt done.marker"]
    MAXT = 255
    for t in range(0, MAXT + 1):
        esc = hdr_hex(t, 0)
        lines.append(
            f"printf '{esc}\\n' | nc -w 1 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > t{t}.txt"
        )
    lines.append("touch done.marker")
    script = "\n".join(lines) + "\n"

    local_script = os.path.join(os.path.dirname(__file__), "sweep3.sh")
    with open(local_script, "w", newline="\n") as f:
        f.write(script)

    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        # kill old sweep + upload new
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_script, "/tmp/sweep3.sh")
        out("script uploaded")

        settings.SSH_COMMAND_TIMEOUT = 20
        r = await conn.run("pkill -f sweep2.sh 2>/dev/null; echo cleaned; true")
        out(r.stdout.strip())

        r = await conn.run(
            "setsid sh -c 'sh /tmp/sweep3.sh >/tmp/sweep3.out 2>&1 </dev/null &'; echo LAUNCHED; true"
        )
        out(r.stdout.strip())

        done = False
        for attempt in range(60):  # up to 10 min
            await asyncio.sleep(10)
            try:
                r = await conn.run(
                    "ls /tmp/sweep3/done.marker >/dev/null 2>&1 && echo DONE || "
                    "echo \"WAITING $(ls /tmp/sweep3/t*.txt 2>/dev/null | wc -l)/256\"; true"
                )
                txt = (r.stdout or "").strip()
                out(f"poll {attempt}: {txt}")
                if "DONE" in txt:
                    done = True
                    break
            except Exception as e:
                out(f"poll error: {type(e).__name__}")
                await asyncio.sleep(5)

        if not done:
            out("sweep incomplete - summarizing what exists")

        r = await conn.run(
            'cd /tmp/sweep3 && for f in $(ls -v t*.txt 2>/dev/null); do '
            't=$(echo $f | tr -dc "0-9"); resp=$(cat $f); '
            'if [ ${#resp} -ge 32 ]; then '
            'b6=$(echo $resp | cut -c25-26); b7=$(echo $resp | cut -c27-28); '
            'err=$(( 16#$b7$b6 )); echo "$t ERR=$err"; '
            'else echo "$t NORESP"; fi; done; true'
        )
        results = {}
        for line in (r.stdout or "").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].startswith("ERR="):
                results[int(parts[0])] = int(parts[1].split("=")[1])
            elif len(parts) == 2 and parts[1] == "NORESP":
                results[int(parts[0])] = None

        out("\nERROR MAP (type -> err):")
        by_err = {}
        for t in sorted(results):
            e = results[t]
            by_err.setdefault(e, []).append(t)
        for e, ts in sorted(by_err.items(), key=lambda kv: (kv[0] is None, kv[0])):
            label = "NORESP" if e is None else f"err={e}"
            out(f"  {label}: {ts}")

        r = await conn.run("pidof csmsd.elf || echo dead; true")
        out(f"\nhealth: {(r.stdout or '').strip()}")

    out("=" * 70)
    out("  STEP 17 COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
