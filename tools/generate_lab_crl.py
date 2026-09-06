"""Generate a short-lived empty CRL for the local staging deployment only."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledge-lab-only", action="store_true", required=True)
    parser.add_argument("--ca-dir", type=Path, default=Path("tmp/edge-live-pki"))
    parser.add_argument("--output", type=Path, default=Path("runtime/mtls/ca.crl"))
    parser.add_argument("--revoke-cert", type=Path)
    args = parser.parse_args()
    ca = x509.load_pem_x509_certificate((args.ca_dir / "ca.crt").read_bytes())
    key = serialization.load_pem_private_key((args.ca_dir / "ca.key").read_bytes(), password=None)
    now = datetime.now(timezone.utc)
    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca.subject)
        .last_update(now - timedelta(minutes=1))
        .next_update(now + timedelta(hours=12))
    )
    if args.revoke_cert:
        revoked = x509.load_pem_x509_certificate(args.revoke_cert.read_bytes())
        builder = builder.add_revoked_certificate(
            x509.RevokedCertificateBuilder().serial_number(revoked.serial_number).revocation_date(now).build()
        )
    crl = builder.sign(key, hashes.SHA256())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(crl.public_bytes(serialization.Encoding.PEM))
    print(f"lab_crl=created path={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
