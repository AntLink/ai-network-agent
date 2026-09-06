from app.core.audit import redact_secrets


def test_audit_redacts_edge_credential_material():
    text = "username admin secret super-secret password=another-secret"
    redacted = redact_secrets(text)
    assert "super-secret" not in redacted
    assert "another-secret" not in redacted
    assert "***" in redacted
