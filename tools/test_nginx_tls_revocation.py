"""Repeatable lab test for Nginx mTLS CRL rejection before HTTP forwarding."""
from __future__ import annotations

import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


ROOT = Path(__file__).resolve().parents[1]
IMAGE = "nginx:alpine"
CONTAINER = "ainet-nginx-tls-revocation-drill"
PORT = 18443
UPSTREAM_PORT = 18080


def write_client_material(directory: Path) -> None:
    ca_cert = x509.load_pem_x509_certificate((ROOT / "tmp/edge-live-pki/ca.crt").read_bytes())
    ca_key = serialization.load_pem_private_key((ROOT / "tmp/edge-live-pki/ca.key").read_bytes(), password=None)
    now = datetime.now(timezone.utc)
    revoked_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    valid_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    revoked_serial = x509.random_serial_number()

    def issue(key, name: str, serial: int) -> x509.Certificate:
        return (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)]))
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(serial)
            .not_valid_before(now - timedelta(minutes=1))
            .not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256())
        )

    revoked_cert = issue(revoked_key, "edge-nginx-revoked", revoked_serial)
    valid_cert = issue(valid_key, "edge-nginx-valid", x509.random_serial_number())
    for stem, key, cert in (("revoked", revoked_key, revoked_cert), ("valid", valid_key, valid_cert)):
        (directory / f"{stem}.key").write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
        (directory / f"{stem}.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (directory / "ca.crt").write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    crl = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(now)
        .next_update(now + timedelta(hours=1))
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
        .add_extension(x509.CRLNumber(1), critical=False)
        .add_revoked_certificate(
            x509.RevokedCertificateBuilder().serial_number(revoked_serial).revocation_date(now).build()
        )
        .sign(ca_key, hashes.SHA256())
    )
    (directory / "ca.crl").write_bytes(crl.public_bytes(serialization.Encoding.PEM))
    (directory / "central.crt").write_bytes((ROOT / "runtime/mtls/central.crt").read_bytes())
    (directory / "central.key").write_bytes((ROOT / "runtime/mtls/central.key").read_bytes())


def request(directory: Path, stem: str) -> tuple[str, str]:
    context = ssl.create_default_context(cafile=str(directory / "ca.crt"))
    context.check_hostname = False
    context.load_cert_chain(str(directory / f"{stem}.crt"), str(directory / f"{stem}.key"))
    with socket.create_connection(("127.0.0.1", PORT), timeout=5) as raw:
        with context.wrap_socket(raw, server_hostname="central") as tls:
            tls.sendall(b"GET /health HTTP/1.1\r\nHost: central\r\nConnection: close\r\n\r\n")
            return "HTTP", tls.recv(128).decode("latin1", errors="replace")


class SentinelHandler(BaseHTTPRequestHandler):
    hits: list[str] = []

    def do_GET(self):  # noqa: N802
        self.hits.append(self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"upstream-ok\n")

    def log_message(self, *_args):
        return


def main() -> int:
    directory = Path(tempfile.mkdtemp(prefix="ainet-nginx-tls-"))
    container = None
    upstream = None
    try:
        write_client_material(directory)
        SentinelHandler.hits = []
        upstream = HTTPServer(("0.0.0.0", UPSTREAM_PORT), SentinelHandler)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        nginx_conf = directory / "nginx.conf"
        nginx_conf.write_text(
            "error_log /dev/stderr debug; events {}\nhttp { server { listen 8443 ssl; ssl_certificate /etc/ainet/pki/central.crt; "
            "ssl_certificate_key /etc/ainet/pki/central.key; ssl_client_certificate /etc/ainet/pki/ca.crt; "
            "ssl_trusted_certificate /etc/ainet/pki/ca.crt; ssl_crl /etc/ainet/pki/ca.crl; "
            "ssl_verify_client on; ssl_verify_depth 2; location / { proxy_pass http://host.docker.internal:18080; } } }\n",
            encoding="utf-8",
        )
        container = subprocess.check_output(
            ["docker", "run", "-d", "--name", CONTAINER, "-p", f"{PORT}:8443", "-v", f"{directory}:/etc/ainet/pki:ro", "-v", f"{nginx_conf}:/etc/nginx/nginx.conf:ro", IMAGE],
            text=True,
        ).strip()
        time.sleep(2)
        valid_kind, valid_response = request(directory, "valid")
        _, revoked_response = request(directory, "revoked")
        print(f"nginx_valid_client={valid_kind}")
        print(f"nginx_valid_response={valid_response.splitlines()[0] if valid_response else 'EMPTY'}")
        print(f"nginx_revoked_response={revoked_response.splitlines()[0] if revoked_response else 'EMPTY'}")
        print(f"nginx_upstream_hits={len(SentinelHandler.hits)}")
        passed = valid_response.startswith("HTTP/1.1 200") and revoked_response.startswith("HTTP/1.1 400") and len(SentinelHandler.hits) == 1
        print("nginx_tls_revocation=PASS" if passed else "nginx_tls_revocation=FAIL")
        return 0 if passed else 1
    finally:
        if container:
            subprocess.run(["docker", "rm", "-f", CONTAINER], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if upstream:
            upstream.shutdown()
            upstream.server_close()
        shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
