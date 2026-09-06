"""Cryptographic verifier for operator retry approvals."""
from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Mapping


class ApprovalVerificationError(ValueError):
    pass


class HMACApprovalVerifier:
    def __init__(self, secret: str, *, key_id: str = "default", verification_keys: Mapping[str, str] | None = None) -> None:
        self.key_id = key_id
        self.keys = {key: value.encode("utf-8") for key, value in (verification_keys or {}).items() if value}
        if secret:
            self.keys[key_id] = secret.encode("utf-8")

    @property
    def secret(self) -> bytes:
        return self.keys.get(self.key_id, b"")

    def issue_token(self, *, approval_ref: str, operator: str, attempt_id: str, fingerprint: str, expires_at: int) -> str:
        if not self.secret:
            raise ApprovalVerificationError("approval verifier secret is not configured")
        payload = f"{approval_ref}|{operator}|{attempt_id}|{fingerprint}|{expires_at}".encode("utf-8")
        encoded = self._encode(payload)
        signature = hmac.new(self.secret, encoded.encode("ascii"), hashlib.sha256).digest()
        return f"{self.key_id}.{encoded}.{self._encode(signature)}"

    def verify(self, token: str, *, approval_ref: str, operator: str, attempt_id: str, fingerprint: str, now: int | None = None) -> None:
        if not self.secret:
            raise ApprovalVerificationError("approval verifier secret is not configured")
        try:
            token_key_id, encoded, signature = token.split(".", 2)
            secret = self.keys.get(token_key_id, b"")
            if not secret:
                raise ApprovalVerificationError("approval token key is unknown or revoked")
            raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
            supplied_signature = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
            actual_signature = hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).digest()
            if not hmac.compare_digest(actual_signature, supplied_signature):
                raise ApprovalVerificationError("approval token signature is invalid")
            ref, token_operator, attempt, token_fingerprint, expiry = raw.decode("utf-8").split("|", 4)
            if (ref, token_operator, attempt, token_fingerprint) != (approval_ref, operator, attempt_id, fingerprint):
                raise ApprovalVerificationError("approval token binding is invalid")
            if int(expiry) < int(time.time() if now is None else now):
                raise ApprovalVerificationError("approval token is expired")
        except ApprovalVerificationError:
            raise
        except (ValueError, UnicodeDecodeError) as exc:
            raise ApprovalVerificationError("approval token is malformed") from exc

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
