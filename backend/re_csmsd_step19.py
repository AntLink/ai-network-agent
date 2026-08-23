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

LOG = open("re_csmsd_step19_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


TYPES = [27, 28, 30, 31, 33, 34, 52, 53, 60, 61, 62, 66]
SUBTYPES = list(range(0, 49))


def hdr_hex(msg_type, subtype, ver=0):
    import struct
    b = struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, subtype, 0)
    return "\\x" + "\\x".join(f"{x:02x}" for x in b)


async def main():
    out("=" * 70)
    out("  STEP 19: 2D SWEEP - interesting types x subtypes 0..48")
    out("=" * 70)

    lines = ["#!/bin/sh", "mkdir -p /tmp/sweep5", "cd /tmp/sweep5", "rm -f r*.txt done.marker"]
    jobs = [(t, s) for t in TYPES for s in SUBTYPES]
    PAR = 3
    for start in range(0, len(jobs), PAR):
        batch = []
        for t, s in jobs[start:start + PAR]:
            esc = hdr_hex(t, s)
            batch.append(
                f"(printf '{esc}\\n' | timeout 2 nc 127.0.0.1 3302 2>/dev/null "
                f"| od -A n -t x1 | tr -d ' \\n' > r_{t}_{s}.txt) &"
            )
        lines.extend(batch)
        lines.append("wait")
    lines.append("touch done.marker")
    script = "\n".join(lines) + "\n"

    local_script = os.path.join(os.path.dirname(__file__), "sweep5.sh")
    with open(local_script, "w", newline="\n") as f:
        f.write(script)

    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_script, "/tmp/sweep5.sh")
        out(f"script uploaded ({len(jobs)} probes)")

        settings.SSH_COMMAND_TIMEOUT = 20
        await conn.run(
            "setsid sh -c 'sh /tmp/sweep5.sh >/tmp/sweep5.out 2>&1 </dev/null &'; echo LAUNCHED; true")

        done = False
        for attempt in range(90):
            await asyncio.sleep(10)
            try:
                r = await conn.run(
                    "ls /tmp/sweep5/done.marker >/dev/null 2>&1 && echo DONE || "
                    "echo \"WAITING $(ls /tmp/sweep5/r*.txt 2>/dev/null | wc -l)/%d\"; true" % len(jobs))
                txt = (r.stdout or "").strip()
                if attempt % 3 == 0 or "DONE" in txt:
                    out(f"poll {attempt}: {txt}")
                if "DONE" in txt:
                    done = True
                    break
            except Exception as e:
                out(f"poll error: {type(e).__name__}")
                await asyncio.sleep(5)
        out(f"sweep done: {done}")

        # summarize per (type): map subtype -> err
        r = await conn.run(
            'cd /tmp/sweep5 && for f in $(ls -v r_*.txt 2>/dev/null); do '
            'resp=$(cat $f); '
            'if [ ${#resp} -ge 32 ]; then '
            'b6=$(echo $resp | cut -c25-26); b7=$(echo $resp | cut -c27-28); '
            'err=$(( 16#$b7$b6 )); echo "$f ERR=$err"; '
            'else echo "$f NORESP"; fi; done; true'
        )
        grid = {}
        for line in (r.stdout or "").splitlines():
            parts = line.split()
            if len(parts) != 2:
                continue
            fname, val = parts
            _, ts, ss = fname.replace(".txt", "").split("_")
            t, s = int(ts), int(ss)
            if val == "NORESP":
                grid.setdefault(t, {})[s] = "NO"
            else:
                grid.setdefault(t, {})[s] = int(val.split("=")[1])

        for t in TYPES:
            g = grid.get(t, {})
            by_err = {}
            for s, e in sorted(g.items()):
                by_err.setdefault(e, []).append(s)
            summary = "; ".join(f"{k}:{v[:14]}{'...' if len(v)>14 else ''}" for k, v in sorted(by_err.items(), key=lambda kv: str(kv[0])))
            out(f"\ntype {t}: {summary}")

        # grab csmsd log tail - did anything react? (PING etc.)
        r = await conn.run("tail -15 /tmp/csmsd_run.log; true")
        out("\ncsmsd log tail:\n" + (r.stdout or ""))

        r = await conn.run("pidof csmsd.elf || echo dead; true")
        out(f"health: {(r.stdout or '').strip()}")

    out("=" * 70)
    out("  STEP 19 COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
