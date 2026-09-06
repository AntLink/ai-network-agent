"""Durable certificate serial/fingerprint revocation registry."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from threading import Lock
from urllib.parse import unquote

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding


def normalize_fingerprint(value: str) -> str:
    raw = value.strip().lower().removeprefix("sha256:").replace(":", "").replace(" ", "")
    if len(raw) != 64 or any(char not in "0123456789abcdef" for char in raw):
        raise ValueError("certificate fingerprint must be a SHA-256 hex digest")
    return raw


class CertificateRevocationRegistry:
    def __init__(self, state_file: str | None = None) -> None:
        self._lock = Lock()
        self._state_file = Path(state_file) if state_file else None
        self._records: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self._state_file is None or not self._state_file.exists():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._records = {key: value for key, value in raw.items() if isinstance(value, dict)}
        except (OSError, ValueError, TypeError):
            self._records = {}

    def _persist_locked(self) -> None:
        if self._state_file is None:
            return
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._state_file.with_suffix(self._state_file.suffix + ".tmp")
        temporary.write_text(json.dumps(self._records, sort_keys=True), encoding="utf-8")
        temporary.replace(self._state_file)

    def revoke(self, *, fingerprint: str, serial: str | None = None, reason: str = "") -> dict[str, str]:
        normalized = normalize_fingerprint(fingerprint)
        record = {
            "fingerprint": normalized,
            "serial": (serial or "").strip(),
            "reason": reason[:300],
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._records[normalized] = record
            self._persist_locked()
        return dict(record)

    def is_revoked(self, fingerprint: str | None) -> bool:
        if not fingerprint:
            return False
        try:
            normalized = normalize_fingerprint(fingerprint)
        except ValueError:
            return True
        with self._lock:
            self._load()
            return normalized in self._records

    def record(self, fingerprint: str | None) -> dict[str, str] | None:
        if not fingerprint:
            return None
        try:
            normalized = normalize_fingerprint(fingerprint)
        except ValueError:
            return None
        with self._lock:
            value = self._records.get(normalized)
            return dict(value) if value else None


def certificate_fingerprint(certificate_der: bytes) -> str:
    return hashlib.sha256(certificate_der).hexdigest()


def certificate_fingerprint_from_header(value: str) -> str:
    """Derive the SHA-256 revocation key from Nginx's escaped PEM header."""
    pem = unquote(value).replace("\\n", "\n")
    try:
        certificate = x509.load_pem_x509_certificate(pem.encode("ascii"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("client certificate header is invalid") from exc
    return certificate_fingerprint(certificate.public_bytes(Encoding.DER))
