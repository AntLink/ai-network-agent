# Work Session: edge-lifecycle-persistence

## Session Metadata

- Session ID: `20260903-195216-phase-04-edge-lifecycle-persistence`
- Date/Time Started: `2026-09-03T19:52:16+08:00`
- Date/Time Closed: `2026-09-04T00:25:00+08:00`
- Implementation Phase: `phase-04`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add local lifecycle state persistence across Central restart and enforce non-reactivation of revoked/deleted Edge identities.

## Scope

### In Scope
- Persist state to a protected JSON file with atomic replacement where supported.
- Restore state at registry initialization.
- Add persistence and terminal-state tests.

### Out of Scope
- Shared PostgreSQL/Redis HA state, transactional concurrency, and production filesystem hardening remain out of scope.

## Initial Findings

 - Existing in-memory lifecycle registry is canonical and extended in place.
 - The implementation explicitly documents the managed-Windows fallback and its production limitation.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge lifecycle registry | `backend/app/services/edge_identity.py` | `EXTEND` | Existing state machine owns lifecycle decisions | Add local durable persistence |
| Central configuration | `backend/app/core/config.py` | `EXTEND` | Existing settings owns runtime paths | Add lifecycle state path |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1949_phase-02_clear-quarantine-workflow.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `PKI-STATE-001`, `PKI-QUARANTINE-002`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| PKI-STATE-001 | Local lifecycle persistence and non-reactivation guard | `pytest backend/tests/test_edge_identity.py backend/tests/test_edge_control.py -q` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect lifecycle registry and configuration.
2. Add protected local persistence and startup restore.
3. Test restart and terminal state behavior.
4. Document HA limitation.

## Work Log

### 2026-09-04T00:20:00+08:00 — Lifecycle persistence implemented

**Action**
- Added local JSON state persistence and startup restore to `EdgeIdentityRegistry`.
- Added non-reactivation guard for both `REVOKED` and `DELETED` identities.
- Added tests for restore and revoked transition protection.

**Decision / rationale**
- This is a single-node durability step only. HA must use shared durable storage.
- Managed Windows replace failure has an explicit fallback and is documented as a production limitation.

### 2026-09-03T19:52:16+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1952_phase-04_edge-lifecycle-persistence.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-04" --title "edge-lifecycle-persistence" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/edge_identity.py` | extended | Local persistence and terminal-state guard |
| `backend/app/core/config.py` | extended | Lifecycle state file setting |
| `backend/tests/test_edge_identity.py` | created | Restore/non-reactivation tests |
| `docs/traceability/requirements-matrix.md` | updated | `PKI-STATE-001` |
| `docs/runbooks/deployment-runbook.md` | updated | State persistence operation |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Lifecycle/control tests | `python -m pytest backend/tests/test_edge_identity.py backend/tests/test_edge_control.py -q` | 13 passed |
| Python syntax | `python -m compileall -q backend/app backend/tests` | PASS |
| Integration | Live HA/PostgreSQL/Redis/PKI/GNS3 not run | NOT RUN: evidence pending |
| Security/secret redaction | State file contains IDs/states only; no secrets | PASS |

## Errors and Blockers

- Shared HA durability and production filesystem atomicity evidence remain pending.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive local setting; no control protocol change.
- Rollback/recovery impact: lifecycle state restores across single-node restart; revoked/deleted identities cannot be reactivated.

## Decisions / ADRs

- None; local persistence extends existing registry.

## Remaining Work

- Move state to transactional shared storage for HA.
- Add PKI-backed certificate invalidation and overlay deauthorization.

## Next Session Handoff

Start from:
- `backend/app/services/edge_identity.py`
- `backend/app/core/config.py`

Recommended next action:
1. Replace local state file with shared PostgreSQL/Redis lifecycle store and test multi-node consistency.

## Final Summary

Edge lifecycle state now persists locally and revoked identities remain terminal. Tests pass; HA/shared durability and PKI evidence remain pending, so this session is PARTIAL.
