"""Robust chunked deployment of the Go Edge runtime to the GNS3 Alpine VM.

The Cloud/Hyper-V bridge in this lab stalls on sustained large TCP transfers
(SCP/SFTP/SSH-stream copy of the multi-MB binary). Small individual SSH
commands complete reliably, so this helper transfers large files as small
base64 chunks over separate SSH connections, then reconstructs and verifies
the remote file by checksum.

Secrets (keystore) are sent only over the authenticated SSH process stdin.
The script never prints secret values.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
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

# Base64 chunk size chosen small enough that each SSH append completes
# reliably on the slow Cloud bridge.
CHUNK_BYTES = 196608  # 192 KiB of raw file per chunk (~256 KiB base64)


def ssh_base_args() -> list[str]:
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
        "-o",
        "ConnectTimeout=8",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "ServerAliveCountMax=3",
        f"root@{ALPINE_HOST}",
    ]


def exec_ssh(command: str, *, stdin: bytes | None = None, timeout: int = 45) -> str:
    result = subprocess.run(
        [*ssh_base_args(), command],
        input=stdin,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(
            f"Alpine SSH step failed (exit {result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')[:500]}"
        )
    return result.stdout.decode("utf-8", errors="replace")


def remote_md5(path: str) -> str:
    return exec_ssh(f"md5sum {path} 2>/dev/null | cut -d' ' -f1").strip()


def transfer_file(source: Path, destination: str, mode: str) -> None:
    data = source.read_bytes()
    expected = hashlib.md5(data).hexdigest()
    if remote_md5(destination) == expected:
        print(f"SKIP {destination} (checksum already matches)")
        exec_ssh(f"chmod {mode} {destination}")
        return
    n_chunks = (len(data) + CHUNK_BYTES - 1) // CHUNK_BYTES
    print(f"TRANSFER {destination} ({len(data)} bytes in {n_chunks} chunks)")
    for i in range(n_chunks):
        chunk = data[i * CHUNK_BYTES:(i + 1) * CHUNK_BYTES]
        redir = ">" if i == 0 else ">>"
        cmd = f"umask 077; dd of={destination} {redir} bs=131072 2>/dev/null"
        # Each chunk is written via a fresh SSH connection's stdin so no single
        # sustained stream saturates the Cloud bridge.
        exec_ssh(cmd, stdin=chunk, timeout=45)
        if i % 8 == 0 or i == n_chunks - 1:
            cur = remote_md5(destination)
            if cur and cur != expected:
                raise RuntimeError(f"checksum mismatch mid-transfer on {destination}: {cur}")
    got = remote_md5(destination)
    if got != expected:
        raise RuntimeError(
            f"checksum mismatch on {destination}: expected {expected}, got {got}"
        )
    exec_ssh(f"chmod {mode} {destination}")
    print(f"DONE {destination} md5={expected}")


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
        raise SystemExit(f"ERROR: missing deployment artifacts: {missing}")

    username = os.environ.get("CISCO_ROUTER_USERNAME", "admin")
    password = os.environ.get("CISCO_ROUTER_PASSWORD", "")
    if not password:
        raise SystemExit("ERROR: CISCO_ROUTER_PASSWORD is not configured")

    known_host = exec_ssh(
        "if [ -s /root/.ssh/r1_known_hosts ]; then "
        "grep ' ssh-rsa ' /root/.ssh/r1_known_hosts | head -n 1; "
        "else ssh-keyscan -4 -T 10 192.168.10.1 2>/dev/null | "
        "grep ' ssh-rsa ' | head -n 1; fi"
    )
    fields = known_host.split()
    if len(fields) < 3 or fields[1] != "ssh-rsa":
        raise SystemExit("ERROR: pinned R1 SSH host key is missing from Alpine")
    host_key = f"{fields[1]} {fields[2]}"
    try:
        fingerprint = "SHA256:" + base64.b64encode(
            hashlib.sha256(base64.b64decode(fields[2])).digest()
        ).decode("ascii").rstrip("=")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"ERROR: could not derive R1 fingerprint: {exc}") from exc
    if fingerprint != R1_HOST_KEY_FINGERPRINT:
        raise SystemExit(
            f"ERROR: R1 fingerprint mismatch: expected {R1_HOST_KEY_FINGERPRINT}, got {fingerprint}"
        )

    exec_ssh(
        "install -d -m 0700 /etc/ainet-edge /var/lib/ainet-edge && "
        "install -d -m 0755 /etc/init.d /etc/conf.d && "
        "install -d -m 0755 /usr/local/bin"
    )
    transfer_file(BINARY, "/usr/local/bin/ainet-edge", "0755")
    transfer_file(PKI_DIR / "ca.crt", "/etc/ainet-edge/ca.crt", "0644")
    transfer_file(PKI_DIR / "edge-001.crt", "/etc/ainet-edge/edge.crt", "0644")
    transfer_file(PKI_DIR / "edge-001.key", "/etc/ainet-edge/edge.key", "0600")
    transfer_file(INITD, "/etc/init.d/ainet-edge", "0755")
    transfer_file(CONFD, "/etc/conf.d/ainet-edge", "0644")

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
    exec_ssh("umask 077; cat > /etc/ainet-edge/keystore.json", stdin=keystore)
    network_config = (
        "auto lo\niface lo inet loopback\n\n"
        "auto eth0\niface eth0 inet static\n"
        "    address 192.168.10.20\n    netmask 255.255.255.0\n\n"
        "auto eth1\niface eth1 inet static\n"
        "    address 172.21.0.20\n    netmask 255.255.240.0\n"
    ).encode("ascii")
    exec_ssh("umask 022; cat > /etc/network/interfaces", stdin=network_config)
    exec_ssh(
        "chmod 0755 /usr/local/bin/ainet-edge /etc/init.d/ainet-edge && "
        "chmod 0600 /etc/ainet-edge/edge.key /etc/ainet-edge/keystore.json && "
        "chmod 0644 /etc/ainet-edge/ca.crt /etc/ainet-edge/edge.crt /etc/conf.d/ainet-edge && "
        "rc-update add ainet-edge default >/dev/null 2>&1; "
        "rc-service ainet-edge restart"
    )
    print("alpine_edge_deploy=PASS")


if __name__ == "__main__":
    main()
