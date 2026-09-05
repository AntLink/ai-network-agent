"""Generate live mTLS material for the Milestone 1 server-mode Edge vertical slice.

Reuses the existing development CA (tmp/edge-live-pki/ca.key, ca.crt) so trust
chains remain consistent, and issues role-correct certificates:

  - edge-001.crt : SERVER_AUTH + CLIENT_AUTH (Edge listens as an mTLS server and
                   may also dial Central in client mode).
  - central.crt  : CLIENT_AUTH + SERVER_AUTH (Central presents a client cert to
                   the Edge server; also serves as mTLS server for edge-client
                   mode).

Development-only material; never use for production.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

SERVE = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH])
CLIENTX = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH])
BOTH = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH])

ROLES = {
    "edge-001": BOTH,
    "central": BOTH,
}


def _write_key(path: Path, key) -> None:
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


def _write_cert(path: Path, cert) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--ca-dir", type=Path, default=Path("tmp/edge-live-pki"))
    parser.add_argument("--central-ip", default="172.21.0.1")
    parser.add_argument("--edge-ip", default="172.21.0.2")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    ca_crt = x509.load_pem_x509_certificate((args.ca_dir / "ca.crt").read_bytes())
    ca_key = serialization.load_pem_private_key((args.ca_dir / "ca.key").read_bytes(), password=None)
    now = datetime.now(timezone.utc)

    for name, eku in ROLES.items():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_crt.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(eku, critical=False)
        )
        if name == "central":
            builder = builder.add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName("central"), x509.DNSName("localhost"), x509.IPAddress(ip_address(args.central_ip))]
                ),
                critical=False,
            )
        else:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName(name), x509.IPAddress(ip_address("127.0.0.1")), x509.IPAddress(ip_address(args.edge_ip))]
                ),
                critical=False,
            )
        builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        builder = builder.add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        cert = builder.sign(ca_key, hashes.SHA256())
        _write_key(out / f"{name}.key", key)
        _write_cert(out / f"{name}.crt", cert)
    # copy CA so trust chain is self-contained in the output dir
    _write_cert(out / "ca.crt", ca_crt)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
