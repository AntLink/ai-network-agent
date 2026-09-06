# AINET Production PKI Revocation Policy

> Draft for operator approval. This document describes how revoked and
> compromised AINET identities are invalidated at three enforcement layers:
> the application session layer, the mTLS proxy terminator, and the Edge
> binary/session control plane. No secrets are stored here. The lab PKI used
> in Milestones 1-3 is **not** production PKI evidence (see `deployment-runbook.md`
> section 6) and does not satisfy this policy on its own.

## 1. Scope and ownership

- Production identities: Central (server), Edge hosts, and devices provisioned
  into the AINET inventory. Each carries a certificate bound to a CA chain
  owned by the production PKI operator.
- Authority: a named human "revocation authority" must be recorded in the
  deployment record before go-live. The authority approves hard revokes and
  their justification.
- The application enforcement registry is `EDGE_CERT_REVOCATION_STATE_FILE`
  on Central (durable, hashed per fingerprint). The mTLS terminator reloads a
  PEM `ssl_crl` (see `deploy/mtls/nginx_crl_reload.py`).
- Identity semantics: `REVOKED`/`DELETED` states are terminal; revoked or
  deleted identities are never re-activatable (invariant preserved).

## 2. Events that require revocation

1. Known or suspected private-key compromise of an Edge/Central cert.
2. Offboarding of an Edge host or device (permanent removal; use `DELETED`).
3. Unauthorized enrollment attempt detected (identity mismatch, role misuse).
4. Violation of an enrollment/operating agreement (abuse, scope creep).
5. Expiry of a time-limited certificate that must not renew.
6. Discovery of a mis-issued certificate (wrong SAN, wrong role, wrong owner).

## 3. Revocation procedure

1. Operator confirms the incident and records identity,
   reason, timestamp, and requester in the audit log (no secrets).
2. Application layer: post the fingerprint to the durable revocation registry
   and to `POST /api/v1/control/revoke` if HELLO/session control applies --
   Central rejects the fingerprint at HELLO and severs active sessions.
3. Terminator layer: publish a new PEM CRL containing the serial; run
   `python deploy/mtls/nginx_crl_reload.py --crl /etc/ainet/pki/ca.crl` which
   validates the CRL (parseable, unexpired), compares hash, runs `nginx -t`,
   and reloads only on change. Invalid/expired CRLs fail closed.
4. Verify: attempt a HELLO with the revoked identity; expect rejection, and
   confirm the gateway denied the proxied request before TLS-application.
5. Record evidence (revoked identity id, CRL serial, reload sha256, rejection
   probe) in `docs/evidence/pki-overlay/`.

## 4. Restoration / caution

- A revoked fingerprint may only be restored through a fresh enrollment with a
  new key pair and a new certificate; never by removing the revocation entry
  for the original key.
- Quarantine (soft, recovery-preserving) remains distinct from revoke (hard,
  terminal): use quarantine for suspected issues; escalate to revoke only on a
  confirmed decision.

## 5. Cadence, audit, and drift control

- Revocation-state and CRL must be reviewed at least once per release cycle and
  after every revoke event.
- The operator verifies that auto-renewals or re-enrollments cannot silently
  bypass the registry; no TOFU / shared known_hosts fallback.
- A quarterly drill: revoke a test identity at all three layers and prove
  rejection; record results in `docs/evidence/pki-overlay/`.

## 6. Approval state

This policy is a **draft** requiring explicit operator approval before it can
be referenced as a production gate artifact. Until approved, the production
EASM/preflight `revocation-policy` gate stays FAIL (fail-closed).