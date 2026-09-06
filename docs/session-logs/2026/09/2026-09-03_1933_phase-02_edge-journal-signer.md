# Work Session: edge-journal-signer

## Session Metadata

- Session ID: `20260903-193350-phase-02-edge-journal-signer`
- Date/Time Started: `2026-09-03T19:33:50+08:00`
- Date/Time Closed: `2026-09-03T21:15:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add Edge-side Ed25519 signing for canonical journal summaries using a protected PKCS#8 key file, preserving the existing reconciliation contract.

## Scope

### In Scope
- Add canonical Go signer and private-key loader.
- Wire `--journal-signing-key` into the outbound client.
- Run Go/Python verification and document PKI limitations.

### Out of Scope
- PKI enrollment, key rotation/revocation, actual journal-summary enumeration, and live end-to-end reconciliation remain out of scope.

## Initial Findings

 - Existing Go mTLS/security loader and control client are canonical.
 - Central Python verifier canonicalizes the same summary fields; signer uses matching JSON map canonicalization.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Go control signer | `edge/internal/control/signing.go` | `CREATE` | No existing Go signer covers journal summaries | Isolated contract signing boundary |
| Edge key loading | `edge/internal/security/mtls.go` | `EXTEND` | Existing security package owns PEM/X.509 loading | Add PKCS#8 Ed25519 loader |
| Outbound control runtime | `edge/cmd/ainet-edge/main.go`, `edge/internal/control/client.go` | `EXTEND` | Existing flags/client own outbound control | Add explicit signing-key wiring |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1926_phase-02_journal-summary-signature.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `EDGE-RECON-004`, `EDGE-RECON-005`, `PKI-REVOCATION-002`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| EDGE-RECON-005 | Edge key load and canonical summary signing | `go test -race ./...`; `pytest backend/tests/test_edge_control.py -q` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect existing control client/security loader.
2. Add signer and key loader.
3. Wire CLI flag and run cross-runtime tests.
4. Document PKI lifecycle limitation and handoff.

## Work Log

### 2026-09-03T21:10:00+08:00 — Edge signer implemented

**Action**
- Added Go Ed25519 signing over the canonical summary fields.
- Added PKCS#8 PEM private-key loader and `--journal-signing-key` wiring.
- Kept signing optional; Central enforcement remains explicit configuration.

**Decision / rationale**
- The mTLS key and journal-signing key are separate identities/materials.
- No private key, signature value, or secret was placed in logs.

### 2026-09-03T19:33:50+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1933_phase-02_edge-journal-signer.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "edge-journal-signer" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `edge/internal/control/signing.go` | created | Canonical Ed25519 summary signer |
| `edge/internal/control/client.go` | extended | Sign summaries when key configured |
| `edge/internal/security/mtls.go` | extended | PKCS#8 Ed25519 key loader |
| `edge/cmd/ainet-edge/main.go` | extended | `--journal-signing-key` flag |
| `edge/internal/control/client_test.go` | extended | Signer contract test |
| `docs/traceability/requirements-matrix.md` | updated | `EDGE-RECON-005` |
| `docs/runbooks/deployment-runbook.md` | updated | Signer operation notes |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Go race tests | `go test -race ./...` from `edge/` | PASS: all packages |
| Python control tests | `python -m pytest backend/tests/test_edge_control.py -q` | 7 passed |
| Python syntax | `python -m compileall -q backend/app backend/tests` | PASS |
| Integration | Live PKI/Central/Edge/GNS3 not run | NOT RUN: runtime evidence pending |
| Security/secret redaction | Private key is file-loaded only; no key material logged | PASS |

## Errors and Blockers

- Edge key lifecycle and end-to-end signer-to-Central verification remain pending.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive optional summary signature and CLI flag.
- Rollback/recovery impact: missing/invalid signatures are held/rejected when Central enforcement is enabled; no replay is triggered.

## Decisions / ADRs

- None; signer is an isolated contract extension.

## Remaining Work

- Connect signer to PKI enrollment/rotation/revocation and run end-to-end signed reconciliation.
- Enumerate actual journal summaries instead of caller-provided IDs.

## Next Session Handoff

Start from:
- `edge/internal/control/signing.go`
- `edge/internal/security/mtls.go`
- `edge/cmd/ainet-edge/main.go`

Recommended next action:
1. Add PKI-managed signing key lifecycle and signed journal enumeration in the Edge runtime.

## Final Summary

Edge can now sign canonical journal summaries with an explicit Ed25519 PKCS#8 key. Go and Python tests pass; PKI lifecycle and live end-to-end evidence remain pending, so this session is PARTIAL.
