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

DEST_DIR = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsd_elf"
FILES = [
    "/media/tci/csms/bin/csmsd.elf",
]


async def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        # size check first
        result = await conn.run("ls -la /media/tci/csms/bin/csmsd.elf; file /media/tci/csms/bin/csmsd.elf", check=False)
        print(result.stdout)

        async with conn.start_sftp_client() as sftp:
            for remote in FILES:
                local = os.path.join(DEST_DIR, os.path.basename(remote))
                print(f"pulling {remote} -> {local} ...")
                await sftp.get(remote, local)
                size = os.path.getsize(local)
                print(f"done: {size:,} bytes")


if __name__ == "__main__":
    asyncio.run(main())
