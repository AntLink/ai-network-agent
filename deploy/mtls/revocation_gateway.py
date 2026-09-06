"""Small reference mTLS gateway with dynamic certificate revocation checks.

This deployment component terminates TLS, checks the verified peer certificate
before reading HTTP, and proxies only sanitized requests to FastAPI. Run it
behind a process supervisor/container; do not expose FastAPI directly.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID

from app.services.certificate_revocation import CertificateRevocationRegistry, certificate_fingerprint


MAX_REQUEST = 64 * 1024


def peer_identity(ssl_object: ssl.SSLObject) -> tuple[str, str]:
    der = ssl_object.getpeercert(binary_form=True)
    if not der:
        raise ValueError("verified client certificate is required")
    cert = x509.load_der_x509_certificate(der)
    common_names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    if not common_names or not common_names[0].value:
        raise ValueError("client certificate common name is required")
    return common_names[0].value, certificate_fingerprint(der)


def sanitize_request(raw: bytes, edge_id: str, fingerprint: str) -> bytes:
    header_end = raw.find(b"\r\n\r\n")
    if header_end < 0:
        raise ValueError("incomplete HTTP headers")
    lines = raw[:header_end].split(b"\r\n")
    if not lines or not lines[0].startswith((b"GET ", b"POST ", b"PUT ", b"PATCH ", b"DELETE ", b"HEAD ")):
        raise ValueError("unsupported HTTP request")
    kept = [lines[0]]
    for line in lines[1:]:
        if line.lower().startswith((b"x-client-edge-id:", b"x-client-cert-fingerprint:")):
            continue
        kept.append(line)
    kept.extend([
        f"X-Client-Edge-ID: {edge_id}".encode(),
        f"X-Client-Cert-Fingerprint: {fingerprint}".encode(),
    ])
    return b"\r\n".join(kept) + b"\r\n\r\n" + raw[header_end + 4:]


def force_connection_close(raw: bytes) -> bytes:
    """Tell HTTP clients that this gateway closes the socket per request."""
    header_end = raw.find(b"\r\n\r\n")
    if header_end < 0:
        return raw
    lines = raw[:header_end].split(b"\r\n")
    kept = [line for line in lines if not line.lower().startswith(b"connection:")]
    kept.append(b"Connection: close")
    return b"\r\n".join(kept) + b"\r\n\r\n" + raw[header_end + 4:]


async def health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, metrics: dict[str, int]) -> None:
    try:
        request = await asyncio.wait_for(reader.read(4096), timeout=2)
        path = request.split(b" ", 2)[1].decode() if request.startswith(b"GET ") else ""
        if path == "/ready":
            body, status = b'{"status":"ready"}\n', b"200 OK"
        elif path == "/metrics":
            body = b"\n".join(f"ainet_gateway_{key} {value}".encode() for key, value in metrics.items()) + b"\n"
            status = b"200 OK"
        else:
            body, status = b"not found\n", b"404 Not Found"
        writer.write(b"HTTP/1.1 " + status + b"\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
        await writer.drain()
    except (asyncio.TimeoutError, IndexError, UnicodeDecodeError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, registry: CertificateRevocationRegistry, upstream_host: str, upstream_port: int, metrics: dict[str, int]) -> None:
    try:
        ssl_object = writer.get_extra_info("ssl_object")
        if ssl_object is None:
            raise ValueError("TLS is required")
        edge_id, fingerprint = peer_identity(ssl_object)
        # Reload durable state so a revoke on another Central/API process is
        # enforced without restarting this terminator.
        if registry.is_revoked(fingerprint):
            metrics["denied_certificates_total"] += 1
            return
        raw = await reader.read(MAX_REQUEST)
        request = sanitize_request(raw, edge_id, fingerprint)
        upstream_reader, upstream_writer = await asyncio.open_connection(upstream_host, upstream_port)
        upstream_writer.write(request)
        await upstream_writer.drain()
        response = await upstream_reader.read(MAX_REQUEST)
        writer.write(force_connection_close(response))
        await writer.drain()
        upstream_writer.close()
        await upstream_writer.wait_closed()
        metrics["proxied_requests_total"] += 1
    except (OSError, ValueError, ssl.SSLError):
        metrics["errors_total"] += 1
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def run(args: argparse.Namespace) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(args.cert, args.key)
    context.load_verify_locations(cafile=args.ca)
    context.verify_mode = ssl.CERT_REQUIRED
    registry = CertificateRevocationRegistry(args.revocation_state)
    metrics = {"proxied_requests_total": 0, "denied_certificates_total": 0, "errors_total": 0}
    server = await asyncio.start_server(
        lambda r, w: handle(r, w, registry, args.upstream_host, args.upstream_port, metrics),
        args.listen_host, args.listen_port, ssl=context,
    )
    health = await asyncio.start_server(lambda r, w: health_handler(r, w, metrics), args.health_host, args.health_port)
    async with server, health:
        await asyncio.gather(server.serve_forever(), health.serve_forever())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--revocation-state", default="logs/edge-certificate-revocations.json")
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=9445)
    parser.add_argument("--upstream-host", default="127.0.0.1")
    parser.add_argument("--upstream-port", type=int, default=8000)
    parser.add_argument("--health-host", default="127.0.0.1")
    parser.add_argument("--health-port", type=int, default=9090)
    args = parser.parse_args()
    asyncio.run(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
