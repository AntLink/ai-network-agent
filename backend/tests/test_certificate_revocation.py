from pathlib import Path

import pytest

from app.services.certificate_revocation import CertificateRevocationRegistry, certificate_fingerprint, normalize_fingerprint


def test_certificate_fingerprint_is_sha256_hex():
    fingerprint = certificate_fingerprint(b"certificate")
    assert fingerprint == normalize_fingerprint("SHA256:" + fingerprint)


def test_revocation_persists_and_is_fail_closed_for_invalid_present_value(tmp_path: Path):
    state = tmp_path / "revocations.json"
    fingerprint = "a" * 64
    registry = CertificateRevocationRegistry(str(state))
    registry.revoke(fingerprint=fingerprint, serial="serial-1", reason="compromise")
    assert CertificateRevocationRegistry(str(state)).is_revoked(fingerprint)
    assert CertificateRevocationRegistry(str(state)).record(fingerprint)["serial"] == "serial-1"
    with pytest.raises(ValueError):
        normalize_fingerprint("not-a-fingerprint")
    assert registry.is_revoked("not-a-fingerprint") is True
