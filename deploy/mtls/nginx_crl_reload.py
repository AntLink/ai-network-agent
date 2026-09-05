"""Fail-closed CRL validation and Nginx reload helper."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509


def validate_crl(path: Path) -> bytes:
    data = path.read_bytes()
    crl = x509.load_pem_x509_crl(data)
    now = datetime.now(timezone.utc)
    next_update = crl.next_update_utc if hasattr(crl, "next_update_utc") else crl.next_update.replace(tzinfo=timezone.utc)
    if next_update <= now:
        raise ValueError("CRL is expired")
    if crl.issuer.rfc4514_string() == "":
        raise ValueError("CRL issuer is missing")
    return data


def reload_if_changed(*, crl_path: Path, hash_path: Path, nginx_bin: str = "nginx") -> str:
    data = validate_crl(crl_path)
    digest = hashlib.sha256(data).hexdigest()
    previous = hash_path.read_text(encoding="ascii").strip() if hash_path.exists() else ""
    if digest == previous:
        return "UNCHANGED"
    subprocess.run([nginx_bin, "-t"], check=True, capture_output=True, text=True)
    subprocess.run([nginx_bin, "-s", "reload"], check=True, capture_output=True, text=True)
    hash_path.parent.mkdir(parents=True, exist_ok=True)
    hash_path.write_text(digest + "\n", encoding="ascii")
    return "RELOADED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crl", required=True, type=Path)
    parser.add_argument("--hash-state", required=True, type=Path)
    parser.add_argument("--nginx-bin", default="nginx")
    args = parser.parse_args()
    try:
        print(reload_if_changed(crl_path=args.crl, hash_path=args.hash_state, nginx_bin=args.nginx_bin))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"CRL_RELOAD=FAIL {type(exc).__name__}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
