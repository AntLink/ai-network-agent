import asyncio
import os
import sys
from pathlib import Path

import asyncssh
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR))
from app.transports.ssh import SSHTransport  # noqa: E402

HOST = "192.168.162.20"
USERNAME = os.environ["LINUX_EMBEDDED_USERNAME"]
PASSWORD = os.environ["LINUX_EMBEDDED_PASSWORD"]

LOCAL_FILE = BASE_DIR / "csms_bridge" / "csms-bridge-armv7"
REMOTE_TMP = "/tmp/csms-bridge-armv7"
REMOTE_DEST = "/media/httpd/cgi-bin/csms-bridge-armv7"

COMMANDS = [
    ("a", f"chmod +x {REMOTE_TMP}"),
    ("b", f"cp {REMOTE_TMP} {REMOTE_DEST}"),
    ("c", f"chmod +x {REMOTE_DEST}"),
    ("d", f"ls -la {REMOTE_DEST}"),
    ("e", f"nohup {REMOTE_DEST} >/tmp/csms-bridge.log 2>&1 & sleep 3"),
    ("f", "wget -qO- http://localhost:8080/health"),
    ("g", "wget -qO- http://localhost:8080/gps"),
    ("h", "netstat -tlnp | grep 8080"),
    ("i", "ps aux | grep csms-bridge | grep -v grep"),
]


async def upload() -> None:
    print(f"=== SCP {LOCAL_FILE} -> {HOST}:{REMOTE_TMP} ===")
    async with asyncssh.connect(
        HOST,
        port=22,
        username=USERNAME,
        password=PASSWORD,
        known_hosts=None,
        connect_timeout=30,
    ) as conn:
        await asyncssh.scp(str(LOCAL_FILE), (conn, REMOTE_TMP))
    print("SCP done.")


async def main() -> None:
    await upload()

    transport = SSHTransport(HOST, USERNAME, PASSWORD)
    for label, command in COMMANDS:
        print(f"\n=== [{label}] $ {command} ===")
        try:
            out = await transport.run(command)
            if out:
                print(out, end="" if out.endswith("\n") else "\n")
            else:
                print("(no output)")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
