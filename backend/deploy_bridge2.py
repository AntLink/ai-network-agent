import os
import sys
from pathlib import Path

import paramiko
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
    ("a", "killall csms-bridge-armv7 2>/dev/null"),
    ("b", f"cp {REMOTE_TMP} {REMOTE_DEST}"),
    ("c", f"chmod +x {REMOTE_DEST}"),
    ("d", f"nohup {REMOTE_DEST} >/tmp/csms-bridge.log 2>&1 &"),
    ("e", "sleep 3"),
    ("f", "wget -qO- http://localhost:8080/health"),
    ("g", "wget -qO- http://localhost:8080/spectrum/status"),
    ("h", "wget -qO- 'http://localhost:8080/spectrum/raw/live?format=text&limit=1'"),
    ("i", "netstat -tlnp | grep 8080"),
]


def upload() -> None:
    print(f"=== SCP {LOCAL_FILE} -> {HOST}:{REMOTE_TMP} ===")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        port=22,
        username=USERNAME,
        password=PASSWORD,
        look_for_keys=False,
        allow_agent=False,
        timeout=30,
    )
    try:
        sftp = client.open_sftp()
        sftp.put(str(LOCAL_FILE), REMOTE_TMP)
        sftp.close()
    finally:
        client.close()
    print("SCP done.")


async def main() -> None:
    upload()

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
    import asyncio

    asyncio.run(main())
