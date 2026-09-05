# Work Session: signed-retry-approval-verifier

## Session Metadata

- Session ID: `20260903-181413-phase-02-signed-retry-approval-verifier`
- Date/Time Started: `2026-09-03T18:14:13+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add cryptographic verification for operator-approved retry decisions, binding approval to the exact attempt and execution fingerprint.

## Scope

### In Scope
- Add HMAC approval token verifier with expiry and constant-time signature comparison.
- Require approval token in the retry API when `operator_approved=true`.
- Persist only token hash, never the raw token.

### Out of Scope
- External approval issuer, key rotation/KMS, and controlled replay execution remain future work.

## Initial Findings

- Approval reference was only syntactically required; no cryptographic verification existed.
- Retry API already had operator identity and fingerprint gates.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Retry API | `backend/app/api/v1/endpoints/tasks.py` | `EXTEND` | Existing approval reference gate | Verify signed token before policy evaluation. |
| Approval verifier | `backend/app/services/approval_verifier.py` | `CREATE` | No verifier existed | Self-hosted cryptographic verification seam. |
| Attempt schema | `backend/migrations/001_task_attempts.sql`, PostgreSQL adapter | `EXTEND` | Existing approval metadata | Persist token hash only. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1810_phase-02_durable-retry-approval-reference.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `RETRY-APPROVAL-001`, `AUTH-OPERATOR-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| RETRY-APPROVAL-001 | Approved retry requires a valid, bound, unexpired token; raw token is not persisted. | `pytest backend/tests/test_approval_verifier.py backend/tests/test_retry_api.py -q` | verifier/API tests | IMPLEMENTED_UNVERIFIED |

## Plan

1. Implement HMAC token issue/verify semantics.
2. Require and verify token on approved retry API requests.
3. Store token hash and add binding/expiry tests.

## Work Log

### 2026-09-03T18:14:13+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1814_phase-02_signed-retry-approval-verifier.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "signed-retry-approval-verifier" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-04T00:00:00+08:00 — Signed approval verifier implemented

**Action**
- Added `HMACApprovalVerifier` binding approval reference, operator, attempt ID, fingerprint, and expiry.
- Retry API now rejects approved requests without a valid token or configured secret.
- Added `operator_approval_token_hash` persistence field; raw token is never stored.
- Added tests for valid token, changed binding, expiry, and API behavior.

**Files**
- `backend/app/services/approval_verifier.py`
- `backend/app/api/v1/endpoints/tasks.py`
- `backend/app/core/config.py`
- `backend/app/services/postgres_task_attempt_leases.py`
- `backend/migrations/001_task_attempts.sql`
- `backend/tests/test_approval_verifier.py`

**Commands executed**
```text
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m pytest backend\\tests\\test_approval_verifier.py backend\\tests\\test_retry_api.py backend\\tests\\test_retry_policy.py backend\\tests\\test_task_attempt_leases.py backend\\tests\\test_edge_control.py backend\\tests\\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m py_compile backend\\app\\api\\v1\\endpoints\\tasks.py backend\\app\\services\\approval_verifier.py
```

**Result**
- Twenty-two focused Python tests passed.
- Python compilation passed.

**Security decision**
- `RETRY_APPROVAL_HMAC_SECRET` must be configured for approved retry; empty secret fails closed.
- This verifies a signed token but does not itself provide token issuance governance or key rotation.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/approval_verifier.py` | added | Signed approval verification |
| `backend/app/api/v1/endpoints/tasks.py` | extended | Verify approval token and store hash |
| `backend/app/core/config.py` | extended | Approval secret setting |
| `backend/migrations/001_task_attempts.sql` | extended | Token hash column |
| `backend/app/services/postgres_task_attempt_leases.py` | extended | Token hash update allowlist |
| `backend/tests/test_approval_verifier.py` | added | Cryptographic binding tests |
| `docs/session-logs/2026/09/2026-09-03_1814_phase-02_signed-retry-approval-verifier.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Focused verifier/retry/lease tests | PASS |
| Lint | Python compile | PASS |
| Integration | ASGI retry API and verifier tests | PASS; external issuer pending |
| Security/secret redaction | Token persistence/code inspection | PASS; raw token not persisted |

## Errors and Blockers

- Initial implementation omitted the token field from the Pydantic model; test failure found and fixed before final verification.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive retry request field and DB column.
- Rollback/recovery impact: approved retry now fails closed without configured secret/token.

## Decisions / ADRs

- Key management/rotation and approval issuer integration require an ADR before production.

## Remaining Work

- Integrate approval issuer/KMS and key rotation.
- Add durable approval record verification and controlled replay.

## Next Session Handoff

Start from:
- HMAC verifier is implemented; issuer governance and rotation are not.

Recommended next action:
1. Connect a trusted approval issuer and key lifecycle.
2. Add ALLOW-only replay execution with audit binding.

## Final Summary

Session is partially complete: signed approval verification is implemented/tested; issuer governance, rotation, and replay remain pending.
