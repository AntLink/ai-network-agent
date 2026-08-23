import asyncio
import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

import asyncssh

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

DEST = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf\csmsdb_copy.db"


async def main():
    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        # make a consistent snapshot on device first (cp is fine; sqlite tolerates)
        r = await conn.run("cp /media/tci/csms/data/csmsdb.db /tmp/csmsdb_snap.db && sync && ls -la /tmp/csmsdb_snap.db; true")
        print(r.stdout)
        async with conn.start_sftp_client() as sftp:
            await sftp.get("/tmp/csmsdb_snap.db", DEST)
        print(f"pulled: {os.path.getsize(DEST):,} bytes")


asyncio.run(main())
