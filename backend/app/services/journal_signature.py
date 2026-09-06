"""Fail-closed Ed25519 verification for Edge journal summaries."""
from __future__ import annotations

import base64
import json
from typing import Any, Mapping


class JournalSignatureError(ValueError):
    pass


class EdgeJournalKeyRegistry:
    """Small registry seam for active/revoked Edge verification keys."""

    def __init__(self, public_keys: Mapping[str, str], revoked_edges: set[str] | None = None) -> None:
        self._public_keys = dict(public_keys)
        self._revoked_edges = set(revoked_edges or set())

    def verification_keys(self) -> dict[str, str]:
        return {edge_id: key for edge_id, key in self._public_keys.items() if edge_id not in self._revoked_edges}

    def rotate(self, edge_id: str, public_key: str) -> None:
        if not edge_id or not public_key:
            raise ValueError("Edge ID and public key are required")
        self._public_keys[edge_id] = public_key
        self._revoked_edges.discard(edge_id)

    def revoke(self, edge_id: str) -> None:
        self._revoked_edges.add(edge_id)


def canonical_summary(summary: Mapping[str, Any]) -> bytes:
    payload = {
        "attempt_id": str(summary.get("attempt_id", "")),
        "idempotency_key": str(summary.get("idempotency_key", "")),
        "status": str(summary.get("status", "")),
        "result_available": bool(summary.get("result_available", False)),
    }
    if not payload["attempt_id"] or not payload["idempotency_key"] or not payload["status"]:
        raise JournalSignatureError("journal summary identity/status is required")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_summary_signature(*, edge_id: str, summary: Mapping[str, Any], public_keys: Mapping[str, str]) -> None:
    encoded_key = public_keys.get(edge_id)
    signature = summary.get("signature")
    if not encoded_key or not signature:
        raise JournalSignatureError("journal summary signature or Edge public key is missing")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(encoded_key + "=" * (-len(encoded_key) % 4)))
        key.verify(base64.urlsafe_b64decode(str(signature) + "=" * (-len(str(signature)) % 4)), canonical_summary(summary))
    except Exception as exc:
        raise JournalSignatureError("journal summary signature is invalid") from exc
