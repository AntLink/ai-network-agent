from pathlib import Path

import pytest

from app.services.certificate_revocation import CertificateRevocationRegistry, certificate_fingerprint, certificate_fingerprint_from_header, normalize_fingerprint


def test_certificate_fingerprint_from_escaped_pem_header():
    from datetime import datetime, timedelta, timezone
    from urllib.parse import quote
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "edge-test")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "edge-test")]))
        .public_key(key.public_key()).serial_number(1)
        .not_valid_before(now).not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM).decode("ascii")
    assert certificate_fingerprint_from_header(quote(pem)) == certificate_fingerprint(cert.public_bytes(serialization.Encoding.DER))


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
