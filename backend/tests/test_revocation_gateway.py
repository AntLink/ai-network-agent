from deploy.mtls.revocation_gateway import force_connection_close, sanitize_request


def test_gateway_replaces_client_supplied_identity_headers():
    raw = b"GET /health HTTP/1.1\r\nHost: central\r\nX-Client-Edge-ID: forged\r\nX-Client-Cert-Fingerprint: forged\r\n\r\n"
    result = sanitize_request(raw, "edge-real", "a" * 64)
    assert b"X-Client-Edge-ID: forged" not in result
    assert b"X-Client-Cert-Fingerprint: forged" not in result
    assert b"X-Client-Edge-ID: edge-real" in result
    assert b"X-Client-Cert-Fingerprint: " + (b"a" * 64) in result


def test_gateway_explicitly_signals_per_request_connection_close():
    raw = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: keep-alive\r\n\r\nok"
    result = force_connection_close(raw)
    assert b"Connection: keep-alive" not in result
    assert b"Connection: close" in result
