# Work Session: central-attempt-reconciliation

## Session Metadata

- Session ID: `20260903-191453-phase-02-central-attempt-reconciliation`
- Date/Time Started: `2026-09-03T19:14:53+08:00`
- Date/Time Closed: `2026-09-03T19:55:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add Central-side classification for Edge-reported unresolved attempts, without creating retries or dispatching device actions.

## Scope

### In Scope
- Add a typed `/control/reconcile` endpoint and shared classification service.
- Add Go client method and Python/Go tests.
- Update traceability, runbook, and handoff.

### Out of Scope
- Device-side reconciliation, signed journal summaries, and automatic replay authorization remain out of scope.

## Initial Findings

 - Existing authenticated Edge session and TaskAttempt store are canonical.
 - Retry policy and replay gate already require explicit safety evidence; reconciliation must not bypass them.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Central Edge control API | `backend/app/api/v1/endpoints/edge_control.py` | `EXTEND` | Existing authenticated heartbeat API owns Edge control messages | Add read-only reconciliation endpoint |
| TaskAttempt state | `backend/app/services/task_attempt_leases.py` | `REUSE_AS_IS` | Existing store provides attempt status/result | Classifier reads only |
| Go control client | `edge/internal/control/client.go` | `EXTEND` | Existing mTLS control client owns Central calls | Add reconciliation request method |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1912_phase-02_edge-reconnect-reconciliation.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `EDGE-RECON-001`, `EDGE-RECON-002`, `TASK-LEASE-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| EDGE-RECON-002 | Central classification endpoint and Go client method with no replay authorization | `pytest backend/tests/test_edge_control.py -q`; `go test -race ./...` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect current HELLO/heartbeat and TaskAttempt store contracts.
2. Add read-only classifier and endpoint.
3. Add Go client method and tests.
4. Update durable evidence and handoff.

## Work Log

### 2026-09-03T19:50:00+08:00 — Central classifier implemented

**Action**
- Added read-only Central reconciliation service and authenticated `/v1/control/reconcile` endpoint.
- Added Go client `Reconcile` method and contract test.
- Classifications include terminal result, unresolved, unknown, and Edge-scope mismatch.

**Decision / rationale**
- Reconciliation only reports state; it never creates a child attempt or authorizes replay.
- Existing TaskAttempt store and authenticated control channel were extended.

### 2026-09-03T19:14:53+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1914_phase-02_central-attempt-reconciliation.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "central-attempt-reconciliation" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/attempt_reconciliation.py` | created | Central read-only classifier |
| `backend/app/api/v1/endpoints/edge_control.py` | extended | Reconciliation endpoint |
| `backend/tests/test_edge_control.py` | extended | Terminal/unknown classification test |
| `edge/internal/control/client.go` | extended | Reconciliation request method |
| `edge/internal/control/client_test.go` | extended | Client response test |
| `docs/traceability/requirements-matrix.md` | updated | `EDGE-RECON-002` |
| `docs/runbooks/deployment-runbook.md` | updated | Reconciliation operations |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Python control tests | `python -m pytest backend/tests/test_edge_control.py -q` | 5 passed |
| Python syntax | `python -m compileall -q backend/app backend/tests` | PASS |
| Go race tests | `go test -race ./...` from `edge/` | PASS: all packages |
| Integration | Live reconnect/device/GNS3 not run | NOT RUN: runtime evidence pending |
| Security/secret redaction | Result metadata only; Edge identity scope enforced | PASS |

## Errors and Blockers

- Classifier does not yet reconcile device-side state; unresolved attempts remain held for operator/policy review.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive `/control/reconcile` endpoint and response contract.
- Rollback/recovery impact: reconciliation is read-only and never triggers replay; unknown attempts remain fenced.

## Decisions / ADRs

- None; additive endpoint/service only.

## Remaining Work

- Add signed journal summaries and device-state reconciliation.
- Add live reconnect cycle and GNS3 vertical-slice evidence.

## Next Session Handoff

Start from:
- `backend/app/services/attempt_reconciliation.py`
- `backend/app/api/v1/endpoints/edge_control.py`
- `edge/internal/control/client.go`

Recommended next action:
1. Add typed unresolved journal summary and Central reconciliation evidence before any replay execution.

## Final Summary

Central now classifies unresolved Edge attempts without replay authorization. Python and Go tests pass; device-side reconciliation and live reconnect evidence remain pending, so this session is PARTIAL.
