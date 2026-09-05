# Work Session: controlled-replay-plan-gate

## Session Metadata

- Session ID: `20260903-182111-phase-02-controlled-replay-plan-gate`
- Date/Time Started: `2026-09-03T18:21:11+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add a fail-closed controlled replay plan gate that prepares, but does not execute, a safe capability replay.

## Scope

### In Scope
- Require stored decision `ALLOW`, valid approval token, matching fingerprint, eligible status, and safe capability.
- Preserve credential references only; never expose credential values.
- Add explicit API/service tests proving `execute=false`.

### Out of Scope
- Actual device replay executor, approval issuer, and production authorization remain future work.

## Initial Findings

- Existing retry policy, token verifier, task store, and task router are canonical.
- Attempt records now retain device/capability/routing metadata needed for a future replay.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Retry policy/token verifier | Existing services | `REUSE` | Existing centralized gates | Compose existing safety checks. |
| Replay plan gate | `backend/app/services/replay_gate.py` | `CREATE` | No replay gate existed | Prepare-only seam; no device execution. |
| Tasks router | `backend/app/api/v1/endpoints/tasks.py` | `EXTEND` | Existing attempts API | Add replay-plan endpoint. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1818_phase-02_approval-key-rotation-foundation.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `RETRY-API-001`, `RETRY-TOKEN-001`, `SAFETY-CAPABILITY-003`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| SAFETY-CAPABILITY-003 | Replay plan is prepared only for ALLOW + valid token + matching fingerprint and never executes automatically. | `pytest backend/tests/test_replay_gate.py -q` | replay gate tests | IMPLEMENTED_UNVERIFIED |

## Plan

1. Add replay gate service.
2. Add task API endpoint with operator identity gate.
3. Test valid prepare and rejected non-ALLOW.

## Work Log

### 2026-09-03T18:21:11+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1821_phase-02_controlled-replay-plan-gate.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "controlled-replay-plan-gate" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-04T01:00:00+08:00 — Controlled replay plan gate implemented

**Action**
- Added `build_replay_plan()` composing ALLOW decision, token, fingerprint, status, and capability checks.
- Added `POST /api/v1/tasks/attempts/{attempt_id}/replay-plan` with operator identity/role checks.
- Replay plan returns `execute=false`; no device or Edge dispatch is performed.
- Added attempt device/capability/routing metadata and PostgreSQL schema fields.
- Added service tests for valid safe plan and non-ALLOW rejection.

**Files**
- `backend/app/services/replay_gate.py`
- `backend/app/api/v1/endpoints/tasks.py`
- `backend/app/services/postgres_task_attempt_leases.py`
- `backend/migrations/001_task_attempts.sql`
- `backend/tests/test_replay_gate.py`
- `docs/traceability/requirements-matrix.md`

**Commands executed**
```text
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m pytest backend\\tests\\test_replay_gate.py backend\\tests\\test_approval_verifier.py backend\\tests\\test_retry_api.py backend\\tests\\test_retry_policy.py backend\\tests\\test_task_attempt_leases.py backend\\tests\\test_edge_control.py backend\\tests\\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m py_compile backend\\app\\services\\replay_gate.py backend\\app\\api\\v1\\endpoints\\tasks.py backend\\app\\services\\postgres_task_attempt_leases.py
```

**Result**
- Twenty-five focused Python tests passed.
- Python compilation passed.

**Security decision**
- The gate exposes credential references only and explicitly cannot execute an operation.
- Real replay requires a later capability executor with fresh lease/idempotency checks.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/replay_gate.py` | added | Prepare-only replay safety gate |
| `backend/app/api/v1/endpoints/tasks.py` | extended | Replay plan endpoint and metadata |
| `backend/app/services/postgres_task_attempt_leases.py` | extended | Persist replay metadata |
| `backend/migrations/001_task_attempts.sql` | extended | Device/capability/routing columns |
| `backend/tests/test_replay_gate.py` | added | Replay gate evidence |
| `docs/session-logs/2026/09/2026-09-03_1821_phase-02_controlled-replay-plan-gate.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Focused replay/retry/lease tests | PASS |
| Lint | Python compile | PASS |
| Integration | Service and ASGI gate paths | PASS; actual replay pending |
| Security/secret redaction | Plan fields/code inspection | PASS; credential values excluded |

## Errors and Blockers

- No new errors. Actual replay executor intentionally not enabled.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive task route and attempt metadata.
- Rollback/recovery impact: prepare-only endpoint has no device side effect.

## Decisions / ADRs

- Actual replay executor and approval binding may require an ADR.

## Remaining Work

- Add fresh lease acquisition and idempotency enforcement for replay.
- Implement safe capability executor through Edge routing.

## Next Session Handoff

Start from:
- Replay gate is prepare-only; no execution evidence exists.

Recommended next action:
1. Add execution endpoint that consumes only a verified, unexpired replay plan.
2. Test duplicate/replay protection and task audit.

## Final Summary

Session is partially complete: controlled replay plan gate is implemented/tested; actual replay executor remains pending.
