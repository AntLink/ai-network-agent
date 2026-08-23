import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USERNAME = "root"
PASSWORD = "815m1ll4h"

COMMANDS = [
    ("SOURCE 1a: SQLite DB files", "ls -la /media/tci/csms/data/*.db 2>&1 || true"),
    ("SOURCE 1b: SQLite tables", 'sqlite3 /media/tci/csms/data/csmsdb.db ".tables" 2>/dev/null || echo "no sqlite3"'),
    ("SOURCE 1c: SQLite strings (freq/signal/spectrum/power/dBm/MHz)",
     'strings /media/tci/csms/data/csmsdb.db 2>/dev/null | grep -iE "freq|signal|spectrum|power|dBm|MHz" | head -30 || true'),
    ("SOURCE 2a: Data directory listing", "ls -la /media/tci/csms/data/ 2>&1 || true"),
    ("SOURCE 2b: Find .dat/.bin/.raw/.csv files",
     'find /media/tci -name "*.dat" -o -name "*.bin" -o -name "*.raw" -o -name "*.csv" 2>/dev/null || true'),
    ("SOURCE 2c: Find spectrum/sweep/signal files",
     'find /media/tci -name "*spectrum*" -o -name "*sweep*" -o -name "*signal*" 2>/dev/null || true'),
    ("SOURCE 3a: Monitor UDP :18331 (5s capture, hex dump)",
     'timeout 5 cat /dev/udp/localhost/18331 2>/dev/null | xxd | head -30 || echo "UDP read failed"'),
    ("SOURCE 3b: UDP :18331 listener check", "netstat -ulnp 2>/dev/null | grep 18331 || echo 'nothing listening on 18331'"),
]


async def main():
    print(f"Connecting to {HOST} as {USERNAME}...")
    transport = SSHTransport(HOST, USERNAME, PASSWORD)
    for label, cmd in COMMANDS:
        print()
        print("=" * 70)
        print(f"[{label}]")
        print(f"$ {cmd}")
        print("-" * 70)
        try:
            out = await transport.run(cmd)
            print(out if out.strip() else "(no output)")
        except Exception as e:
            print(f"ERROR: {e}")
    print()
    print("=" * 70)
    print("DONE")


asyncio.run(main())
