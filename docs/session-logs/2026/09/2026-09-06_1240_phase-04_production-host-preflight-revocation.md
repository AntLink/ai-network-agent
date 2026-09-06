# Session: Production Host Preflight + Revocation Policy (M4)

- Timestamp (local): 2026-09-06 12:40 (+08, after host inspection)
- Phase: phase-04 (M4 Production Operations)
- Branch: `v5-release-prep`
- Related: inspection recorded in commit `8be8ccf`

## Context

Production host `192.168.210.51` was inspected over SSH and recorded in the
`five-block-production-hardening` session log. Findings: Docker active, no
existing AINET deployment, existing Nginx owns TCP 443, anonymous GHCR pulls
`unauthorized` (private images), ~3.3 GiB RAM with high swap, lab PKI not
production PKI. Six blocking gates were identified before safe deployment;
this session encodes those gates as a machine-checkable, read-only host
preflight and drafts the missing revocation policy.

## Work done

1. **`deploy/production/preflight.py`** (new) - host-side gate checker,
   standard-library only, runs on the target Ubuntu/Docker host. It only
   reads; it never writes, pulls, or modifies, and accepts no secrets. Gates:
   - `docker-active`
   - `no-existing-ainet` (refuses to clobber an existing deployment)
   - `registry-feed-auth` (immutable `<name>@<digest>` refs from the release
     manifest via `docker manifest inspect`; passes only once the host-level
     GHCR secret is provisioned)
   - `hostname-required` (approved production hostname)
   - `tls-cert-valid` (exists, parses, unexpired, SAN covers hostname)
   - `listener-plan` (fail on bound AINET default ports; preserves Nginx TCP
     443, reports its owner, never modifies it)
   - `capacity-memory` (RAM/swap advisories; fail < 2 GiB, warn < 4 GiB or
     heavy swap)
   - `revocation-policy` (approved policy file present)
   - `licensing-reference` (`LIC-YYYY-MM-DD-NNN-LABEL` pattern)
   - Verdict/exit: READY 0, READY-WITH-WARNINGS 2, NOT-READY 1 (fail-closed).

2. **`backend/tests/test_production_preflight.py`** (new) - 23 contract tests
   for the pure gate logic using scripted subprocess outcomes; PASS.

3. **`docs/production/revocation-policy.md`** (new, draft) - production PKI
   revocation policy at three layers (application registry, mTLS terminator
   CRL, Edge session control), revoke events, procedure, cadence/audit.
   Marked as a draft requiring explicit operator approval.

4. **`docs/runbooks/deployment-runbook.md`** section 19 - production host
   deployment plan: the six blockers as gates, preflight usage, capacity and
   isolation review, post-deployment hygiene (rotate host password/keys).

5. **Evidence** `docs/evidence/m4-production-operations/production-host-preflight-evidence-20260906.json`.

## Verification

- `pytest backend/tests/test_production_preflight.py` -> 23 passed.
- Full regression `pytest backend/tests/` -> **141 passed, 3 skipped**.
  - One test file (test_certificate_revocation.py) only failed because the
    user temp dir `%TEMP%\pytest-of-mohfa` is locked by an external process;
    re-running the whole suite with
    `--basetemp C:\Users\mohfa\AppData\Local\Temp\opencode\pytest-base`
    passes cleanly (environment workaround, not a code defect).
- Real-host CLI smoke test on this Windows box (no openssl/ss/meminfo):
  docker detected, GHCR manifest inspect proved UNAUTHORIZED for the pinned
  v0.1.0 digests, missing host tooling degrades to WARN not crash, exit 1 =
  NOT-READY. Correct fail-closed behavior confirmed.

## Honest status

- Production deployment remains **blocked** until the six external gates are
  approved/provisioned (PAT via host secret, hostname, TLS cert, listener/port
  plan, revocation policy approval, licensing reference).
- The preflight turns those blockers from prose into verifiable checks but
  cannot remove the need for operator approval.
- Revocation policy document is a draft; preflight `revocation-policy` gate
  stays FAIL until approved and deployed on the host.

## Next steps

1. (Operator) Provision GHCR read-only PAT on host via `docker login`, obtain
   approved hostname + TLS cert, approve listener/port plan and revocation
   policy, record licensing reference.
2. Re-run preflight on `192.168.210.51`; capture `VERDICT: READY` JSON as
   production-gate evidence.
3. Continue M4: live Edge binary install executor and DB/PKI backup-restore
   drill, then M5 HA live failover.
