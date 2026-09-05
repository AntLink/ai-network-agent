"""Build a temporary lab Edge-2 keystore from local env and a pinned R2 key."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    load_dotenv(Path(".env"), override=True)
    host_key = os.environ.get("R2_HOST_KEY", "").strip()
    username = os.environ.get("CISCO_ROUTER_USERNAME", "admin")
    password = os.environ.get("CISCO_ROUTER_PASSWORD", "")
    if not host_key or not password:
        raise SystemExit("R2 host key or router credential is not configured")
    if not host_key.startswith("ssh-rsa "):
        raise SystemExit("R2 host key is not an RSA public key")
    out = Path("tmp/edge-002-pki/keystore.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"b-r1": {"username": username, "password": password, "host_key": host_key}}, separators=(",", ":")), encoding="utf-8")
    os.chmod(out, 0o600)
    print("edge002_keystore=PASS")


if __name__ == "__main__":
    main()
