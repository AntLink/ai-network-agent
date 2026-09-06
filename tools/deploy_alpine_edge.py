"""Deploy the existing Go Edge runtime to the GNS3 Alpine node over SSH.

Secrets are loaded from the local environment and sent only over the
authenticated SSH process stdin.  The script never prints secret values.
"""

from __future__ import annotations

import json
import os
import subprocess
import base64
import hashlib
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
ALPINE_HOST = os.environ.get("AINET_ALPINE_EDGE_HOST", "172.21.0.20")
SSH_KEY = ROOT / "tmp" / "alpine-deploy-key-user"
KNOWN_HOSTS = ROOT / "tmp" / "alpine-known-hosts"
BINARY = ROOT / "tmp" / "ainet-edge-linux"
PKI_DIR = ROOT / "tmp" / "edge-live-pki"
INITD = ROOT / "edge" / "installers" / "alpine" / "ainet-edge.initd"
CONFD = ROOT / "edge" / "installers" / "alpine" / "ainet-edge.confd"
R1_HOST_KEY_FINGERPRINT = "SHA256:x9VCRMp1sjoo0vmmjbAzTE7h/+OA1I7D5I/FnlkY7/M"


def ssh_args() -> list[str]:
    return [
        "ssh.exe",
        "-i",
        str(SSH_KEY),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={KNOWN_HOSTS}",
        f"root@{ALPINE_HOST}",
    ]


def run_ssh(command: str, *, stdin: bytes | None = None) -> None:
    result = subprocess.run(
        [*ssh_args(), command],
        input=stdin,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError(f"Alpine SSH step failed with exit code {result.returncode}")


def read_ssh(command: str) -> str:
    result = subprocess.run([*ssh_args(), command], capture_output=True, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError(f"Alpine SSH read failed with exit code {result.returncode}")
    return result.stdout.decode("utf-8", errors="strict").strip()


def copy_file(source: Path, destination: str) -> None:
    allowed_destinations = {
        "/usr/local/bin/ainet-edge",
        "/etc/ainet-edge/ca.crt",
        "/etc/ainet-edge/edge.crt",
        "/etc/ainet-edge/edge.key",
        "/etc/init.d/ainet-edge",
        "/etc/conf.d/ainet-edge",
    }
    if destination not in allowed_destinations:
        raise RuntimeError("Unexpected Alpine deployment destination")
    run_ssh(f"umask 077; cat > {destination}", stdin=source.read_bytes())


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)
    required = [
        SSH_KEY,
        KNOWN_HOSTS,
        BINARY,
        PKI_DIR / "ca.crt",
        PKI_DIR / "edge-001.crt",
        PKI_DIR / "edge-001.key",
        INITD,
        CONFD,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required deployment artifacts are missing")

    username = os.environ.get("CISCO_ROUTER_USERNAME", "admin")
    password = os.environ.get("CISCO_ROUTER_PASSWORD", "")
    if not password:
        raise RuntimeError("CISCO_ROUTER_PASSWORD is not configured")

    known_host = read_ssh(
        "if [ -s /root/.ssh/r1_known_hosts ]; then "
        "grep ' ssh-rsa ' /root/.ssh/r1_known_hosts | head -n 1; "
        "else ssh-keyscan -4 -T 10 192.168.10.1 2>/dev/null | "
        "grep ' ssh-rsa ' | head -n 1; fi"
    )
    fields = known_host.split()
    if len(fields) < 3 or fields[1] != "ssh-rsa":
        raise RuntimeError("Pinned R1 SSH host key is missing from Alpine")
    host_key = f"{fields[1]} {fields[2]}"
    fingerprint = "SHA256:" + base64.b64encode(
        hashlib.sha256(base64.b64decode(fields[2])).digest()
    ).decode("ascii").rstrip("=")
    if fingerprint != R1_HOST_KEY_FINGERPRINT:
        raise RuntimeError("Pinned R1 SSH host-key fingerprint does not match expected lab evidence")

    run_ssh(
        "install -d -m 0700 /etc/ainet-edge /var/lib/ainet-edge && "
        "install -d -m 0755 /etc/init.d /etc/conf.d && "
        "install -d -m 0755 /usr/local/bin"
    )
    copy_file(BINARY, "/usr/local/bin/ainet-edge")
    copy_file(PKI_DIR / "ca.crt", "/etc/ainet-edge/ca.crt")
    copy_file(PKI_DIR / "edge-001.crt", "/etc/ainet-edge/edge.crt")
    copy_file(PKI_DIR / "edge-001.key", "/etc/ainet-edge/edge.key")
    copy_file(INITD, "/etc/init.d/ainet-edge")
    copy_file(CONFD, "/etc/conf.d/ainet-edge")

    keystore = json.dumps(
        {
            "r1-lab": {
                "username": username,
                "password": password,
                "host_key": host_key,
            }
        },
        separators=(",", ":"),
    ).encode("utf-8")
    run_ssh("umask 077; cat > /etc/ainet-edge/keystore.json", stdin=keystore)
    network_config = (
        "auto lo\niface lo inet loopback\n\n"
        "auto eth0\niface eth0 inet static\n"
        "    address 192.168.10.20\n    netmask 255.255.255.0\n\n"
        "auto eth1\niface eth1 inet static\n"
        "    address 172.21.0.20\n    netmask 255.255.240.0\n"
    ).encode("ascii")
    run_ssh("umask 022; cat > /etc/network/interfaces", stdin=network_config)
    run_ssh(
        "chmod 0755 /usr/local/bin/ainet-edge /etc/init.d/ainet-edge && "
        "chmod 0600 /etc/ainet-edge/edge.key /etc/ainet-edge/keystore.json && "
        "chmod 0644 /etc/ainet-edge/ca.crt /etc/ainet-edge/edge.crt /etc/conf.d/ainet-edge && "
        "rc-update add ainet-edge default >/dev/null && "
        "rc-service ainet-edge restart"
    )
    print("alpine_edge_deploy=PASS")


if __name__ == "__main__":
    main()
