# Work Session: retry-decision-policy

## Session Metadata

- Session ID: `20260903-175524-phase-02-retry-decision-policy`
- Date/Time Started: `2026-09-03T17:55:24+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add a centralized execution-retry decision policy that distinguishes transport loss from device execution outcome.

## Scope

### In Scope
- Model ALLOW, REQUIRE_REVIEW, and REJECT outcomes.
- Require idempotency and verification for risky/uncertain replay.
- Cover safe, conditional, and non-retryable classes with tests.

### Out of Scope
- Policy is not yet wired to a retry endpoint/worker or audit workflow.

## Initial Findings

- Existing schemas already define `SAFE_RETRY`, `CONDITIONAL_RETRY`, and `NON_RETRYABLE`.
- No centralized retry policy service existed.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Retry taxonomy | `backend/app/schemas/edge.py` | `REUSE` | Existing RetryClass enum | Preserve contract vocabulary. |
| Retry decision policy | `backend/app/services/retry_policy.py` | `CREATE` | No central decision function existed | Single authoritative safety decision seam. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1752_phase-02_taskattempt-recovery-worker-lifespan.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `RETRY-001`, `TASK-LEASE-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| RETRY-001 | Transport loss with unknown execution requires review; risky retry requires verification/approval. | `pytest backend/tests/test_retry_policy.py -q` | `backend/tests/test_retry_policy.py` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Add policy evaluation result types.
2. Apply transport-loss and retry-class rules.
3. Add focused decision tests and document non-wiring limitation.

## Work Log

### 2026-09-03T17:55:24+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1755_phase-02_retry-decision-policy.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "retry-decision-policy" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T21:30:00+08:00 — Retry decision policy implemented

**Action**
- Added centralized `evaluate_retry()` policy using the existing retry taxonomy.
- Transport loss during dispatch/running now requires review unless non-execution is verified.
- Conditional retries require operator approval and `NOT_EXECUTED` verification.
- Non-retryable operations remain rejected unless explicitly approved by an operator workflow.
- Added focused tests for safe, conditional, non-retryable, and uncertain transport outcomes.

**Files**
- `backend/app/services/retry_policy.py`
- `backend/tests/test_retry_policy.py`
- `docs/traceability/requirements-matrix.md`

**Commands executed**
```text
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m pytest backend\\tests\\test_retry_policy.py backend\\tests\\test_task_attempt_leases.py backend\\tests\\test_edge_control.py backend\\tests\\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m py_compile backend\\app\\services\\retry_policy.py
```

**Result**
- Fifteen focused Python tests passed.
- Python compilation passed.

**Security / reliability decision**
- Policy never infers non-execution from a lost transport response.
- This policy is not yet connected to automatic retry execution, intentionally preventing an unreviewed replay path.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/retry_policy.py` | added | Central retry decision seam |
| `backend/tests/test_retry_policy.py` | added | Retry semantics evidence |
| `docs/session-logs/2026/09/2026-09-03_1755_phase-02_retry-decision-policy.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Focused retry/lease/control tests | PASS |
| Lint | Python compile | PASS |
| Integration | Policy unit tests | PASS; task retry workflow pending |
| Security/secret redaction | Policy input/output inspection | PASS; no payload/credential handling |

## Errors and Blockers

- No new errors. Retry execution wiring intentionally remains out of scope.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: no protocol changes.
- Rollback/recovery impact: additive service; no automatic behavior enabled.

## Decisions / ADRs

- No ADR required for policy function; explicit operator retry workflow may require one.

## Remaining Work

- Wire policy into TaskAttempt retry/review endpoint.
- Emit audit events for decisions.
- Add idempotency/fingerprint verification and batch partial-failure semantics.

## Next Session Handoff

Start from:
- Policy exists and is tested but is not yet called by task retry execution.

Recommended next action:
1. Add explicit retry decision API and audit evidence.
2. Connect only approved `ALLOW` decisions to safe task creation.

## Final Summary

Session is partially complete: retry policy and tests are implemented; execution workflow and audit wiring remain pending.
