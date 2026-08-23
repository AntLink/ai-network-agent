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
    ("/media/TCI/csms/bin/csmsAudio.elf", "csmsAudio.elf"),
    ("/media/httpd/cgi-bin/ProcessConfig.elf", "ProcessConfig.elf"),
]


async def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    async with asyncssh.connect(HOST, username=USER, password=PASS, known_hosts=None) as conn:
        r = await conn.run("ls -la /bin/csmsAudio.elf /media/httpd/cgi-bin/ProcessConfig.elf; true")
        print(r.stdout)
        async with conn.start_sftp_client() as sftp:
            for remote, local_name in FILES:
                local = os.path.join(DEST_DIR, local_name)
                print(f"pulling {remote} ...")
                await sftp.get(remote, local)
                print(f"  -> {os.path.getsize(local):,} bytes")


asyncio.run(main())
