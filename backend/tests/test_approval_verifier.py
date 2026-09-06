from app.services.approval_verifier import ApprovalVerificationError, HMACApprovalVerifier


def test_hmac_approval_token_binds_operator_attempt_and_fingerprint():
    verifier = HMACApprovalVerifier("test-secret")
    token = verifier.issue_token(approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, expires_at=2_000_000_000)
    verifier.verify(token, approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, now=1_900_000_000)


def test_hmac_approval_token_rejects_binding_change():
    verifier = HMACApprovalVerifier("test-secret")
    token = verifier.issue_token(approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, expires_at=2_000_000_000)
    try:
        verifier.verify(token, approval_ref="approval-1", operator="other", attempt_id="attempt-1", fingerprint="f" * 64, now=1_900_000_000)
    except ApprovalVerificationError:
        return
    raise AssertionError("changed operator must invalidate approval token")


def test_hmac_approval_token_rejects_expiry():
    verifier = HMACApprovalVerifier("test-secret")
    token = verifier.issue_token(approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, expires_at=100)
    try:
        verifier.verify(token, approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, now=101)
    except ApprovalVerificationError:
        return
    raise AssertionError("expired approval must be rejected")


def test_hmac_approval_verifier_accepts_grace_key_and_rejects_revoked_key():
    old = HMACApprovalVerifier("old-secret", key_id="old")
    token = old.issue_token(approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, expires_at=2_000_000_000)
    rotated = HMACApprovalVerifier("new-secret", key_id="new", verification_keys={"old": "old-secret"})
    rotated.verify(token, approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, now=1_900_000_000)
    revoked = HMACApprovalVerifier("new-secret", key_id="new")
    try:
        revoked.verify(token, approval_ref="approval-1", operator="operator-1", attempt_id="attempt-1", fingerprint="f" * 64, now=1_900_000_000)
    except ApprovalVerificationError:
        return
    raise AssertionError("revoked key must invalidate old token")
