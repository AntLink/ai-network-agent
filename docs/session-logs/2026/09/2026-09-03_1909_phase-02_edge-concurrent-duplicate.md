# Work Session: edge-concurrent-duplicate

## Session Metadata

- Session ID: `20260903-190937-phase-02-edge-concurrent-duplicate`
- Date/Time Started: `2026-09-03T19:09:37+08:00`
- Date/Time Closed: `2026-09-03T19:25:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Prove that the existing Edge attempt journal prevents concurrent duplicate delivery from executing the same handler twice.

## Scope

### In Scope
- Add a concurrent request test for identical attempt/idempotency keys.
- Run Go race verification and update requirement evidence.

### Out of Scope
- Central reconnect reconciliation and live device execution remain out of scope.

## Initial Findings

 - Existing HTTP control server journal is canonical.
 - No protocol or capability change is required; duplicate handling is internal runtime behavior.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge attempt journal | `edge/internal/control/server.go` | `REUSE_AS_IS` | Existing in-flight fence and terminal journal already implement the behavior | Add concurrency evidence only |
| Go control tests | `edge/internal/control/server_test.go` | `EXTEND` | Existing control test fixture owns handshake/session setup | Add concurrent duplicate scenario |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1856_phase-02_edge-durable-journal.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `EDGE-JOURNAL-001`, `EDGE-JOURNAL-003`, `M1-PROTO-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| EDGE-JOURNAL-003 | Concurrent duplicate rejected while original is in flight; handler runs once | `go test -race ./...` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect existing journal and control test fixture.
2. Add concurrent duplicate delivery test.
3. Run race tests and document fixture correction if needed.
4. Update durable evidence and handoff.

## Work Log

### 2026-09-03T19:20:00+08:00 — Concurrent duplicate evidence

**Action**
- Added a concurrent control-server test with identical attempt and idempotency key.
- Verified the second request receives `409` while the first is blocked, and the handler call count remains one.

**Result**
- Initial fixture missed `X-Edge-Session` and timed out before handler entry; the fixture was corrected and the race test passed.

### 2026-09-03T19:09:37+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1909_phase-02_edge-concurrent-duplicate.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "edge-concurrent-duplicate" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `edge/internal/control/server_test.go` | extended | Concurrent duplicate delivery test |
| `docs/traceability/requirements-matrix.md` | updated | `EDGE-JOURNAL-003` |
| `docs/runbooks/deployment-runbook.md` | updated | Concurrent duplicate behavior |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Go race tests | `go test -race ./...` from `edge/` | PASS: all packages |
| Formatting | `gofmt -w internal/control/server_test.go` | PASS |
| Integration | Live Central/Edge/GNS3 not run | NOT RUN: runtime evidence pending |
| Security/secret redaction | Test uses synthetic identifiers only | PASS |

## Errors and Blockers

- No product blocker. Live Central reconnect reconciliation remains pending.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: none; test exercises existing envelope and session contract.
- Rollback/recovery impact: duplicate in-flight execution is fenced; reconnect reconciliation is still required after restart.

## Decisions / ADRs

- None; no architecture boundary changed.

## Remaining Work

- Implement Central/Edge unresolved-attempt reconciliation on reconnect.
- Add live GNS3 vertical-slice evidence.

## Next Session Handoff

Start from:
- `edge/internal/control/server.go`
- `edge/internal/control/server_test.go`

Recommended next action:
1. Design reconnect journal summary and Central reconciliation response for unresolved attempts.

## Final Summary

Concurrent duplicate delivery is now race-tested and executes once. Reconnect reconciliation and live GNS3 evidence remain pending, so this session is PARTIAL.
