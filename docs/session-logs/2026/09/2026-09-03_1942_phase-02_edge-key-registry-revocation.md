# Work Session: edge-key-registry-revocation

## Session Metadata

- Session ID: `20260903-194211-phase-02-edge-key-registry-revocation`
- Date/Time Started: `2026-09-03T19:42:11+08:00`
- Date/Time Closed: `2026-09-03T22:35:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add a Central Edge journal public-key registry seam with revoked-Edge filtering so valid signatures from revoked identities are rejected.

## Scope

### In Scope
- Add registry abstraction and revoked-edge configuration.
- Enforce registry filtering in reconciliation signature validation.
- Add tests and durable evidence.

### Out of Scope
- Durable PKI issuer, key rotation workflow, immediate control-session disconnect, and production revocation evidence remain out of scope.

## Initial Findings

 - Existing journal verifier and reconciliation endpoint are canonical.
 - Revocation is applied before signature verification; no replay authorization is added.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Journal key registry | `backend/app/services/journal_signature.py` | `EXTEND` | Existing verifier owns public-key lookup boundary | Add active/revoked filtering |
| Reconciliation endpoint | `backend/app/api/v1/endpoints/edge_control.py` | `EXTEND` | Existing endpoint enforces signatures | Apply revoked registry before verification |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1940_phase-02_cross-runtime-signature-vector.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `EDGE-RECON-004`, `PKI-REVOCATION-003`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| PKI-REVOCATION-003 | Revoked Edge IDs excluded from summary verification | `pytest backend/tests/test_edge_control.py backend/tests/test_journal_signature.py -q` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect current verifier and reconciliation endpoint.
2. Add active/revoked registry filtering.
3. Test valid and revoked Edge behavior.
4. Document production PKI limitations.

## Work Log

### 2026-09-03T22:30:00+08:00 — Revocation filter implemented

**Action**
- Added `EdgeJournalKeyRegistry` with active-key filtering and revoked Edge exclusion.
- Added `EDGE_RECONCILIATION_REVOKED_EDGES_JSON` configuration and revoked-signature rejection test.

**Decision / rationale**
- Revocation is checked before signature verification.
- This is a configuration/service seam only; durable PKI revocation and immediate session disconnect remain required.

### 2026-09-03T19:42:11+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1942_phase-02_edge-key-registry-revocation.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "edge-key-registry-revocation" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/journal_signature.py` | extended | Active/revoked key registry |
| `backend/app/api/v1/endpoints/edge_control.py` | extended | Revoked-key enforcement |
| `backend/app/core/config.py` | extended | Revoked Edge configuration |
| `backend/tests/test_edge_control.py` | extended | Revoked valid-signature test |
| `docs/traceability/requirements-matrix.md` | updated | `PKI-REVOCATION-003` |
| `docs/runbooks/deployment-runbook.md` | updated | Revocation operation note |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Python control/signature tests | `python -m pytest backend/tests/test_edge_control.py backend/tests/test_journal_signature.py -q` | 9 passed |
| Python syntax | `python -m compileall -q backend/app backend/tests` | PASS |
| Integration | Live PKI/control disconnect/GNS3 not run | NOT RUN: evidence pending |
| Security/secret redaction | Public keys only; no private key or token logged | PASS |

## Errors and Blockers

- Registry is currently configuration-backed and does not itself provide durable PKI rotation or immediate session disconnect.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive configuration; no envelope change.
- Rollback/recovery impact: revoked identities cannot pass enforced summary verification; control-session revocation remains pending.

## Decisions / ADRs

- None; focused registry extension.

## Remaining Work

- Integrate registry with durable PKI lifecycle and force-disconnect.
- Add rotation/grace-key semantics and live signed reconnect evidence.

## Next Session Handoff

Start from:
- `backend/app/services/journal_signature.py`
- `backend/app/api/v1/endpoints/edge_control.py`

Recommended next action:
1. Replace configuration-backed revocation with the project PKI authority and immediate session invalidation.

## Final Summary

Central now rejects valid journal signatures from configured revoked Edges. Tests pass; durable PKI lifecycle and force disconnect remain pending, so this session is PARTIAL.
