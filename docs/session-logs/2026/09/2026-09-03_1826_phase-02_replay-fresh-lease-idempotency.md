# Work Session: replay-fresh-lease-idempotency

## Session Metadata

- Session ID: `20260903-182611-phase-02-replay-fresh-lease-idempotency`
- Date/Time Started: `2026-09-03T18:26:11+08:00`
- Date/Time Closed: `2026-09-03T18:34:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add the first controlled replay-acquisition seam after the prepare-only replay gate. The seam creates a fresh Central-owned lease, preserves the original execution fingerprint, enforces deterministic idempotency, and remains explicitly undispatched.

## Scope

### In Scope
- Extend the existing TaskAttempt lease store and PostgreSQL migration.
- Add API-level replay acquisition using the existing retry/replay gate.
- Add focused tests and update traceability/runbook evidence.

### Out of Scope
- Device execution, Edge dispatch, and production replay authorization remain out of scope.

## Initial Findings

- Existing FastAPI task API and shared TaskAttempt store are canonical.
- The replay-plan gate already validates ALLOW, capability, fingerprint, and signed approval token.
- In-memory storage is test/M1 only; PostgreSQL must retain replay metadata for later durable operation.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Existing TaskAttempt API/store | `backend/app/api/v1/endpoints/tasks.py`, `backend/app/services/task_attempt_leases.py` | `EXTEND` | Shared retry/replay path and Central lease authority already exist | Avoid a second jobs/replay subsystem |
| PostgreSQL TaskAttempt persistence | `backend/app/services/postgres_task_attempt_leases.py`, `backend/migrations/001_task_attempts.sql` | `EXTEND` | Durable adapter/schema already exists | Persist replay lineage and execution gate state |
| Retry/replay safety gate | `backend/app/services/replay_gate.py` | `REUSE_AS_IS` | Existing fail-closed prepare gate validates approval and fingerprint | Acquisition calls the gate without enabling execution |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1821_phase-02_controlled-replay-plan-gate.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `TASK-LEASE-001`, `RETRY-API-001`, `RETRY-TOKEN-001`, `SAFETY-CAPABILITY-003`, `TASK-REPLAY-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| TASK-REPLAY-001 | Fresh child TaskAttempt, deterministic replay idempotency, replay lineage, undispatched execution state | `pytest backend/tests/test_retry_api.py backend/tests/test_task_attempt_leases.py -q` | `docs/traceability/requirements-matrix.md`, test output below | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect the previous replay gate and persistence contract.
2. Add durable replay metadata and deterministic idempotency enforcement.
3. Add focused API/store tests.
4. Run focused and regression verification; document blockers.

## Work Log

### 2026-09-03T18:26:11+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1826_phase-02_replay-fresh-lease-idempotency.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "replay-fresh-lease-idempotency" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T18:27+08:00 — Assessment and implementation

**Action**
- Inspected the replay endpoint, in-memory lease store, PostgreSQL adapter, migration, runbook, traceability, and focused tests.
- Added fresh replay acquisition, replay lineage/status fields, durable PostgreSQL columns, and duplicate idempotency coverage.

**Decision / rationale**
- Extend the canonical TaskAttempt subsystem. A replay uses a fresh child attempt and lease; it does not mutate or reuse the uncertain parent.
- Keep acquisition separate from execution. The endpoint returns `execute=false` and `execution_status=NOT_DISPATCHED`.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/api/v1/endpoints/tasks.py` | extended | Controlled replay acquisition endpoint |
| `backend/app/services/task_attempt_leases.py` | extended/verified | In-memory idempotency uniqueness |
| `backend/app/services/postgres_task_attempt_leases.py` | extended | Durable replay lineage/status fields |
| `backend/migrations/001_task_attempts.sql` | extended | Replay metadata columns and forward-compatible ALTER |
| `backend/tests/test_task_attempt_leases.py` | extended | Duplicate idempotency test |
| `backend/tests/test_retry_api.py` | extended | Fresh replay lease and duplicate acquisition test |
| `docs/traceability/requirements-matrix.md` | updated | `TASK-REPLAY-001` traceability |
| `docs/runbooks/deployment-runbook.md` | updated | Replay acquisition operational semantics |
| `docs/session-logs/index.md` | updated | Session index entry |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Focused Python tests | `python -m pytest backend/tests/test_task_attempt_leases.py backend/tests/test_retry_api.py backend/tests/test_replay_gate.py backend/tests/test_approval_verifier.py -q` | 17 passed |
| Full Python backend tests | `python -m pytest backend/tests -q` | 41 passed, 1 RouterOS prompt failure |
| Go race tests | `go test -race ./...` from `edge/` | PASS: all Go packages |
| Secret redaction review | Source inspection; raw token is not persisted/logged | PASS for this slice |

## Errors and Blockers

- Full backend suite remains non-green at `backend/tests/test_console_transport.py::test_expect_detects_routeros_new_password_prompt_with_split_letters`: observed `prompt` instead of `newpass`; unrelated to replay changes and needs separate terminal investigation.
- Go race test first hit sandbox access denial for external build cache; approved rerun passed.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: PostgreSQL adds nullable replay lineage/status fields; existing records remain valid.
- Rollback/recovery impact: replay child remains fenced/undispatched until a future executor; duplicate acquisition is rejected.

## Decisions / ADRs

- None. No ADR required; this extends the existing replay gate and lease authority.

## Remaining Work

- Implement a real replay executor only after re-routing, capability advertisement, credential reference lookup, fresh lease validation, and policy checks.
- Add live PostgreSQL migration/restore evidence and GNS3 Edge execution evidence.

## Next Session Handoff

Start from:
- `backend/app/api/v1/endpoints/tasks.py` replay-acquire endpoint.
- `backend/app/services/postgres_task_attempt_leases.py` and `backend/migrations/001_task_attempts.sql`.

Recommended next action:
1. Build the later executor gate around the child attempt; do not dispatch from `replay-acquire`.

## Final Summary

Session completed as a partial M2 foundation. Production replay remains disabled.
