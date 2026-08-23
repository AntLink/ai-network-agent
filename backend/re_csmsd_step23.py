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

CMDS = {
    "shm files": "ls -la /dev/shm/ 2>/dev/null",
    "shm dump (first bytes)": "od -A x -t x1z /dev/shm/Global.TCI.ShMem3230 2>/dev/null | head -10",
    "db size + tables": """ls -la /media/tci/csms/data/*.db 2>/dev/null
strings /media/tci/csms/data/csmsdb.db | grep -c CREATE TABLE
true""",
    "db row counts": """strings /media/tci/csms/data/csmsdb.db | grep -E "^INSERT|^\\{" | head -5
ls -la /media/tci/csms/data/
true""",
}


async def main():
    t = SSHTransport(HOST, USER, PASS)
    settings.SSH_COMMAND_TIMEOUT = 25
    for label, cmd in CMDS.items():
        print(f"\n===== {label} =====")
        try:
            r = await t.run(cmd + "; true")
            print(r if r.strip() else "(empty)")
        except Exception as e:
            print(f"ERROR: {e}")


asyncio.run(main())
