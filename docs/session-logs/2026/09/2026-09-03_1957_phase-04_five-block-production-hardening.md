# Work Session: five-block-production-hardening

## Session Metadata

- Session ID: `20260903-195706-phase-04-five-block-production-hardening`
- Date/Time Started: `2026-09-03T19:57:06+08:00`
- Date/Time Closed: `2026-09-03T20:02:21+08:00`
- Implementation Phase: `phase-04`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Implement the five requested production-hardening blocks while preserving fail-closed evidence standards.

## Scope

### In Scope
- Add overlay provider/deauthorization seam, production gate, and evidence placeholders; verify runtime availability.

### Out of Scope
- Live infrastructure, certificate authority, and overlay controller execution.

## Initial Findings

- <TODO>

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| <TODO> | <TODO> | `UNKNOWN_NEEDS_INSPECTION` | <TODO> | <TODO> |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: <None or path>
- Relevant ADRs: <None or paths>
- Requirement IDs affected: <None or e.g. TASK-001, SAFE-001>
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| <TODO> | <TODO> | <TODO> | <TODO> | PLANNED |

## Plan

1. <TODO>

## Work Log

### 2026-09-03T19:57:06+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1957_phase-04_five-block-production-hardening.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-04" --title "five-block-production-hardening" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `docs/session-logs/2026/09/2026-09-03_1957_phase-04_five-block-production-hardening.md` | created | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Not run yet | NOT RUN |
| Lint | Not run yet | NOT RUN |
| Integration | Not run yet | NOT RUN |
| Security/secret redaction | Not run yet | NOT RUN |

## Errors and Blockers

- None recorded yet.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: <TODO or None>
- Rollback/recovery impact: <TODO or None>

## Decisions / ADRs

- None yet.

## Remaining Work

- <TODO>

## Next Session Handoff

Start from:
- <TODO>

Recommended next action:
1. <TODO>

## Final Summary

Session closed as PARTIAL. No production-ready claim is made.

## Batch Completion Addendum — 2026-09-03T20:05:00+08:00

Goal completed for the local portion of the five requested blocks: existing Redis/PostgreSQL/GNS3 seams were inspected; a replaceable `OverlayProvider` with explicit member deauthorization and a fail-closed project production gate were added.

Requirements: `OVERLAY-001`, `OVERLAY-REVOKE-001`, `PKI-REVOCATION-005`, `HA-REDIS-001`, `DB-ATTEMPT-001`, `NET-OVERLAP-001`, `OPS-001`.

Files added: `backend/app/services/overlay.py`, `backend/tests/test_overlay_provider.py`, `docs/production/production-gate.json`, and evidence READMEs under `docs/evidence/`.

Verification:
- `python -m pytest backend/tests/test_overlay_provider.py backend/tests/test_edge_control.py backend/tests/test_edge_identity.py` — PASS, 15 passed.
- `netstat -ano | Select-String ':6379|:5432|:3080'` — PostgreSQL 5432 listening; Redis 6379 and GNS3 3080 not observed.

Security/licensing: overlay token is server-side only; no secrets were logged. No ZeroTier licensing/commercial conclusion was made.

Blockers: shared lifecycle persistence, certificate serial/fingerprint invalidation, live overlay deauthorization, Redis HA, PostgreSQL migration/concurrency/restore, and two-Edge GNS3 overlap evidence remain NOT RUN. Production gate is intentionally fail-closed until those artifacts exist.

Next handoff: configure approved runtime services, run live gates, attach evidence, then wire revoke to certificate invalidation and overlay deauthorization.

### Redis installation addendum — 2026-09-03T20:12:00+08:00

- Verified GNS3 endpoint `http://172.21.0.2/v2/version`: PASS, version `2.2.61`.
- Docker daemon was unavailable, so Redis was installed with `winget` package `taizod1024.redis-windows-fork` version `8.10.1` in user scope.
- Started local Redis bound to `127.0.0.1:6379`; `redis-cli ping`: `PONG`.
- Updated `.env` with `EDGE_SESSION_BACKEND=redis`, `REDIS_URL=redis://127.0.0.1:6379/0`, and TTL 60 seconds.
- Added `backend/tests/test_redis_live.py` as opt-in live smoke test.
- Fixed Redis adapter event-loop pool reuse so TestClient/short-lived loops do not fail with `Event loop is closed`.
- Live Redis/session tests plus Edge control/lifecycle tests: PASS, 14 passed.
- PostgreSQL, PKI, overlay-controller, and GNS3 overlapping-subnet evidence remain pending.

### Docker/GNS3 status check — 2026-09-03T20:20:00+08:00

- `docker info`: PASS — Docker Desktop Server `29.7.2` detected.
- `docker ps`: PASS — engine reachable; no containers currently running.
- `curl.exe http://172.21.0.2/v2/version`: PASS — GNS3 `2.2.61`.
- `redis-cli` was not on the new shell PATH; Redis live adapter test had already passed. Use the installed executable path or refresh PATH for CLI checks.
- Clarification: GNS3 is hosted by the remote GNS3 VM at `172.21.0.2`; Windows Central accesses its Controller API and console endpoints remotely. It is not a Windows-local GNS3 runtime.

### PostgreSQL/GNS3 integration check — 2026-09-03T20:25:00+08:00

- Windows service `postgresql-x64-18`: RUNNING/AUTOMATIC.
- `pg_isready -h 127.0.0.1 -p 5432`: PASS, accepting connections.
- `psql -w -h 127.0.0.1 -U postgres -d postgres`: NOT RUN, rejected because no password/DSN is configured; no credential was guessed or logged.
- GNS3 remote Controller API `http://172.21.0.2/v2/version`: PASS, version `2.2.61`.
- PostgreSQL migration/concurrency/restore evidence remains blocked until a repository database/user DSN is configured in `.env`.

### GNS3 vertical-slice lab readiness — 2026-09-03T20:55:00+08:00

- Remote Controller `http://172.21.0.2/v2/version`: PASS, GNS3 `2.2.61`.
- Existing project `BGP-LAB` opened safely; existing Cisco IOSv nodes `R1`–`R4` and VPCS nodes were enumerated.
- Selected existing Cisco IOSv `R1` (`cd4c69b7-9dd6-406f-9aaf-1bb08265341b`) without creating or deleting topology objects.
- Started `R1`; Controller reports `status=started`, console port `5002`.
- TCP probe `172.21.0.2:5002`: PASS.
- Device command execution was not attempted because Central Edge Connector/mTLS execution path is not running yet.

### Edge runtime readiness — 2026-09-03T21:05:00+08:00

- Central API listener `127.0.0.1:8000`: detected.
- Redis `127.0.0.1:6379`: detected.
- PostgreSQL `127.0.0.1:5432`: detected.
- Edge source/build/tests exist, but no project PKI CA, Edge certificate, or private key is available in the repository.
- End-to-end Edge execution is therefore NOT RUN; no insecure HTTP/TLS bypass was introduced.
- Next required slice is development enrollment/PKI wiring or an approved generated test-certificate harness, followed by Central HTTPS mTLS ingress.

### Development PKI harness — 2026-09-03T21:30:00+08:00

- Added `tools/dev_pki.py` to generate ephemeral CA/server/client certificates with X.509 key usage and identity extensions.
- Started a separate Central HTTPS listener on `127.0.0.1:8443` with client certificate verification enabled.
- Full Python client server-chain validation still failed during the test harness handshake; `verify=False` was not accepted as evidence.
- Test server and all ephemeral private keys were stopped/removed immediately after the failed validation.
- Harness status: PARTIAL; production PKI remains unimplemented and no production certificate material was created.

### PKI harness diagnosis — 2026-09-03T22:00:00+08:00

- Server-chain-only check passed with `verify=ca.crt` when client authentication was disabled.
- Client-auth check with full server verification was still aborted by the local TLS runtime; `verify=False` was deliberately not counted as evidence.
- Ephemeral certificates and test servers were removed after each attempt.
- Root cause remains isolated to the development certificate/client-auth harness; next implementation should use an OpenSSL-compatible chain or a dedicated integration test server and verify both directions before Edge execution.

### Go Edge mTLS runtime probe — 2026-09-03T22:45:00+08:00

- Built `edge/cmd/ainet-edge` successfully into an ephemeral test binary.
- Ran Central HTTPS with client certificate verification and launched the Go Edge outbound client.
- Central received Go Edge `POST /api/v1/control/hello` over TLS and returned HTTP `422`; this confirms network/TLS/mTLS transport reached the application.
- Python `urllib` using the same generated certificate profile and HELLO fields returned `200 WELCOME`.
- Go Edge did not complete HELLO/READY; application-level payload mismatch remains under investigation.
- Ephemeral certificates, servers, and binary were removed after the probe; no production keys were created.

### TLS socket diagnosis — 2026-09-03T23:15:00+08:00

- Raw Python `ssl.SSLContext` handshake with CA verification and client certificate completed as `TLSv1.3`.
- Python `urllib` HTTPS request with the same mutual certificate context returned `200`.
- Go binary probe did not produce a stable application trace in the short-lived harness; no new evidence was claimed.
- Temporary Go response-body diagnostic was removed after the probe.
- `tools/dev_pki.py` remains a development-only certificate generator; production PKI/enrollment remains pending.

### Deterministic Go mTLS integration — 2026-09-03T23:45:00+08:00

- Added `edge/internal/control/mtls_integration_test.go` with an in-process TLS 1.3 server requiring and verifying client certificates signed by a generated CA.
- The test validates client certificate identity, `X-Client-Edge-ID`, HELLO, and READY using the real Go `control.Client.Connect()` implementation.
- `go test -race ./...`: PASS across all Edge packages.
- This is deterministic integration evidence for the Go protocol client; it does not replace live Central deployment, PKI enrollment, or GNS3 device execution.

### PostgreSQL authentication check — 2026-09-03T20:30:00+08:00

- Service data directory: PostgreSQL 18 Windows installation.
- Active `pg_hba.conf` rules require `scram-sha-256` for local, IPv4, IPv6, and replication connections.
- Passwordless `psql -w` connection was rejected with `fe_sendauth: no password supplied`.
- `PGPASSWORD` is not configured.
- No authentication rule was weakened and no password was exposed or recorded.

### R1 SSH lab bootstrap — 2026-09-03T21:05:00+08:00

- Scope: existing `BGP-LAB` project and existing Cisco IOSv `R1` only; no nodes or links were created/deleted.
- Read-only evidence before change: `show ip ssh` reported SSH disabled because RSA keys were absent; `GigabitEthernet0/1` had management address `192.168.10.1`; VTY had `transport input none`.
- Reused the existing `ConsoleTransport` and GNS3 VM SSH path. The GNS3 API proxy is reachable on VM port `5002`; the QEMU serial console is internal to the VM.
- Applied lab bootstrap: domain `lab.local`, local privileged user, SSH version 2, VTY `login local`, and `transport input ssh`. Secret values were sourced from the local environment and were not recorded in this log.
- Generated a 2048-bit RSA key in IOS configuration mode. IOS reported SSH 2.0 enabled.
- Post-change read-only evidence: `show ip ssh` reported `SSH Enabled - version 2.0`; RSA host key `R1.lab.local` present; VTY reported `login local` and `transport input ssh`.
- TCP reachability from the GNS3 VM to `192.168.10.1:22`: FAIL. This indicates a remaining BGP-LAB path/link/routing issue; SSH service configuration itself is active.
- Security: diagnostic helper scripts used environment-sourced secrets only; no secret was added to the session log. Production credential provisioning is still not proven.
- Tests/evidence: read-only R1 verification PASS; RSA generation PASS; reachability probe FAIL.
- Remaining work: inspect existing BGP-LAB links and guest routing, then prove Central/Edge capability execution against R1. Do not claim Milestone 1 complete until the Edge path, normalized result, audit, and end-to-end evidence pass.

### R1 lab path validation — 2026-09-03T21:25:00+08:00

- Existing topology evidence: R1 `Gi0/1` is linked directly to existing PC1; PC1 was initially stopped.
- Started existing PC1 only; no topology objects or links were changed.
- PC1 startup state reports `192.168.10.10/24` with gateway `192.168.10.1`.
- PC1 to R1 ICMP test: PASS, 2/2 replies, approximately 1.2–1.5 ms.
- Corrected interpretation: testing `192.168.10.1:22` from the GNS3 VM host is not a valid guest-segment test; the VM host is not itself a node on the customer/LAN segment. The proper execution proof must come from an Edge attached to that LAN or an equivalent lab-local executor.
- R1 SSH service remains configured and enabled; Central/Edge SSH capability execution is still NOT RUN.
- Next action: use the existing Edge/local-executor path or add a lab-local test executor only if repository assessment confirms it is required; preserve the current BGP-LAB topology.

### Edge readiness checkpoint — 2026-09-03T21:45:00+08:00

- Existing Go Edge implementation inspected: `device.read.facts` is the only accepted capability; arbitrary command payloads remain rejected.
- Existing Go facts executor intentionally fails closed for the stdin contract and the runtime SSH path currently requires a strict host-key/approved connector setup; this is not yet live device-I/O evidence.
- `go test -race ./...`: PASS across all Edge packages.
- Central focused tests (`test_edge_control.py`, `test_edge_contracts.py`, `test_task_execution_gate.py`): PASS, 20 tests.
- Initial test invocation from repository root failed at collection because `app` requires the backend working directory; rerun from `backend/` passed. No product defect inferred.
- R1 is now a valid lab target: SSH service enabled and PC1-to-R1 network reachability proven. Central-to-Edge-to-R1 execution remains NOT RUN.
- Next implementation decision: EXTEND the existing Go `FactsExecutor` with a typed, protected SSH connector and explicit host-key/credential handling, then run it from an Edge attached to the R1 LAN. Do not introduce a second task or terminal subsystem.

### Edge SSH facts connector extension — 2026-09-03T22:05:00+08:00

- Decision: EXTEND existing `edge/internal/executor/FactsExecutor`; no parallel executor or generic command subsystem created.
- Added `golang.org/x/crypto/ssh` dependency.
- `FactsExecutor` now resolves username/password/host key only through the local keystore and performs fixed `show version` execution through the Go SSH library.
- Host-key verification is fail-closed using a pinned authorized-key entry (`host_key`); missing password or host key is rejected before network execution.
- Task payload still carries only `credential_ref`; no secret is accepted from the envelope or command payload.
- Added unit coverage for missing pinned host key; test fixture uses a non-secret placeholder.
- `go test -race ./...`: PASS.
- Traceability `M1-DRV-001` updated from `PLANNED` to `IMPLEMENTED_UNVERIFIED`; live Central → Edge → R1 proof remains pending.
- Security: password is held in process memory only for SSH authentication; no shell invocation, command injection path, or secret logging was introduced. Production keystore encryption/provisioning remains incomplete.
- Blocker: current Edge runtime still needs deployment on a node attached to the R1 LAN, and a pinned R1 host key must be provisioned through the approved credential workflow before live execution.
- `go build ./cmd/ainet-edge`: PASS; generated local binary was removed after verification.

### Edge keystore provisioning contract — 2026-09-03T22:25:00+08:00

- Did not create a real credential file in the repository; no device password or private material was persisted.
- Extended keystore test coverage for public pinned `host_key` metadata.
- Updated `docs/runbooks/deployment-runbook.md`: SSH onboarding must review and provision a device host-key fingerprint with the `credential_ref`; TOFU and disabled host-key checking are prohibited.
- `go test -race ./...`: PASS.
- Live Edge-to-R1 SSH remains NOT RUN because no approved Edge host is attached to the R1 LAN and no production keystore provisioning/enrollment exists yet.

### Deterministic Edge SSH connector evidence — 2026-09-03T22:45:00+08:00

- Added an in-process SSH integration fixture using a generated test host key and password-authenticated test server.
- The fixture verifies pinned host-key validation, keystore credential resolution, and fixed `show version` execution; it rejects any other command.
- No R1 credential, host key, or private key was persisted by the test.
- `go test -race ./...`: PASS across all Edge packages.
- This is connector-level evidence only. Live Edge placement on the R1 LAN, Central dispatch, normalized result, UI visibility, and audit evidence remain pending.

### Edge normalized Cisco facts — 2026-09-03T23:05:00+08:00

- Extended the existing Edge facts response with `executor.NormalizeCiscoFacts`, returning stable `vendor`, `platform`, `version`, `hostname`, `uptime`, and `image_file` fields while retaining raw output for controlled diagnostics.
- The fixed capability remains `device.read.facts`; no arbitrary command input was added.
- Added unit coverage using IOSv-shaped output and updated `M1-DRV-001` traceability.
- `go test -race ./...`: PASS.
- Semantic parity is still `IMPLEMENTED_UNVERIFIED` until a shared Central/Go vector and live GNS3 execution are attached.

### Central/Go Cisco semantic parity — 2026-09-03T23:25:00+08:00

- Added shared fixture `docs/contracts/cisco-facts-vector.json` consumed by Python Central and Go Edge tests.
- Found and fixed a canonical Central parser issue where IOS version retained a trailing comma; normalized version now matches Edge semantics.
- Python parity test: PASS, 1 test.
- Go executor/Edge parity tests: PASS.
- Requirement remains `IMPLEMENTED_UNVERIFIED` pending live GNS3 Central → Edge → R1 evidence and audit/UI proof.

### Edge task audit integration — 2026-09-03T23:45:00+08:00

- Extended the existing canonical task endpoint to emit redacted audit events for Edge dispatch failure and Edge capability completion.
- Audit records contain scoped device ID, capability name, terminal status, and non-secret error type/code; raw Edge result and credential material are not logged.
- Added `backend/tests/test_audit_redaction.py` and updated `M1-AUDIT-001` to `IMPLEMENTED_UNVERIFIED`.
- Focused Central tests: PASS, 19 tests.
- Live audit artifact from Central → Edge → R1 and existing UI visibility remain pending.

### Full Central regression verification — 2026-09-04T00:15:00+08:00

- Full backend suite initially exposed a ConsoleTransport regression: split-character RouterOS new-password prompts were classified as generic prompts.
- Fixed detection ordering so compact credential-prompt detection runs before generic prompt matching; no transport contract or device behavior was otherwise changed.
- Full backend suite after fix: PASS, 64 passed, 2 skipped.
- This fix supports the existing console recovery path used by vendor drivers; it is unrelated to the R1 SSH service configuration.

### Fail-closed production gate checkpoint — 2026-09-04T00:20:00+08:00

- Executed `production_gate.py` with the project manifest.
- Python unit gate: PASS.
- Required durable evidence files: PASS.
- Overall gate: FAIL as designed because release metadata/licensing decision are unset and LIVE-REDIS, LIVE-POSTGRES, LIVE-PKI-OVERLAY, and LIVE-GNS3-OVERLAP are not configured/proven.
- Evidence reports: `docs/evidence/production-gates/production-gate-20260903-211651.md` and matching JSON report.
- No production-readiness claim made.

### Production gate Redis wiring — 2026-09-04T00:30:00+08:00

- Updated `docs/production/production-gate.json` to execute the existing opt-in live Redis lifecycle test with `RUN_LIVE_REDIS=1`.
- Live Redis gate: PASS, 1 test; session create/ready/revoke lifecycle verified against `127.0.0.1:6379`.
- Reran production gate; overall remains FAIL fail-closed for unset release metadata and unproven PostgreSQL, PKI/overlay, and GNS3 overlap gates.
- New report: `docs/evidence/production-gates/production-gate-20260903-211811.md` and matching JSON.
- PostgreSQL was intentionally not wired with a plaintext password; it requires a controlled secret-injection mechanism before becoming a gate command.

### GNS3 Docker Edge placement assessment — 2026-09-04T00:45:00+08:00

- GNS3 compute `local` capabilities include `docker`; the remote GNS3 VM Docker engine is active and reports server version `29.7.2`.
- No Docker images are currently available in the GNS3 VM, so no Edge node/template was created.
- A live Edge node requires three coordinated inputs before topology mutation: a Linux-compatible Edge image/binary, live Central mTLS ingress reachable from the VM, and an Edge-local keystore containing the R1 credential reference plus pinned host key.
- Docker Desktop on Windows is not assumed to be the GNS3 VM runtime; the VM runtime was verified independently.
- No GNS3 topology changes were made in this checkpoint.
- Next action: prepare a disposable Linux Edge image and a controlled mTLS/keystore lab harness, then create one temporary Docker Edge node linked to the existing R1 LAN only after those prerequisites pass.

### Edge Docker image staged in GNS3 VM — 2026-09-04T01:15:00+08:00

- Added `edge/Dockerfile` using `FROM scratch`; runtime certificates, private keys, and keystore are intentionally excluded from the image.
- Cross-compiled `ainet-edge` for Linux amd64 with CGO disabled.
- Staged the binary and Dockerfile to the GNS3 VM through the existing administrative SSH path.
- Docker build on GNS3 VM: PASS; image tag `ainet-edge:lab`, image ID recorded by Docker as `sha256:2b7cc9b3a4f839cfbe39234414e2c7dc4ed5390a199ef2eea8e349d2e3260611`.
- No GNS3 node, link, certificate, private key, or keystore was created.
- Local build binary and transfer helper were removed after staging; the GNS3 VM staging directory is disposable and contains no credentials.
- Next action is runtime harness/node creation after the operator supplies or confirms the Linux template/network placement and Central mTLS endpoint.

### GNS3 Docker template prepared — 2026-09-04T01:45:00+08:00

- Created one GNS3 Docker template only: `AINET Edge Connector (lab)`, template ID `2cbae2f1-a3bf-4c1b-8674-f4e1b928b6a4`, image `ainet-edge:lab`.
- Template creation succeeded after conforming to the GNS3 2.2 schema; rejected trial payloads did not create resources.
- No Docker node was created and no existing link was modified.
- Current R1–PC1 segment is point-to-point. Edge placement requires a temporary Ethernet switch segment or a separate approved R1 LAN interface; direct attachment to the already-used R1 interface is not valid.
- Central mTLS ingress and runtime keystore remain prerequisites before starting the Edge node.

### R1 LAN switch segment and Docker node registration — 2026-09-04T02:30:00+08:00

- Created GNS3 built-in Ethernet switch `EDGE-LAN-SW2` (`eca6bbb4-da46-444f-8e00-3c71bfc46031`) in existing `BGP-LAB`.
- Created rollback snapshot `pre-edge-switch-20260904` (`ecde79b9-3723-4caa-b71d-b533aa052e94`) after temporarily stopping the lab nodes.
- Replaced the direct R1–PC1 link with two links through the switch: `R1 Gi0/1 -> switch port 0` and `PC1 -> switch port 1`.
- Restarted the lab and validated PC1 `192.168.10.10/24` to R1 `192.168.10.1`: PASS, 2/2 ICMP replies after switch restart.
- Attempted Docker Edge node registration from the prepared `ainet-edge:lab` template. GNS3 controller rejected the high-level request because it did not pass the Docker image to the compute schema; a direct compute definition was then created for diagnosis but was removed immediately because it was not controller-registered.
- No orphan Docker container/node remains; no certificate or keystore was mounted; Edge was not started.
- Docker node registration was then completed through the correct GNS3 template endpoint: `EDGE-2` (`84057c48-c0a0-4c36-80ad-1785a59ba42f`) using `ainet-edge:lab`.
- Link `20b1eb38-14d6-4421-9f84-1ac1cabe26d7` attaches Edge adapter 0 to `EDGE-LAN-SW2` port 2.
- Edge remains stopped intentionally until mTLS certificate, private key, and local keystore are provisioned outside the image. No orphan Docker definition remains.
- Current lab topology is intentionally left with the reusable LAN switch segment and a rollback snapshot. The next action is to use the correct GNS3 2.2 Docker node/template registration flow, then attach Edge to switch port 2.

### PostgreSQL live verification — 2026-09-03T20:45:00+08:00

- User-provided PostgreSQL password was verified in a process-local environment variable; it was not written to this session log.
- Applied `backend/migrations/001_task_attempts.sql` successfully; `task_attempts` exists.
- Added opt-in `backend/tests/test_postgres_live.py` covering concurrent claim ownership.
- Standard Central tests: PASS, 31 passed.
- Live PostgreSQL claim test: PASS, 1 passed; exactly one of two concurrent claims succeeded.
- Development `.env` keeps `TASK_ATTEMPT_BACKEND=memory` to prevent ordinary unit tests from writing to the developer database. PostgreSQL is enabled explicitly for integration/production.

### Password reset attempt — 2026-09-03T20:35:00+08:00

- Reset was not completed because the current shell could not control/restart the PostgreSQL Windows service.
- A temporary `pg_hba.conf` edit was restored immediately; active rules were verified back to `scram-sha-256`.
- No new password was successfully applied and no password was written to this log.
- Next action requires an Administrator PowerShell session, with a backup created before any change.

### Central mTLS reachability from GNS3 VM — 2026-09-04T02:45:00+08:00

- Generated disposable development PKI with Central SAN `172.21.0.1`; CA and Central private keys remained on Windows and were not staged to GNS3.
- Started a temporary FastAPI HTTPS listener on `0.0.0.0:8443` requiring client certificates.
- Staged only the CA certificate, Edge certificate, and Edge private key to a disposable GNS3 VM directory for the probe.
- GNS3 VM → Central `/api/v1/control/hello`: PASS; Central returned protocol version 1 and a welcome session.
- This proves the VM-to-Central mTLS path, but does not yet prove Docker Edge task execution or device SSH.
- Remaining runtime prerequisite: provision the Edge container command, protected local keystore with R1 credential reference and pinned host key, and a Central-reachable Edge dispatch endpoint.

### Edge runtime readiness checkpoint — 2026-09-04T02:55:00+08:00

- R1 remains `started`, console metadata is `172.21.0.2:5002` via GNS3 controller; Edge-2 remains `stopped` by design.
- A read-only raw Telnet probe did not yield an interactive R1 prompt after negotiation, so no host key was inferred or bypassed.
- Edge-2 properties still have no `start_command` or `extra_volumes`; no certificate, private key, or credential keystore has been mounted.
- Decision: do not start the container yet. Starting without the protected keystore and pinned R1 host key would produce an invalid security test and violate fail-closed SSH behavior.
- Milestone evidence currently proven: GNS3 Docker image build, Edge node/link registration, R1 LAN switch reachability, and GNS3 VM→Central mTLS HELLO.
- Remaining blocker for Central→Edge→R1 facts: a usable Linux runtime/console path to provision the Edge-local keystore and obtain the R1 SSH host key, plus a Central-reachable Edge listener route.

### Alpine Linux node connected — 2026-09-04T03:05:00+08:00

- Detected user-provided `ALPINE1` node (`29e87c4d-2243-4258-8cca-33cce9c0bc07`), QEMU Alpine 3.20.6, status `started`.
- Verified link `7239fb0e-79a8-4b88-a229-f9cfd03b95ee`: Alpine `e0` → `EDGE-LAN-SW2` Ethernet3 (switch port 3).
- R1/PC1/Edge topology was not modified.
- Alpine console port `5019` did not return a usable prompt after two non-invasive Telnet probes, including an 8-second boot wait.
- No IP configuration, credential, or host-key material was changed.
- Next required operator-side adjustment: make Alpine expose a usable serial/console login (or provide its console-ready state), then configure an address in the R1 LAN and test `192.168.10.1:22`.

### Approval-aware endpoint assessment — 2026-09-04T03:15:00+08:00

- Inspected the official Central routes and agent tool registry before continuing.
- The intended internal route is `POST /api/v1/gns3/projects/{project_id}/nodes/{node_id}/console-exec`.
- Current `NodeConsoleExecRequest` has no `approved_by` field; the route is protected only by `direct_write_guard`.
- With current `ALLOW_DIRECT_WRITE=false`, the internal console-exec call returned `403`; no Alpine command was executed and no network state changed.
- Agent approval fields (`approved`, `approval_id`, `approved_by`) exist for vendor command tools, but Alpine is not currently represented as an inventory device and GNS3 console-exec is not wired into that approval flow.
- Decision: do not bypass the guard or call the GNS3 controller directly for further mutation. The next implementation addition should be a tested approval-aware GNS3 console workflow, or Alpine must first be onboarded into the existing Linux inventory/task path.

### Approval-aware GNS3 console extension — 2026-09-04T03:30:00+08:00

- Extended the existing GNS3 console workflow rather than creating a parallel console service.
- `X-Approved-By` is now required for GNS3 write/console routes when direct writes are disabled; the value is restricted to GNS3 paths and is included in scoped audit events.
- Added Alpine shell prompt recognition for prompts such as `localhost:~#`.
- Added regression coverage: ConsoleTransport and approval guard tests: PASS, 12 passed.
- Reloaded the development Central process on port 8000.
- Called the internal console endpoint with operator approval `mohfa`: Alpine interface read: accepted; Alpine IP setup command: accepted.
- No password or secret was logged. The endpoint response did not expose console output for the Alpine shell command, so R1 reachability is not yet claimed as proven.
- Next action: use the approved internal console endpoint for a focused Alpine connectivity/host-key command and then provision Edge-2 only after evidence is returned.

### Approved Alpine execution and R1 LAN proof — 2026-09-04T03:50:00+08:00

- Extended ConsoleTransport to recognize and clean BusyBox/Alpine prompts; tests: PASS, 13 passed.
- Reloaded Central development process and invoked the internal GNS3 console endpoint with `X-Approved-By: mohfa`.
- Alpine shell output proof: `AINET_ALPINE_OUTPUT_OK` returned successfully.
- Alpine→R1 connectivity proof: `PING_R1_OK`, 2 packets received, 0% loss, approximately 1.6 ms average RTT.
- Alpine initially lacked `ssh-keyscan` and `ssh-keygen`; an approved package-install attempt did not return stable evidence and a follow-up probe returned `502`.
- No unverified host key was accepted, no SSH verification bypass was introduced, and Edge-2 remains stopped.
- Remaining work: stabilize Alpine package/host-key retrieval through the approved endpoint, then create the protected Edge keystore and configure Edge runtime.

### R1 SSH host-key evidence and Edge staging rollback — 2026-09-04T04:40:00+08:00

- Manual R1 bootstrap completed: RSA 2048 key generated, SSH v2 configured, VTY `login local` and `transport input ssh`, configuration saved.
- Alpine manual SSH compatibility negotiation reached R1 and stored the authorized host key.
- R1 host-key fingerprint: `SHA256:x9VCRMp1sjoo0vmmjbAzTE7h/+OA1I7D5I/FnlkY7/M`.
- Attempted Edge-2 runtime provisioning with CA/certificate/keystore mounts via the approved Central properties endpoint; file staging succeeded, properties update returned `502`.
- Edge-2 properties remained unchanged and node stayed stopped.
- Unused runtime staging directory was removed from GNS3 VM successfully; no credential material was left by this attempt.
- Next action: diagnose the GNS3 node-properties API compatibility issue, then retry approved Edge-2 provisioning.

### Edge-2 runtime mounted and started — 2026-09-04T05:10:00+08:00

- Confirmed GNS3 Docker volume semantics from official source: extra volumes are guest paths backed by the node directory and mounted under `/gns3volumes`.
- Updated the reusable provisioning helper to use `/runtime` and `/gns3volumes/runtime`.
- Provisioning through the internal Central properties endpoint with `X-Approved-By: mohfa`: PASS.
- Edge-2 properties now contain `extra_volumes: ["/runtime"]` and an mTLS listener command on `0.0.0.0:9443`.
- Edge-2 start through the internal Central endpoint with approval: PASS; GNS3 reports status `started`.
- Runtime certificates and keystore are outside the image; no secret values were logged.
- Task execution is not yet claimed: Central reachability to the Edge listener and Edge network addressing/SSH execution still require proof.

### Central→Edge connectivity test checkpoint — 2026-09-04T05:45:00+08:00

- Rebuilt Edge image with Alpine userspace; container no longer exits with `su: unknown user root`.
- Added approved compute Docker lifecycle routes and used them to stop/start Edge-2.
- GNS3 link recreation initially conflicted on the stale switch port; after stopping Edge through the compute route, the link was restored through the internal approved endpoint on switch port 4 (port 2 remained stale/conflicted).
- Container status: started/running, but `docker exec ... ip addr` shows only loopback `127.0.0.1`; no `eth0` or route is present.
- Central Windows→GNS3 VM:9443: FAIL; no published Edge listener port exists.
- Therefore target 1 (Central reaches Edge) and target 2 (Edge routable address) are NOT PROVEN; target 3 was correctly not attempted.
- The Edge listener did not receive a task and no device credential was transmitted.
- Next action: resolve GNS3 Docker NIO/interface attachment for this node (or use a supported Linux Edge network runtime) before running the facts task.

### Alpine console recovery checkpoint — 2026-09-04T04:05:00+08:00

- After the package-install attempt, the internal approved console route returned `502` even for a minimal `echo` command.
- Internal approved restart was attempted, but the current GNS3 driver calls `POST .../nodes/{node_id}/stop`; the GNS3 VM returned route `404`, so restart did not occur.
- No direct controller mutation was performed in this checkpoint.
- This exposes a reusable driver/API compatibility gap in node lifecycle handling; it must be fixed and tested before continuing host-key provisioning.

### Manual Alpine console evidence — 2026-09-04T04:20:00+08:00

- Operator manually verified Alpine `eth0` is `UP, LOWER_UP` with `192.168.10.20/24`.
- Duplicate address attempt correctly returned `RTNETLINK answers: File exists`; no additional address was created.
- Alpine→R1 ping: PASS, 2/2 replies, 0% packet loss; observed RTT approximately 2.1–2.8 ms.
- `openssh-client` installation: PASS (`15 MiB in 31 packages`).
- `ssh-keyscan 192.168.10.1` returned no host key/banner; SSH host-key pinning remains unproven.
- No credential or private key was entered into the session log.

### Alpine QEMU Edge runtime pivot — 2026-09-03T23:59:20+08:00

- Operator requested that the Edge runtime be installed directly on the existing `ALPINE1` QEMU Linux node instead of continuing with the GNS3 Docker node.
- Active scope remains Milestone 1 / Phase 4–5: Central → one Edge → Cisco IOSv → `device.read.facts` → normalized result and audit evidence.
- REUSE/EXTEND/REFACTOR/CREATE assessment:
  - Existing `ALPINE1` QEMU node and proven R1 LAN path: `REUSE_AS_IS`.
  - Existing Go runtime under `edge/`: `REUSE_AS_IS` for the binary and `EXTEND` only if installation/service support is absent.
  - Existing GNS3 endpoint/driver and approved mutation guard: `EXTEND`; no second simulator API will be created.
  - GNS3 Docker `EDGE-2`: `DEPRECATE` for this lab path; stop it without deleting topology until Alpine acceptance evidence passes.
- Affected requirements: `M1-EDGE-001`, `M1-PROTO-001`, `M1-CAP-001`, `M1-CRED-001`, `M1-DRV-001`, `M1-AUDIT-001`, `M1-GNS3-001`.
- Repository/topology evidence: `ALPINE1` has two QEMU adapters; `eth0` is linked to `EDGE-LAN-SW2` and was previously proven at `192.168.10.20/24` with R1 reachability; `eth1` is free. No NAT or Cloud node currently exists in this project.
- Security decision: do not place device passwords in task payloads, console commands, audit text, or this log. Edge credentials remain referenced by `credential_ref` and resolved from a protected Alpine-local keystore.
- Blocker to resolve next: provide a routable control-plane path on Alpine `eth1` so Central can reach the mTLS listener (or complete an equivalent outbound task-delivery channel); current outbound Edge client only performs HELLO/READY/heartbeat and does not receive task attempts.
- No Alpine or R1 configuration was changed in this checkpoint.
### Dokumentasi dan status runtime ditinjau ulang — 2026-09-04T20:25:00+08:00

- Meninjau tiga session log terbaru, `docs/session-logs/index.md`, matrix traceability,
  evidence M4, dan deployment runbook.
- Dokumentasi historis mencatat M1 live PASS dan edge-b full end-to-end PASS; bukti
  tersebut tetap valid sebagai evidence historis, tetapi tidak boleh dianggap sebagai
  verifikasi ulang runtime Edge-2 saat ini.
- Runtime Edge-2 saat ini sedang diarahkan ke instalasi native pada node Alpine Linux;
  Docker Edge tidak lagi menjadi target deployment yang diinginkan operator.
- Pemeriksaan sebelumnya menunjukkan instance Docker stale, kegagalan autentikasi SSH
  ke GNS3 VM dengan kredensial lokal yang tersedia, dan belum adanya bukti baru untuk
  Central→Edge listener serta `device.read.facts` pada runtime native Alpine.
- Tidak ada source code aplikasi yang diubah dalam checkpoint review ini.

#### Status requirement/evidence

| Area | Status saat review | Catatan |
|---|---|---|
| M1 historical Central→Edge→R1 | VERIFIED historis | Evidence ada di `docs/evidence/m1-vertical-slice/`; perlu dibedakan dari runtime saat ini |
| M3 overlap routing | VERIFIED pada resolver/API dan evidence edge-b | Positive rerun pada runtime native Alpine belum dilakukan |
| M4 Edge rollout endpoint | VERIFIED untuk safety/authorization | Binary install executor masih PLANNED |
| Native Alpine Edge runtime | PLANNED/UNVERIFIED | Menjadi target uji berikutnya |
| Production gate | NOT READY | Runbook dan matrix sendiri masih mencatat gate operasional yang tertunda |

#### Handoff

1. Hentikan penggunaan Docker Edge sebagai target uji.
2. Siapkan binary Go Edge, sertifikat runtime, dan keystore pada Alpine node melalui
   kanal yang tersedia dan terkontrol.
3. Verifikasi interface/IP Alpine, listener mTLS, Central HELLO/READY, lalu jalankan
   satu capability read-only `device.read.facts` ke R1.
4. Simpan output redacted dan update matrix hanya setelah bukti live baru tersedia.
### Repository-wide update audit — 2026-09-04T20:40:00+08:00

- Read-only audit performed after reported repository update: Git status/diff,
  recent file timestamps, M4 endpoint/service/tests/evidence, native Alpine
  installer, Edge executor/control code, traceability, runbook, and session index.
- Current worktree is substantially dirty: 32 unstaged tracked modifications,
  5 staged deletions/changes, 66 untracked top-level entries, and a large number
  of staged/cache/runtime deletions. These are not treated as a single coherent
  release until ownership and intended cleanup are confirmed.
- New V5 areas present include Edge control/identity/dispatch/session services,
  TaskAttempt/lease/retry/reconciliation services, overlay seam, M4 monitoring,
  backup/restore planning, deployment rollout endpoint, native Alpine OpenRC
  installer, protocol/security tests, evidence, traceability, and runbook docs.
- M4 Edge rollout endpoint remains a planning/authorization API; its service
  explicitly states that actual binary distribution/install is still an executor
  step.
- Native Alpine installer is present and targets `/usr/local/bin/ainet-edge`,
  `/etc/ainet-edge/*`, `/var/lib/ainet-edge`, and OpenRC service `ainet-edge`.
- Security follow-up recorded: the current Edge facts fallback uses system
  `sshpass -p` and writes debug output to `/root/edge-debug.log`; this requires
  hardening before production claims because process arguments/debug paths can
  expose credentials.
- No application source was changed during this audit.
### Native Alpine project correction — 2026-09-04T20:55:00+08:00

- Reopened `BGP-LAB` through the approved Central GNS3 endpoint and verified its
  current inventory.
- The previously referenced Alpine node ID is not present in `BGP-LAB`; it is in
  the separate opened project `TEST-EDGE`.
- Current native lab inventory: `TEST-EDGE` contains `ALPINE1`, `ALPINE2`,
  `IOSv1`, `IOSv2`, `NAT1`, `NAT2`, `Switch1`, and `Switch2`.
- `ALPINE1` is currently started and exposes console port `5022`.
- `BGP-LAB` currently contains `R1`, `PC1`, `EDGE-LAN-SW2`, and the Docker
  `EDGE-2` node; its nodes are stopped except the switch/cloud state.
- Deployment must target `TEST-EDGE/ALPINE1` and its associated IOSv1 path,
  not the old `BGP-LAB` node ID. No topology mutation was performed.
### Native Alpine deployment readiness probe — 2026-09-04T21:15:00+08:00

- Reopened and inspected the correct GNS3 project `TEST-EDGE`; native `ALPINE1`
  is node `16b41bdc-e99d-4ac3-b2ec-e4ea3b28e2c6`, console `5022`.
- Approved read-only console probe succeeded: `eth0` has `192.168.42.188/24`,
  `eth1` has the customer-LAN address `192.168.1.10/24`, and a default route is
  present.
- Approved console liveness probe returned `ALPINE_PROBE_OK`.
- Existing deployment helper default target is stale for this runtime; it must
  use the discovered Alpine address or a console/transfer path.
- Read-only SSH probe to `root@192.168.42.188:22` timed out; no installation
  command or secret transfer was attempted.
- Probe of the prior GNS3-VM HTTP transfer endpoint produced no positive transfer
  evidence; native binary deployment remains blocked on a reachable authenticated
  transfer/console bootstrap path.
- No source code or application configuration was changed in this checkpoint.
### Alpine SSH bootstrap checkpoint — 2026-09-04T21:35:00+08:00

- Through the approved GNS3 console endpoint for `TEST-EDGE/ALPINE1`, installed
  or verified Alpine OpenSSH packages, generated host keys, enabled `sshd` in
  the default OpenRC runlevel, and restarted the service.
- Follow-up read-only verification confirmed `/usr/sbin/sshd` and listeners on
  `0.0.0.0:22` and `:::22`.
- The same verification found an older manually launched Edge binary listening
  on `127.0.0.1:9443`; the managed native OpenRC service and protected runtime
  files are not yet present in the expected paths.
- No new binary, certificate, keystore, or device credential was transferred.
- Next action: establish a controlled transfer path to `ALPINE1`, install the
  current native binary and protected runtime files, replace the unmanaged
  listener with the OpenRC service, then verify Central HELLO/READY.
### Native Alpine service installation checkpoint — 2026-09-04T22:10:00+08:00

- Verified on `TEST-EDGE/ALPINE1` that native Edge artifacts already exist under
  `/root`: current binary, CA/certificate/key, keystore, and journal; the manual
  process binds only to `127.0.0.1:9443`.
- Began an approved console migration to standard OpenRC locations using the
  existing local artifacts and the repository Alpine init/confd files. The
  console command timed out before a completion marker was returned.
- A follow-up read-only file check also timed out; completion of the copy is
  therefore unverified. No manual kill/restart was issued after the timeout,
  preventing an uncertain partial operation from disrupting the running lab.
- Current status: native Edge service migration `IMPLEMENTED_UNVERIFIED`;
  Central→Edge mTLS and `device.read.facts` rerun are not yet claimed.
- Next action: recover Alpine console responsiveness, inspect file presence, then
  finish idempotent file installation and controlled service takeover with audit
  evidence.
### Native Alpine OpenRC installation — 2026-09-04T22:45:00+08:00

- Restarted `TEST-EDGE/ALPINE1` through the approved GNS3 lifecycle endpoint to
  recover the console.
- Reused the existing Alpine-local binary and runtime artifacts; copied the
  binary to `/usr/local/bin/ainet-edge` and runtime files to `/etc/ainet-edge/`.
- Installed repository OpenRC files at `/etc/init.d/ainet-edge` and
  `/etc/conf.d/ainet-edge`; configured permissions and registered the service in
  the default runlevel.
- `rc-service ainet-edge start` returned `[ ok ]` and `status: started`.
- Follow-up console output became unreliable after service start; listener
  binding and Central HELLO/READY are therefore still UNVERIFIED. No
  `device.read.facts` task was dispatched.
- Docker Edge remains excluded from the native deployment target.
### Native control-path topology verification — 2026-09-04T23:15:00+08:00

- Correct native lab is `TEST-EDGE`, not `BGP-LAB`.
- Verified topology: `ALPINE1 eth1 -> Switch1 -> IOSv1 e0`; `ALPINE1 eth0 -> NAT1`.
- `ALPINE1` is started with console `5022`; `IOSv1` is started with console `5008`.
- ALPINE1 previously reported `192.168.42.188/24` on NAT-facing `eth0`,
  `192.168.1.10/24` on customer-facing `eth1`, and a default route.
- Central Windows currently has HTTP transfer service on port `8899` and API on
  port `8000`; no evidence yet proves Central can reach Alpine's port `9443`.
- Native OpenRC service start returned success, but follow-up console output did
  not provide reliable listener evidence. The next gate is control-path proof:
  Alpine listener on a routable/bound address, Central HELLO/READY, then the
  read-only facts task.
### Native Edge outbound control-path diagnosis — 2026-09-05T00:30:00+08:00

- Confirmed direct Central Windows → Alpine NAT inbound TCP is unavailable;
  therefore native Edge uses outbound mTLS client mode as designed.
- Started the temporary lab Central mTLS listener on `172.21.0.1:8443`.
- First Alpine configuration used a duplicated base path and produced
  `/api/v1/control/v1/control/hello` with HTTP 404. Corrected the service base
  URL to `/api`.
- After correction, Central received `/api/v1/control/hello` from the GNS3 VM,
  proving outbound network reachability and TLS transport. Central returned HTTP
  422, so the remaining issue is application payload/identity validation rather
  than TCP reachability or the duplicated URL.
- No `device.read.facts` dispatch was attempted. No device credential was sent
  by the test task.
- Current next action: capture the non-secret 422 validation body or compare the
  running Alpine binary's HELLO contract with the Central schema, then rerun
  HELLO/READY before dispatching a task.
### Native Edge HELLO/READY contract fix â€” 2026-09-05T00:55:00+08:00

- Diagnosed the HTTP 422 response from Central as a schema mismatch: the Go
  client serialized an unset `unresolved_attempt_ids` slice as JSON `null`,
  while Central requires a list.
- Extended the existing Go control client to normalize a nil slice to an empty
  list and added a focused regression test. The response-body diagnostic is
  bounded and contains no credentials.
- `go test ./...` passed with the workspace-local Go build cache; the updated
  Linux binary was built and transferred to native `TEST-EDGE/ALPINE1`.
- Restarted the Alpine OpenRC service using the updated binary. Central mTLS
  logs then recorded `/api/v1/control/hello` HTTP 200 followed by
  `/api/v1/control/ready` HTTP 200.
- Gate result: native Alpine outbound control channel and HELLO/READY are
  `PASS`; `device.read.facts` execution is still pending.
- Files changed in this checkpoint: existing Go control client and its test;
  no application source outside the control contract was introduced.
- Next action: inspect the existing capability request and `r1-m1` inventory
  record, dispatch one read-only facts task, and capture the result/audit.
### Native Alpine runtime and dispatch boundary checkpoint â€” 2026-09-05T01:05:00+08:00

- Corrected the Go heartbeat JSON contract by adding snake_case JSON tags to
  `PresenceHeartbeat` and `TaskHeartbeat`; Go package tests remained passing.
- Built the Edge binary explicitly for `GOOS=linux`, `GOARCH=amd64`. An earlier
  local build had been Windows format and Alpine reported `Exec format error`;
  this was corrected and verified by a live Alpine process.
- Renewed the lab PKI chain after the original CA and leaf certificates expired:
  generated a new lab CA plus matching Central and `edge-001` certificates,
  installed the CA and matching Edge key/certificate on Alpine, and restarted
  the temporary Central mTLS listener.
- Live native control evidence after renewal: Alpine process is running;
  Central recorded HELLO HTTP 200, READY HTTP 200, and heartbeat HTTP 200.
- Started Docker Desktop Redis as container `ainet-redis`, exposed locally on
  port 6379, and verified `redis-cli ping` returned `PONG`.
- Updated runtime `.env` dispatch target from the obsolete server-mode
  `172.21.0.2:9443` to native Central listener `172.21.0.1:8443`, with the
  renewed lab CA/client certificate paths; restarted the main Central API.
- A read-only `device.read.facts` request for inventory device `r1-m1` still
  returned HTTP 503. Evidence review shows the Go client-mode path currently
  implements HELLO/READY and heartbeats but no outbound task receive/poll or
  bidirectional stream. Central's HTTP dispatcher therefore cannot deliver a
  task through the native client session yet.
- Gate result: native Alpine identity, mTLS, shared Redis availability, and
  presence heartbeat are `PASS`; native task delivery and R1 facts remain
  `BLOCKED_BY_IMPLEMENTATION_GAP`. M1 is not complete.
- Commands/tests: Go package tests passed; Docker Redis `PONG`; GNS3 console
  lifecycle/install commands succeeded; task API response was HTTP 503.
- Security: no passwords or private key contents were written to this log;
  temporary PKI files remain lab-only and production revocation/rotation is
  still unverified.
- Next action: extend the existing outbound control protocol with a
  capability-safe task receive path (poll or long-lived stream), connect it to
  the existing Central lease/dispatch service, then rerun the single facts
  task before adding further capabilities.
### Native outbound task polling implementation â€” 2026-09-05T02:00:00+08:00

- Extended the existing Edge session registry with task enqueue, claim, result,
  and bounded result-wait operations for both memory and Redis implementations.
- Added authenticated Central control endpoints for `tasks/next` and
  `tasks/result`; task dispatch now uses the existing TaskAttempt lease path and
  shared registry instead of creating a second jobs subsystem.
- Extended the Go native client with authenticated task polling and result
  submission. Client mode now loads the protected local keystore and executes
  only the existing `device.read.facts` capability through `FactsExecutor`.
- Updated the Alpine OpenRC configuration to client mode including the local
  keystore reference. Deployed a Linux amd64 build and verified the native
  process is running.
- Go regression suite: all packages passed. Python control/Redis tests: 11
  passed, 1 skipped (live Redis test marker not enabled).
- Live control endpoint evidence: Central returned HTTP 200 to repeated
  `/control/tasks/next` polling and heartbeat remained HTTP 200.
- End-to-end facts task remains unverified: the current Alpine log reports
  `x509: certificate signed by unknown authority` after PKI rotation, despite
  matching CA/leaf file hashes. The task API therefore returned HTTP 503 and no
  R1 result is claimed.
- Security: task payload remains capability-based and contains only
  `credential_ref`; no credential values were logged. Temporary diagnostic PKI
  material remains lab-only.
- Next action: resolve the live TLS trust discrepancy (server certificate
  chain/endpoint process), verify one task reaches `FactsExecutor`, then capture
  normalized R1 facts and audit evidence.
### Shared Redis session follow-up â€” 2026-09-05T03:00:00+08:00

- Confirmed the outbound task polling implementation is deployed on native
  Alpine and Central `/control/tasks/next` responds HTTP 200 over mTLS.
- Confirmed the live Redis container and Python Redis adapter independently with
  a passing live Redis test.
- Restarted the exact 8443 listener process and added a temporary non-secret
  startup diagnostic; it reported `edge session backend: redis`.
- Runtime inconsistency remains: Redis `DBSIZE` stays zero while the Edge
  continues receiving HTTP 200 polling responses. This indicates the observed
  polling session is stale or another in-memory process is still serving part of
  the control path; task API continues to fail closed with HTTP 503.
- No device task result, password, private key, or raw secret was written to
  the session log. M1 remains incomplete.
- Next action: isolate and terminate all stale 8443/8000 lab processes, start a
  single controlled pair with explicit Redis configuration, verify a new HELLO
  creates a Redis key, then dispatch the facts task.
### M1 task UI result rendering â€” 2026-09-05T03:30:00+08:00

- Audited the existing `src/views/tasks/` page and backend task mapper; it
  already refreshes on the task SSE stream and uses the existing task detail
  endpoint.
- Extended existing `Task` typing/normalization to retain `output`,
  `attempt_id`, and `execution_location` from the native Edge result.
- Extended the existing task detail view to display execution location, attempt
  identity, and a bounded readable JSON representation of the normalized result.
- Fixed a pre-existing missing `EmptyState` import in the devices view exposed
  by the full TypeScript build.
- `npm.cmd run build` completed through TypeScript and Vite artifact generation;
  `dist/index.html` and asset output were produced. Vite emitted only a
  deprecation warning for `optimizeDeps.esbuildOptions`.
- UI requirement status: `IMPLEMENTED_UNVERIFIED`; browser visual evidence is
  still required before marking it VERIFIED. No new frontend subsystem was
  created.
### Native Alpine M1 vertical slice PASS â€” 2026-09-05T03:10:00+08:00

- Isolated stale Central processes and started one controlled API pair on ports
  8000 and 8443 with explicit Redis configuration.
- Verified native Alpine task polling and Central shared-session control path.
- Added the current TEST-EDGE IOSv1 inventory record separately from the
  historical `r1-m1` record because IOSv1 is `192.168.1.1` in this topology;
  the historical `r1-m1` `192.168.10.1` identity was preserved.
- First execution with `r1-lab` failed closed because that reference is absent
  from the Alpine keystore. Repository evidence identified the provisioned
  Edge-001 reference `a-r1`; no credential value was displayed or logged.
- Final read-only execution succeeded: Central task API returned HTTP 200,
  TaskAttempt `SUCCEEDED`, and Edge returned normalized Cisco facts for R1
  (`15.6(2)T`) from `192.168.1.1`.
- Evidence captured at
  `docs/evidence/m1-vertical-slice/native-alpine-iosv1-facts-20260904.json`.
- Gate result: native Alpine control channel, Redis session queue, task polling,
  local Edge credential resolution, SSH execution, normalized result, and audit
  are `PASS` for this vertical slice. Production readiness remains `NOT READY`;
  retry/replay hardening, revoke/rollback, HA, and broader acceptance remain.

### Edge task contract regression and production gate — 2026-09-05

- Added a focused regression test to the existing `test_edge_control.py` suite
  for the native Edge task round-trip: `enqueue → tasks/next → tasks/result`.
- No second task or jobs subsystem was created; the test uses the existing
  `InMemoryEdgeSessionRegistry` seam and preserves production Redis behavior.
- Test result: `backend/tests/test_edge_control.py` and
  `backend/tests/test_edge_contracts.py` passed, `15 passed`.
- Executable production gate was run and correctly failed closed. Remaining
  required failures are `LIVE-POSTGRES`, `LIVE-PKI-OVERLAY`, and
  `LIVE-GNS3-OVERLAP`; release version, commit, and licensing decision are
  still unconfigured. Evidence artifacts were generated under
  `docs/evidence/production-gates/`.
- Security: test payload contains only a credential reference; no credential
  value, certificate, private key, or device secret was logged.
- Next action: complete one live production gate, prioritizing PostgreSQL
  durability/recovery evidence, before starting broader HA work.

### PostgreSQL live gate reconnaissance — 2026-09-05

- Confirmed the active Windows service is `postgresql-x64-18` and PostgreSQL
  reports `127.0.0.1:5432 - accepting connections` via `pg_isready`.
- Confirmed the repository configuration currently resolves to
  `TASK_ATTEMPT_BACKEND=memory` and has no `POSTGRES_DSN`.
- The existing migration and live test are present:
  `backend/migrations/001_task_attempts.sql` and
  `backend/tests/test_postgres_live.py`. The live test requires an explicit
  DSN and performs concurrent claim verification, but restore evidence still
  requires a controlled database backup/restore procedure.
- No database login was attempted without an approved DSN; no password,
  token, or database secret was read or written.
- Gate status remains `LIVE-POSTGRES: NOT_CONFIGURED`, not a code failure.
- Blocker/next action: operator must provide the intended PostgreSQL database
  name, username, and approved DSN/password handling method; then apply the
  migration and run the live concurrency/recovery/restore evidence procedure.

### PostgreSQL gate runbook alignment — 2026-09-05

- Updated `docs/runbooks/deployment-runbook.md` to describe the actual native
  Alpine outbound-polling Edge mode instead of the obsolete server-mode
  listener instructions.
- Added a fail-closed PostgreSQL live-gate procedure with DSN placeholders,
  migration/test steps, and explicit backup/restore evidence requirements.
- Expanded `docs/evidence/postgres/README.md` with the operator evidence
  checklist. No database credentials or connection strings were written.
- No application source behavior changed in this step; live PostgreSQL remains
  blocked only by the missing approved DSN/database access and restore drill.

### PostgreSQL access verification — 2026-09-05

- Confirmed no `PG*`, `POSTGRES*`, or `DATABASE*` environment variable is
  configured for this session.
- A read-only local connection probe using the standard `postgres` role with
  password prompting disabled was rejected with `no password supplied`.
- No password guessing, reset, authentication bypass, or database mutation was
  performed. PostgreSQL gate remains `NOT_CONFIGURED` pending approved access.

### PostgreSQL migration and live lease evidence — 2026-09-05

- Using the operator-provided local database credential only in the temporary
  process environment, connected to PostgreSQL 18 database `postgres`.
- Applied `backend/migrations/001_task_attempts.sql` successfully and
  idempotently; the `task_attempts` table and indexes are present.
- Extended `backend/tests/test_postgres_live.py` to cover lease renewal and
  expiry recovery in addition to concurrent single-owner claim.
- Live result: `2 passed`.
- Evidence saved at
  `docs/evidence/postgres/postgres-live-20260905.json` with status `PARTIAL`.
- Restore drill is still pending, so `LIVE-POSTGRES` must remain fail-closed;
  no password, DSN, certificate, or private key was written to evidence/logs.

### PostgreSQL isolated restore drill — 2026-09-05

- Inserted one non-secret sentinel TaskAttempt into the migrated staging table,
  created a custom-format data dump, and restored it into an isolated temporary
  PostgreSQL database.
- Verified the sentinel after restore, then removed only the temporary database
  and temporary dump file.
- Restore result: `PASS`; no production database rows were deleted.
- Updated `docs/evidence/postgres/postgres-live-20260905.json` to `PASS`.
- PostgreSQL migration, concurrency, renewal, expiry recovery, and restore
  evidence are now complete. Remaining production blockers are unrelated gates:
  PKI/overlay, GNS3 overlap, release metadata, and licensing decision.

### PostgreSQL production-gate integration — 2026-09-05

- Replaced the PostgreSQL gate placeholder with an executable command that
  requires `POSTGRES_DSN` from the operator environment and runs the live test;
  no credential is embedded in `docs/production/production-gate.json`.
- Verified the full production gate with the approved temporary environment:
  `LIVE-POSTGRES` now passes. Global result remains `FAIL` as designed because
  `LIVE-PKI-OVERLAY`, `LIVE-GNS3-OVERLAP`, release version/commit, and licensing
  decision remain incomplete.

### PKI/overlay gate reconnaissance — 2026-09-05

- Ran the existing PKI, identity, control-revoke, and overlay contract tests:
  `16 passed`.
- Confirmed the Windows `ZeroTierOneService` is running, but the local CLI
  cannot access `authtoken.secret`; no private controller API or authorized
  overlay network is available for a live deauthorization test.
- Confirmed the repository still lacks durable certificate serial/fingerprint
  invalidation bound to the revoke endpoint. Local lifecycle revoke and session
  disconnect are tested, but they are not sufficient for the production gate.
- No overlay membership was changed and no secret/token was read or logged.
- Gate remains `LIVE-PKI-OVERLAY: NOT READY`; next action requires an approved
  private ZeroTier/controller endpoint plus PKI revocation authority, followed
  by live deauthorization and post-revoke handshake evidence.

### Private ZeroTier controller and Ubuntu overlay member — 2026-09-05

- Confirmed `UBUNTU1` exists in TEST-EDGE, is started, and has console `5013`.
- Read-only/runtime check showed ZeroTier `1.16.2 ONLINE` with member ID
  `e2542655d9`. It initially reported `ACCESS_DENIED` because the controller
  had not authorized it.
- Authorized the member through the GNS3 VM private controller API for network
  `14139cc3dd000001`, refreshed the client membership, and verified network
  status `OK` / `PRIVATE`.
- Saved partial evidence at
  `docs/evidence/pki-overlay/zerotier-controller-ubuntu1-20260905.json`.
- No controller token, password, certificate, or private key was recorded.
- This proves private controller + authorized client preparation only; live
  deauthorization, certificate invalidation, and post-revoke rejection remain
  pending.

### ZeroTier controller IP assignment follow-up — 2026-09-05

- Enabled the lab network IPv4 pool `10.201.0.1–10.201.0.254` and assigned
  `10.201.0.10` to Ubuntu1 member `e2542655d9` through the private controller.
- Controller API returned the assignment, but Ubuntu1 continued to report no
  assigned overlay IP (`listnetworks` showed `-`).
- Interpretation: controller authorization/API is reachable from the admin
  path, but the ZeroTier client has not synchronized the controller network
  configuration over the overlay path. Overlay connectivity is therefore still
  pending; no deauthorization evidence is claimed.
- Removed temporary controller/client probe scripts. No credentials or tokens
  were recorded.
- Next action: verify controller-node reachability/peer discovery from Ubuntu1
  and confirm the controller service is reachable as a ZeroTier controller, or
  use a supported private-controller topology with a reachable controller node.

### ZeroTier managed-IP synchronization checkpoint — 2026-09-05

- Ubuntu1 sees controller node `14139cc3dd` as a `DIRECT` peer and reports
  `allowManaged=1`; local client settings are not blocking managed addresses.
- Controller API retains Ubuntu1 assignment `10.201.0.10` and `authorized=true`.
- After client refresh/restart, Ubuntu1 still reports network `OK PRIVATE` but
  no assigned IP and no address on `zt27hjzq64`.
- Conclusion: authorization/API setup is complete, but managed-IP
  synchronization is not yet proven. Do not proceed to overlay ping or
  deauthorization evidence until the address appears on the client.
- Removed diagnostic probe scripts. No controller token/password was stored.
- Next session should inspect controller network/member logs and the effective
  controller node configuration, then test with a supported controller/client
  topology if the GNS3 VM controller cannot publish managed addresses.

### ZeroTier controller synchronization diagnosis — 2026-09-05

- Read-only inspection of GNS3 VM confirmed controller node `14139cc3dd` is
  `ONLINE`, network definition `14139cc3dd000001.json` exists, and the service
  has no reported startup errors relevant to the network.
- Ubuntu1 sees controller `14139cc3dd` as a direct peer. Its network client
  setting `allowManaged` is `1`.
- Controller member state contains `authorized=true` and assignment
  `10.201.0.10`, but Ubuntu1 still has no address on `zt27hjzq64`.
- Did not manually add the IP because that would not prove controller-managed
  overlay behavior. Temporary diagnostic script was removed.
- Current blocker is managed-IP publication/synchronization in this
  controller topology. Next session should inspect the effective controller
  network JSON/API response and consider a supported Debian/Ubuntu controller
  host if the GNS3 VM service cannot publish assignments.

### GNS3 overlapping-subnet gate reconnaissance — 2026-09-05

- GNS3 controller `172.21.0.2` is reachable and reports version `2.2.61`.
- Project `TEST-EDGE` is open with `ALPINE1`, `ALPINE2`, `IOSv1`, and `IOSv2`
  started. Existing topology evidence confirms both IOSv devices use
  `192.168.1.1/24` behind separate switches.
- Scoped routing regression tests passed: `8 passed`.
- Existing live two-Edge evidence is partial: `edge-b` reaches IOSv2 and
  returns normalized facts, while `edge-001` to IOSv1 remains pending due to
  an Edge keystore/device credential mismatch. This is not yet sufficient for
  the positive two-Edge acceptance gate.
- No topology changes or credential updates were performed in this step.
- Next action: reconcile the approved IOSv1 credential with the Edge-local
  keystore without logging its value, rerun both positive dispatches, and save
  the complete overlapping-subnet evidence.

### GNS3 Edge-001 connectivity probe — 2026-09-05

- Performed a secret-free-output SSH probe from Alpine1 toward IOSv1 using the
  operator-provided password only through the temporary process input.
- Result: `R1_AUTH=FAIL` because Alpine1 timed out connecting to
  `192.168.1.1:22`; the SSH server did not reach password authentication.
- Therefore no credential mismatch is proven yet. No keystore, IOSv1
  configuration, or topology was modified.
- Removed the temporary probe after execution. Next action is to restore or
  validate the Alpine1-to-Switch1-to-IOSv1 LAN path, then rerun the credential
  probe and facts task.

### GNS3 Edge-001 LAN and SSH recovery — 2026-09-05

- Corrected the console target from stale port `5019` to active Alpine1 console
  port `5022`.
- Read-only Alpine1 probe confirmed `eth1=192.168.1.10/24`, connected link
  state, route `192.168.1.0/24`, and ping to IOSv1 `192.168.1.1` with 0% loss.
- SSH password authentication from Alpine1 to IOSv1 passed. The previous
  timeout was transient; credential mismatch is no longer indicated.
- Temporary probes were removed. No keystore, router configuration, or
  topology was changed.
- Next action: rerun Central `device.read.facts` for the Edge-001 scoped device
  and capture the complete two-Edge normalized result.

### GNS3 overlapping-subnet live acceptance — 2026-09-05

- After restoring Alpine1 LAN reachability, Central dispatched
  `device.read.facts` to `r1-native-edge001` via `edge-001`.
- Result: TaskAttempt `SUCCEEDED`; normalized facts identified IOSv1 as R1,
  Cisco IOS `15.6(2)T`, management IP `192.168.1.1`.
- Combined with the existing Edge-B → IOSv2 success, both isolated Edge paths
  now return normalized facts for devices sharing `192.168.1.1`.
- Evidence saved at `docs/evidence/gns3-overlap/live-two-edge-proof-20260905.json`;
  raw CLI output and credential values were not stored.
- GNS3 overlapping-subnet acceptance is now `PASS` for this lab topology.

### GNS3 overlap evidence completion — 2026-09-05

- Updated the live evidence and traceability matrix with the successful
  Edge-001 → IOSv1 result alongside the existing Edge-B → IOSv2 result.
- Both devices use `192.168.1.1` on isolated LANs and both return normalized
  `device.read.facts`; no Central route conflict was observed.
- `NET-OVERLAP-001` is now marked `VERIFIED` for the TEST-EDGE lab topology.
- Production gate evidence now points to the completed live artifact, while the
  command remains intentionally unconfigured until a repeatable GNS3 acceptance
  command is available.

### GNS3 evidence validator integration — 2026-09-05

- Added `tools/validate_gns3_overlap_evidence.py`, a fail-closed validator for
  the captured live artifact. It requires both Edge results to be `SUCCEEDED`
  and both management IPs to equal `192.168.1.1`.
- Connected the validator to the `LIVE-GNS3-OVERLAP` production gate. It
  validates recorded evidence; it does not pretend to replace a fresh live
  GNS3 run.

### Production gate reduction after PostgreSQL/GNS3 evidence — 2026-09-05

- GNS3 evidence validator returned `GNS3_OVERLAP_EVIDENCE=PASS`.
- Full executable production gate now reports only one required technical gate
  failure: `LIVE-PKI-OVERLAY`; PostgreSQL and GNS3 overlap gates pass.
- Release metadata (`version`, `git_commit`) and licensing decision remain
  intentionally unconfigured pending formal release review.

### Architecture decision: direct mTLS control, optional ZeroTier — 2026-09-05

- Confirmed the intended runtime contract: Central ↔ Edge control uses direct
  HTTPS/mTLS; Edge executes device capabilities locally on the customer LAN.
- ZeroTier is an optional overlay/client integration behind `OverlayProvider`,
  not a mandatory proxy for task execution and not a replacement for Central
  identity/session enforcement.
- Recorded high-impact decision in
  `docs/adr/0001-direct-mtls-control-optional-zerotier-overlay.md` and aligned
  the deployment runbook.
- No application source behavior changed. The live PKI/overlay gate remains
  required only for production claims involving overlay membership and revoke.

### Session handoff checkpoint — 2026-09-05

#### Current outcome

- Native Alpine Edge vertical slice is proven: Central → Redis session queue →
  Alpine Edge → Cisco IOSv facts → normalized result → audit.
- PostgreSQL gate is `PASS`: migration, concurrent single-owner claim, renewal,
  expiry recovery, and isolated restore drill are evidenced.
- GNS3 overlap gate is `PASS` for TEST-EDGE: Edge-001/IOSv1 and Edge-B/IOSv2
  both use `192.168.1.1` on isolated LANs and both return normalized facts.
- Production gate result is still `FAIL / NOT READY`; the only remaining
  required technical gate is `LIVE-PKI-OVERLAY`.

#### Important files changed in this session

- `backend/tests/test_edge_control.py` — native Edge task poll/result contract
  regression test.
- `backend/tests/test_postgres_live.py` — live renewal and expiry recovery
  coverage.
- `backend/migrations/001_task_attempts.sql` — applied to local PostgreSQL 18
  staging database; no new migration was added in the latest step.
- `tools/validate_gns3_overlap_evidence.py` — fail-closed evidence validator.
- `docs/production/production-gate.json` — PostgreSQL and GNS3 evidence/gates
  connected without embedded secrets.
- `docs/evidence/postgres/postgres-live-20260905.json` — PostgreSQL PASS.
- `docs/evidence/gns3-overlap/live-two-edge-proof-20260905.json` — GNS3 overlap
  PASS.
- `docs/evidence/pki-overlay/README.md` — PKI/overlay blocker and acceptance
  sequence.
- `docs/runbooks/deployment-runbook.md` — native Alpine polling and PostgreSQL
  gate procedure.
- `docs/traceability/requirements-matrix.md` — `NET-OVERLAP-001` VERIFIED.

#### Last verified commands/results

- `pytest backend/tests/test_edge_control.py backend/tests/test_edge_contracts.py -q` → `15 passed`.
- `pytest backend/tests/test_postgres_live.py -q` with approved temporary DSN → `2 passed`.
- `pytest backend/tests/test_overlay_provider.py backend/tests/test_edge_identity.py backend/tests/test_edge_control.py -q` → `16 passed`.
- `pytest backend/tests/test_execution_routing.py backend/tests/test_gns3_approval_guard.py -q` → `8 passed`.
- `python tools/validate_gns3_overlap_evidence.py` → `GNS3_OVERLAP_EVIDENCE=PASS`.
- Full production gate → `FAIL`; only `LIVE-PKI-OVERLAY` remains as a required
  technical gate, plus release metadata and licensing placeholders.

#### Next-session plan, in order

1. Do not alter the working PostgreSQL/GNS3 evidence.
2. Implement or extend durable certificate serial/fingerprint revocation and
   bind it to the actual mTLS handshake enforcement path.
3. Obtain approved private ZeroTier/controller access and run live member
   deauthorization against a disposable lab member.
4. Capture redacted PKI/overlay evidence and connect a repeatable validator to
   `LIVE-PKI-OVERLAY`.
5. Run the full production gate again.
6. Only after all technical gates pass, set release version/commit and record
   the licensing decision from verified upstream/license evidence.

#### Security and operational notes

- Never place passwords, DSNs containing passwords, API tokens, certificates,
  private keys, or raw device secrets in session logs/evidence.
- The operator-provided password was used only in temporary process scope for
  local PostgreSQL and lab SSH checks; it was not stored in repository files.
- Current native Edge executor still requires production hardening review around
  secret-safe SSH invocation and local debug logging before commercial launch.
- Do not mark the platform production-ready merely because PostgreSQL and GNS3
  gates pass; PKI/overlay, HA, monitoring, update/rollback, licensing, and
  release metadata remain part of the final production decision.

### ZeroTier managed-IP synchronization resolved — 2026-09-05

- Root cause found: the IP pool `10.201.0.1–10.201.0.254` had no matching
  managed route, so the client ignored the assignment.
- Added managed route `10.201.0.0/24` through the private controller API.
- Verified Ubuntu1 reports `OK PRIVATE` with
  `zt27hjzq64=10.201.0.10/24`.
- Updated overlay preparation evidence with `overlay_connectivity=PASS`.
- Removed temporary diagnostic scripts. No token/password was recorded.
- Next action: test overlay ping/member connectivity, then execute controlled
  ZeroTier deauthorization and verify the member returns to denied state.

### Controlled ZeroTier deauthorization observation - 2026-09-05

- Disposable Ubuntu1 member was deauthorized through the private controller API;
  controller state reported `authorized=false`.
- Ubuntu1 was checked after the observation delay but still reported `OK
  PRIVATE` with its assigned overlay address. Client-side membership rejection
  was therefore not proven and the live overlay gate remains partial.
- The member was reauthorized immediately and verified back to `OK PRIVATE`,
  restoring the lab state.
- Evidence was updated in
  `docs/evidence/pki-overlay/zerotier-controller-ubuntu1-20260905.json` and
  `docs/evidence/pki-overlay/README.md`.
- Temporary probe scripts were removed after the test. No token, password,
  certificate, private key, or raw device output was logged.
- Remaining work: determine controller/client propagation behavior, prove client
  denial, and connect certificate revocation to mTLS handshake enforcement.

### ZeroTier revoke refresh solution - 2026-09-05

- Repeated the disposable-member test using controller deauthorization followed
  by Ubuntu1 `leave` and `join`.
- While revoked, Ubuntu1 changed to `REQUESTING_CONFIGURATION` and had no
  assigned overlay IP; this proves the previous stale `OK` state was a client
  synchronization/refresh issue rather than a missing IP pool.
- After controller reauthorization and another refresh, Ubuntu1 returned to
  `OK PRIVATE` with its assigned overlay IP.
- Explicit `ACCESS_DENIED` was not observed before restoration, so the live
  overlay gate remains `PARTIAL`, not PASS.
- Evidence was updated and temporary probes were removed. No credentials,
  tokens, certificates, keys, or raw device output were recorded.

### Durable certificate revocation foundation - 2026-09-05

- Added `backend/app/services/certificate_revocation.py` with normalized
  SHA-256 certificate fingerprints, serial metadata, atomic durable JSON state,
  and fail-closed handling for malformed presented fingerprints.
- Extended Central Edge control so a presented revoked certificate fingerprint
  is rejected at `HELLO`; operator revoke can persist a certificate fingerprint
  and serial while existing session disconnect/lifecycle enforcement remains in
  place.
- Added focused persistence and fingerprint tests. Result:
  `16 passed` for certificate revocation, Edge control, and Edge identity tests.
- This is Central enforcement foundation only. The live TLS terminator still
  must supply a trusted certificate fingerprint and a live revoked-certificate
  handshake rejection test is still required before `PKI-REVOCATION-005` or
  `LIVE-PKI-OVERLAY` can be marked verified.
- No certificate private keys, passwords, tokens, or raw device output were
  written to logs or evidence.

### Live Central certificate revocation test - 2026-09-05

- Generated a disposable lab certificate under temporary `tmp` material and
  connected to Central mTLS on port 8443.
- Valid certificate HELLO succeeded with HTTP 200.
- Operator revoke persisted the certificate fingerprint and returned HTTP 200;
  five active sessions were disconnected.
- A second HELLO using the same mTLS certificate was rejected with HTTP 403
  (`Edge certificate is revoked`).
- Central application-layer certificate revocation is therefore proven. The
  TLS terminator still accepted the TLS handshake before the application
  rejection, so pre-HTTP handshake rejection remains unproven and the overall
  live PKI/overlay gate stays partial.
- Temporary certificate/private-key material and probe scripts were removed
  after the test. No secrets or private keys were recorded.

### TLS terminator contract documented - 2026-09-05

- Updated the deployment runbook to require a trusted mTLS terminator to verify
  the peer certificate, check durable revocation before HTTP proxying, strip
  client-supplied identity headers, and set the fingerprint header from the
  verified certificate.
- Updated `PKI-REVOCATION-005` to `IMPLEMENTED_UNVERIFIED`: Central app-layer
  enforcement is evidenced, but pre-HTTP TLS terminator rejection remains an
  operational deployment test.
- Updated PKI/overlay evidence status without claiming production readiness.

### TLS CRL pre-HTTP rejection harness - 2026-09-05

- Created a disposable TLS listener using the lab CA and a CRL containing the
  Edge certificate serial.
- The TLS server rejected the client certificate with `certificate revoked` and
  did not accept the connection for HTTP. This proves the fail-closed CRL
  pattern at TLS level in the lab harness.
- The harness is not a production reverse proxy and does not yet reload the
  Central dynamic revocation registry; production terminator integration stays
  unverified.
- PKI/overlay evidence and README were updated. Temporary CRL/bundle and
  scripts were removed; no private key or secret was recorded.

### Fail-closed PKI/overlay evidence gate - 2026-09-05

- Added `tools/validate_pki_overlay_evidence.py` and connected it to
  `LIVE-PKI-OVERLAY` in `docs/production/production-gate.json`.
- The validator requires controller readiness, overlay connectivity, explicit
  client denial, Central HTTP 403 after certificate revoke, and production TLS
  terminator integration. Missing any one condition returns FAIL.
- Current expected result is FAIL because client `ACCESS_DENIED` and dynamic
  production terminator integration are not yet evidenced.

### mTLS terminator deployment reference - 2026-09-05

- Added `deploy/mtls/nginx.conf.example` as the deployment reference for
  TLS 1.3, mandatory client certificate verification, CRL enforcement, and
  private proxying to Central FastAPI.
- The configuration deliberately strips client-supplied certificate identity
  headers. A trusted terminator module must derive the fingerprint from the
  verified peer certificate; static configuration alone is not marked as live
  production evidence.
- Runbook updated with CRL reload requirements. Production dynamic terminator
  integration remains unverified and the gate remains fail-closed.

### Nginx CRL deployment harness result - 2026-09-05

- Pulled the official `nginx:alpine` image into Docker Desktop and ran a
  disposable mTLS terminator with `ssl_verify_client on`, `ssl_crl`, and
  `ssl_verify_depth 2`.
- The revoked Edge certificate was still accepted by Nginx and the request was
  forwarded to Central, which returned HTTP 400 due to the missing application
  identity header. Nginx therefore did not prove CRL rejection in this setup.
- The result is recorded as a failed deployment harness, not as production
  evidence. The Python TLS CRL harness remains only a lower-level reference.
- The disposable Nginx container, CRL bundle, certificates, and probe scripts
  were removed after the test. Production gate remains fail-closed.

### GNS3 Ubuntu1 lab recovery - 2026-09-05

- The final ZeroTier denial probe encountered a closed `TEST-EDGE` project and
  Ubuntu1 console became unavailable while the VM rebooted; no denial result
  was inferred from that incomplete probe.
- Reopened `TEST-EDGE` through the authenticated GNS3 API and started Ubuntu1.
  The node reached its login console again. ZeroTier service starts during
  Ubuntu boot, but a post-boot client status still requires an interactive
  console login.
- Temporary recovery/status scripts were removed. The lab is restored, while
  the explicit `ACCESS_DENIED` evidence remains pending.

### Post-login ZeroTier verification - 2026-09-05

- After the operator logged into Ubuntu1, the client was verified twice as
  `OK PRIVATE` with overlay address `10.201.0.10/24`.
- A repeat deauthorization refresh probe did not return reliable serial-console
  output, so no `ACCESS_DENIED` claim was made and the existing evidence was
  left unchanged.
- `TEST-EDGE` remained `opened` and Ubuntu1 remained `started`; temporary
  status/deauthorization scripts were removed.

### ZeroTier denial retry blocked by GNS3 console - 2026-09-05

- Attempted the priority `ACCESS_DENIED` test after operator login. The
  controller update path was invoked, but the Ubuntu1 telnet console at port
  5013 refused the connection before the client refresh commands could be
  verified.
- GNS3 API still reports `TEST-EDGE=opened` and `UBUNTU1=started`, indicating
  a stale/unavailable console endpoint rather than a verified ZeroTier result.
- The probe did not modify evidence or claim PASS. Authorization recovery was
  attempted in the probe cleanup path, and the temporary probe was removed.
- Next action for this check is to repair/restart the Ubuntu1 console endpoint,
  log in again if required, then run the manual leave/join denial verification.

### Manual ZeroTier denial verification initiated - 2026-09-05

- Confirmed the operator's Ubuntu1 output was the authorized baseline:
  `OK PRIVATE` with `10.201.0.10/24`.
- Sent controller-side deauthorization for the disposable Ubuntu1 member;
  controller API returned HTTP 200.
- The member is intentionally left deauthorized pending the operator's manual
  `leave/join/listnetworks` output. No PASS evidence is claimed yet.

### ZeroTier ACCESS_DENIED proven - 2026-09-05

- Operator manually executed `leave`, `join`, waited 20 seconds, and ran
  `listnetworks` after controller deauthorization.
- Ubuntu1 returned `ACCESS_DENIED` and no assigned overlay IP. This proves the
  controller deauthorization reaches the client after the required refresh and
  propagation window.
- Controller authorization was restored with HTTP 200. Final authorized client
  refresh is still pending; evidence records the denial PASS but keeps overall
  PKI/overlay status partial until lab recovery is verified.
- No credentials, tokens, certificates, private keys, or raw device secrets
  were recorded.

### ZeroTier lab recovery verified - 2026-09-05

- After controller authorization was restored, the operator executed the final
  Ubuntu1 `leave/join` refresh and waited 20 seconds.
- `listnetworks` returned `OK PRIVATE` with overlay address `10.201.0.10/24`.
- The deauthorization evidence is now complete: controller revoke, client
  `ACCESS_DENIED` with no IP, controller reauthorization, and client recovery
  are all recorded.
- Overall `LIVE-PKI-OVERLAY` remains fail-closed because production gateway
  integration is not yet marked PASS; the ZeroTier member test itself is PASS.

### Gateway runtime hardening - 2026-09-05

- Hardened the existing compose `mtls` profile with restart policy, non-root
  read-only runtime, read-only PKI/revocation mounts, no-new-privileges,
  tmpfs, TCP liveness check, and CPU/memory limits.
- Updated the deployment runbook to distinguish the current liveness check
  from the still-required authenticated readiness and denial metrics.
- No production certificate or private key was added. The production gateway
  gate remains fail-closed pending supervised deployment evidence.

### Supervised gateway runtime lab validation - 2026-09-05

- Started the built gateway image with `restart=unless-stopped`, read-only root
  filesystem, restricted tmpfs, non-root UID `65532:65532`, and read-only PKI
  and revocation mounts.
- TCP listener was reachable and a certificate/identity-aligned HELLO reached
  Central with HTTP 200. An identity mismatch was rejected with HTTP 401.
- This validates the container security/runtime policy in the lab. Compose
  healthcheck configuration is present, but production readiness still needs
  authenticated readiness, denial metrics, approved PKI, and HA evidence.
- Disposable container and PKI material were removed after validation.

### Gateway readiness and denial metrics - 2026-09-05

- Added internal `/ready` and `/metrics` listeners to the dynamic gateway.
- Compose healthcheck now calls `/ready`; denial, proxied-request, and error
  counters are exposed for monitoring integration.
- Rebuilt the gateway image and passed focused tests: `3 passed`.
- Disposable container smoke test returned readiness `ready` and initialized
  all three metrics counters to zero, then the container was removed.
- Production still requires authenticated readiness exposure policy, metric
  scraping/alerts, and HA validation before the gate can pass.

### Monitoring inventory and gateway restart recovery - 2026-09-05

- Inspected the existing monitoring implementation before adding anything:
  `backend/app/api/v1/endpoints/monitoring.py`,
  `backend/app/services/monitoring_alerts.py`,
  `backend/app/api/v1/endpoints/alerts.py`, and the related tests/evidence.
- Decision: REUSE the existing monitoring and rule-based alert subsystem. No
  parallel Prometheus subsystem was created during this session; a future
  scrape/alert deployment must integrate with the existing health and alert
  surfaces.
- Started the built mTLS gateway as a disposable Docker runtime with
  `unless-stopped`, non-root UID `65532:65532`, read-only root filesystem,
  restricted `/tmp`, read-only PKI and revocation mounts.
- Restart recovery result: `/ready` returned `{"status":"ready"}` before
  restart and after restart; `/metrics` returned all three counters after
  restart; container state remained `running` with the expected runtime
  hardening settings.
- This is lab restart-recovery evidence only. It does not prove Central HA,
  distributed session routing, production monitoring scraping, or alert
  delivery.
- Verification rerun with repository `PYTHONPATH` and an isolated workspace
  temp directory passed the focused certificate/gateway suite: `3 passed`.
- Evidence validators: `GNS3_OVERLAP_EVIDENCE=PASS`; `PKI_OVERLAY_EVIDENCE`
  remains fail-closed with `incomplete:tls_terminator`.

### Official compose gateway deployment - 2026-09-05

- First compose build exposed a real packaging gap: the API imported the GNS3
  driver but `aiohttp` was missing from `backend/requirements.txt`.
- Added the missing runtime dependency and added `backend/.dockerignore` to
  prevent `.env`, test/cache data, logs, and temporary files from entering the
  API image build context. This avoids baking device secrets into the image.
- Rebuilt and started the official `backend/docker-compose.yml` `mtls` profile.
  Both `api` and `mtls-gateway` are running; gateway health is `healthy`.
- Gateway runtime inspection confirmed `65532:65532`, read-only root, and the
  `unless-stopped` restart policy.
- Authenticated mTLS HELLO from a Linux container using the Edge certificate
  reached the compose gateway and Central with HTTP 200. A Windows Schannel
  `curl.exe` PEM import attempt was not used as evidence; the container-side
  proof is the valid client path for this lab.
- The compose runtime currently uses development/lab PKI under
  `runtime/mtls`; it is not production PKI and must be replaced before launch.

### Native Alpine Edge reconnect attempt - 2026-09-05

- The official compose gateway is running and healthy, but the native Edge
  deployment could not yet be switched because the GNS3 `ALPINE1` node was
  stopped when inspected. It was started through the GNS3 API (console 5022).
- After boot, `172.21.0.20` was not reachable from the Windows host or GNS3 VM;
  SSH timed out and the VM could not ping the address. The existing Edge
  process observed earlier therefore cannot be treated as the active ALPINE1
  client proof.
- The source OpenRC configuration is correct for the intended client path:
  `--control-url https://172.21.0.1:8443/api`. Remaining operational blocker is
  restoring ALPINE1 interface/SSH configuration from its console, then rerun
  the deployment script and verify HELLO/heartbeat through compose.
- No application source was changed for this blocker. The failed deploy and
  reachability result are recorded to prevent claiming native Edge compose
  integration prematurely.

### TEST-EDGE interface mapping verification - 2026-09-05

- Queried the live GNS3 project topology instead of inferring interface roles.
- Confirmed `ALPINE1 Ethernet0/eth0 -> NAT3` and `ALPINE1 Ethernet1/eth1 ->
  Switch1`; `Switch1 -> IOSv1 Ethernet0`, where the lab R1 management address
  is on the customer LAN.
- Correction: the earlier recommendation to place `172.21.0.20` on `eth1`
  was incorrect for the current topology. Customer-LAN address `192.168.10.20`
  belongs on `eth1` only if that is the configured R1 segment; `eth0` should
  receive the NAT-side address/default route according to NAT3. Central
  reachability must be validated from the actual NAT path before setting the
  Edge control URL.
- No network configuration was changed by Codex in this check. Native Edge
  deployment remains blocked until ALPINE1 console state confirms both links,
  addresses, and SSH reachability.

### ALPINE1 live interface state - 2026-09-05

- Operator console evidence shows `eth0=192.168.42.188/24` with default route
  via `192.168.42.1`; this is the NAT/uplink interface and successfully reaches
  Central `172.21.0.1`.
- Operator console evidence shows `eth1=192.168.1.10/24`; this is the customer
  LAN interface connected to Switch1. The prior `192.168.10.0/24` R1 test is
  not applicable to the current TEST-EDGE topology.
- Next device-path check is `192.168.1.1` over `eth1`, followed by SSH host-key
  pinning. The deployment helper must not overwrite this working DHCP/static
  split or reuse the old `192.168.10.1` host-key assumption.
- Central reachability is now proven from the active Alpine node; Edge native
  redeployment remains pending device SSH validation and safe installer
  alignment.

### GNS3 console endpoint validation - 2026-09-05

- Reused the existing audited endpoint
  `/api/v1/gns3/projects/{project_id}/nodes/{node_id}/console-exec` with
  `X-Approved-By` and executed read-only commands directly on `ALPINE1`.
- Endpoint proof succeeded: Alpine console returned `CONSOLE_OK`, R1
  `192.168.1.1` responded through `eth1`, and TCP/22 was open.
- A follow-up interactive SSH/password probe did not return within the
  endpoint/tool timeout and is intentionally not counted as an authenticated
  login proof. No secret or command output containing a secret was recorded.

### R1 SSH proof via audited console endpoint - 2026-09-05

- Reused the existing audited GNS3 console-interactive endpoint with approval
  header `X-Approved-By` and a bounded SSH timeout.
- Alpine1 connected to R1 `192.168.1.1` using the required legacy Cisco SSH
  compatibility algorithms, completed authentication, and returned normalized
  read-only facts: Cisco IOSv Software, version `15.6(2)T`, plus uptime.
- R1 host-key fingerprint was observed in Alpine's known-hosts store and is
  available for subsequent pinning; the fingerprint value is intentionally
  excluded from this session log.
- This closes the Alpine-to-R1 SSH connectivity proof. Native Edge runtime
  deployment/configuration through the compose gateway remains the next step.

### Native Edge client runtime verification - 2026-09-05

- Reused the existing GNS3 console endpoint to inspect ALPINE1. The native
  binary is present and running with `--control-url https://172.21.0.1:8443/api`,
  Edge identity `edge-001`, and the expected mTLS file paths.
- Restarted the existing OpenRC Edge service through the audited console
  endpoint to reload its current certificate state.
- Alpine OpenSSL validation to the compose gateway passed TLS 1.3 server
  verification with the mounted CA and Edge client certificate.
- Go Edge HELLO is still not proven: the runtime reports `x509: certificate
  signed by unknown authority` after restart. Central compose logs show no
  native Edge HELLO, so no task/heartbeat success is claimed.
- Do not disable certificate verification. Next investigation is to compare
  the certificate actually presented on `172.21.0.1:8443` with the Go trust
  pool and verify the Go runtime/client certificate compatibility.

### Native Edge through official compose gateway - 2026-09-05

- Root cause isolated: stale Uvicorn mTLS process owned port `8443` and
  presented the old lab certificate instead of the compose gateway
  certificate. The process was verified by command line and stopped.
- Confirmed Alpine now sees the compose gateway certificate fingerprint; the
  old Edge certificate was also found in the durable revocation registry.
- Reused the existing audited GNS3 console endpoint to transfer the current
  non-revoked lab certificate set to ALPINE1 from a temporary local server,
  restarted the OpenRC Edge service, and stopped the transfer server.
- Compose API logs then recorded repeated Edge HELLO requests with HTTP 200;
  the native Edge client is now reaching Central through the official gateway.
- This proves native Edge mTLS HELLO connectivity in the lab. Task dispatch,
  heartbeat-specific evidence, and production-approved PKI remain open.

### Gateway denial metrics correction - 2026-09-05

- Gateway metrics after the native Edge restart showed continued certificate
  denials and no corresponding authenticated native Edge HELLO evidence after
  the certificate replacement attempt.
- Local inspection confirms the intended runtime Edge certificate is not in
  the revocation registry, while the older Alpine certificate is revoked.
- The certificate transfer/restart step is therefore not accepted as complete;
  the native Edge process must be independently verified to load the intended
  non-revoked certificate before task dispatch.
- Fail-closed behavior is working: revoked Edge connections are denied at the
  gateway and no task was dispatched under uncertain identity state.

### Direct console access attempt - 2026-09-05

- Attempted to open ALPINE1 through the GNS3 VM console proxy for direct SSH
  validation. The selected proxy presented the GNS3 VM console UI rather than
  the Alpine shell; no reboot or configuration action was submitted.
- The probe was discarded after the mismatch was identified. Therefore no
  direct SSH login result is claimed from this attempt; operator-provided
  Alpine console output remains the authoritative network-path evidence.

### ALPINE1 to current R1 path validation - 2026-09-05

- Operator console evidence confirms Alpine reaches Central `172.21.0.1`.
- Operator console evidence confirms `192.168.1.1` responds through `eth1`.
- Operator console evidence confirms R1 TCP/22 is open and identifies as
  `Cisco-1.25` over SSH.
- The customer-LAN path is therefore PASS. Remaining proof is the pinned RSA
  host key and authenticated read-only SSH command; no device secret is
  recorded here.

### Dynamic revocation gateway live harness - 2026-09-05

- Added `deploy/mtls/revocation_gateway.py`, which verifies the peer
  certificate, reloads durable revocation state per connection, strips client
  identity headers, injects verified identity, and proxies allowed HTTP to
  Central.
- Live result: a valid certificate reached Central with HTTP 200; after its
  fingerprint was registered while the gateway stayed running, the next
  connection closed before HTTP (`RemoteDisconnected`).
- Dynamic pre-HTTP enforcement is proven in the repository reference gateway.
  Production supervision/HA/limits/monitoring and explicit ZeroTier
  `ACCESS_DENIED` remain open, so `LIVE-PKI-OVERLAY` stays fail-closed.

### mTLS gateway container packaging - 2026-09-05

- Reused `backend/docker-compose.yml` and added a disabled `mtls` profile for
  the dynamic gateway; no parallel compose stack was created.
- Added `deploy/mtls/Dockerfile` with a non-root runtime, read-only PKI mount,
  durable revocation-state mount, and private upstream connection to the API.
- Updated the deployment runbook with mount and exposure requirements. The
  profile is not production evidence until built, started with approved PKI,
  and tested through a supervised deployment.

### mTLS gateway image validation - 2026-09-05

- Validated `backend/docker-compose.yml` with the `mtls` profile.
- Built the gateway image from `deploy/mtls/Dockerfile` successfully; the
  image uses a non-root UID and includes only the gateway plus Central service
  dependencies.
- Focused gateway/revocation tests passed: `3 passed`.
- The compose profile remains disabled by default and was not started as a
  production deployment because approved PKI mounts and supervised runtime
  evidence are still required.

### mTLS gateway container live validation - 2026-09-05

- Built gateway image was started as a disposable Docker container with lab
  PKI and the durable revocation-state volume.
- Valid Edge certificate reached Central through the container with HTTP 200.
- Fingerprint was revoked while the container stayed running; the next client
  connection was closed before HTTP without restarting the container.
- This proves the packaged dynamic reload behavior in the lab. Production
  supervisor health checks, limits, metrics, HA/shared-state behavior, and
  approved PKI remain required.
- Container and disposable certificate material were removed after the test.

### ALPINE2/R2 overlapping-subnet precheck - 2026-09-05

- Read the live GNS3 `TEST-EDGE` topology. `ALPINE2` is connected with
  `eth0` to `NAT2` and `eth1` to `Switch2`; `Switch2` connects to `IOSv2`.
- Read the ALPINE2 console directly. The current IPv4 output contains only
  loopback `127.0.0.1/8`; `eth0` and `eth1` have no IPv4 address and no route
  is configured.
- No ALPINE2 configuration was changed during this precheck.
- Required next lab preparation: configure ALPINE2 `eth0` with reachable
  Central/overlay-side connectivity and `eth1` with the second customer LAN
  address (planned `192.168.1.20/24`), then configure/verify R2 management at
  `192.168.1.1` before dispatching a second Edge task. This is a lab plan,
  not yet an overlap acceptance result.

### ALPINE2 persistent network configuration and reboot verification - 2026-09-05

- Configured ALPINE2 persistently in `/etc/network/interfaces`:
  `eth0` uses DHCP and `eth1` uses static `192.168.1.20/24`.
- Enabled the Alpine `networking` service in the default runlevel.
- Before reboot, ALPINE2 obtained `eth0=192.168.42.124/24`, retained
  `eth1=192.168.1.20/24`, and installed the expected default and LAN routes.
- Rebooted ALPINE2 and verified the configuration was restored automatically:
  `eth0=192.168.42.124/24`, `eth1=192.168.1.20/24`, default via
  `192.168.42.1`, and connected route `192.168.1.0/24`.
- ALPINE2 persistence is PASS in the lab. R2 management configuration and the
  two-Edge same-IP execution proof remain pending.

### R2 management and ALPINE2-to-R2 path verification - 2026-09-05

- Read R2 through its GNS3 console. `GigabitEthernet0/0` is already configured
  as `192.168.1.1`, status/protocol `up/up`, with method `NVRAM`.
- No R2 configuration change was required.
- From ALPINE2 using `eth1`, ping to `192.168.1.1` passed with 0% packet loss.
- From ALPINE2, TCP/22 on `192.168.1.1` is open.
- The second customer LAN path is therefore ready for Edge-2 enrollment and
  same-IP scoped execution testing. The full overlapping-subnet acceptance
  result remains pending until Edge-2 and Central inventory registration are
  complete.

### Edge-2 runtime readiness check - 2026-09-05

- ALPINE2 was checked after the persistent network configuration. The Alpine
  `networking` service is started, but no `/usr/local/bin/ainet-edge`,
  `/etc/ainet-edge`, or Edge OpenRC service is currently installed.
- Existing `tmp/m2-edges-pki/edge-b.crt` belongs to the older development CA,
  while the active compose gateway uses the current lab CA. It must not be
  reused because it would fail the active mTLS trust boundary.
- Edge-2 provisioning is therefore not yet executed. Next required action is
  to issue a fresh `edge-002` certificate from the active lab CA, prepare a
  separate protected keystore for R2, install the existing Go Edge binary,
  enable its OpenRC service, and verify HELLO/READY before dispatch.

### Native Edge dispatch root-cause resolution and M1 read proof - 2026-09-05

- Investigated the remaining `EDGE_DISPATCH_FAILED` result instead of
  weakening the routing or security checks.
- Found two Central API runtimes: the Edge mTLS gateway proxied to the Docker
  API, while host port `8000` was still served by a stale Windows Uvicorn
  process. Because M1 uses the in-memory Edge session registry, the task sent
  to the stale process could not see the Edge session created by Docker.
- Verified the stale process command line and stopped only that process. The
  Docker API then owned the task endpoint used for the test.
- Reused the canonical capability task endpoint with the existing inventory
  device `r1-native-edge001`, route `EDGE=edge-001`, and capability
  `device.read.facts`.
- Live result: task `task-m1-facts-20260905-central-docker` succeeded;
  TaskAttempt status `SUCCEEDED`; route `EDGE=edge-001`; Edge executed SSH
  locally toward R1 `192.168.1.1`; normalized facts returned hostname `R1`,
  vendor `cisco`, platform `ios`, and version `15.6(2)T`.
- This closes the functional M1 Central → native Alpine Edge → Cisco IOSv
  read-only execution path in the lab. The result is not production evidence:
  lab PKI, in-memory task/session state, single Edge, single API node, and
  remaining HA, durable persistence, credential lifecycle, overlap, and
  production licensing gates remain open.

### Edge-2 certificate preparation - 2026-09-05

- Generated a fresh lab-only `edge-002` certificate from the active CA into a
  separate temporary Edge-2 artifact directory.
- A temporary HTTP staging server was started for transfer planning and then
  stopped without sending artifacts to ALPINE2.
- No Edge-2 private key or device credential was logged. Edge-2 installation
  remains pending until its protected R2 keystore is prepared and transferred.

### Milestone 2 Redis session registry live validation - 2026-09-05

- Confirmed Docker Redis container `ainet-redis` is running and reachable from
  the API container; a read-only Redis `PING` returned successfully.
- Switched backend configuration from the M1 in-memory session registry to
  Redis using the Docker-host reachable Redis endpoint and recreated only the
  API service. Memory mode remains available for isolated unit tests.
- Edge-2 reconnected after API recreation and Central accepted its new
  session/READY flow. A stale pre-restart heartbeat was correctly rejected,
  demonstrating session invalidation rather than silent acceptance.
- Live task `task-m2-redis-edge002-20260905` succeeded through the Redis-backed
  registry: route `EDGE=edge-002`, capability `device.read.facts`, normalized
  result `R2/cisco/ios/15.6(2)T`.
- Redis-backed session/task queue is therefore PASS for this single-node lab
  slice. Multi-node HA, durable task/lease storage, Redis authentication/TLS,
  failure recovery, and production operational evidence remain open.

### Milestone 2 reliability contract tests - 2026-09-05

- Ran the existing lease, Edge control, retry policy, and retry API suites:
  `28 passed`.
- Ran the opt-in live Redis session lifecycle test against the active local
  Redis service: `1 passed`.
- The existing implementation already covers the tested lease/heartbeat,
  retry-class, and Redis lifecycle contracts; no parallel subsystem or source
  patch was required in this step.
- Duplicate delivery/idempotency live evidence and durable PostgreSQL lease
  evidence remain pending.

### Live idempotency duplicate-delivery hardening - 2026-09-05

- Live test before the patch exposed an unhandled duplicate idempotency key as
  HTTP 500; this was treated as a reliability defect.
- Extended both memory and PostgreSQL TaskAttempt stores with lookup by
  `idempotency_key`.
- Extended the canonical capability endpoint to return the existing task and
  attempt with `duplicate=true` when the key matches the same device,
  capability, Edge, execution location, and fingerprint.
- Reuse of a key for a different operation is rejected with HTTP 409.
- Unit regression suites remained green: `24 passed` for lease/control/retry
  coverage.
- Live verification after API rebuild: first read-only request returned 200 and
  executed once; second request returned 200 with `duplicate=true` and the same
  attempt ID; conflicting reuse returned 409. No second device execution was
  performed.
- Idempotency duplicate handling is PASS for the current live Redis/session
  slice. Durable PostgreSQL TaskAttempt execution and concurrent cross-node
  race evidence remain pending.

### PostgreSQL durable TaskAttempt preflight - 2026-09-05

- PostgreSQL was detected listening on local TCP port `5432`.
- Existing migration `backend/migrations/001_task_attempts.sql`, asyncpg
  adapter, and live test suite were inspected and reused.
- Connection attempts with default local DSN candidates were rejected by
  PostgreSQL authentication. No password was guessed, displayed, or logged.
- Durable PostgreSQL activation and live migration/concurrency/restore tests
  are blocked pending an operator-provided valid `POSTGRES_DSN` in the runtime
  environment. Redis and current Edge services remain unaffected.

### PostgreSQL DSN follow-up check - 2026-09-05

- `backend/.env` now contains `TASK_ATTEMPT_BACKEND=postgres` and a
  `POSTGRES_DSN` entry, but the non-secret DSN components show the placeholder
  database name `DATABASE`; connection testing fails with PostgreSQL
  `InvalidAuthorizationSpecificationError`.
- The running API container has not yet been recreated after this configuration
  change, so it is not yet using the requested Postgres backend.
- No credentials were printed or logged. Operator must replace placeholders
  with the actual database/user/password, then API recreation and live tests
  can proceed.

### Edge-2 native Alpine provisioning and overlap execution - 2026-09-05

- Generated a fresh `edge-002` client/server certificate from the active lab
  CA and prepared a separate protected keystore for the R2 credential and
  pinned RSA host key. Secret values were not printed or logged.
- Rebuilt the Go Edge binary explicitly for `linux/amd64` after detecting that
  the first staged artifact had been built for the wrong platform.
- Installed the binary, CA, `edge-002` certificate, key, keystore, and OpenRC
  service on ALPINE2. Enabled `ainet-edge` in the default runlevel; Edge-1 was
  not modified.
- Central recorded Edge-2 `HELLO 200` and `READY 200` through the active mTLS
  gateway. The initial binary format error was corrected and the final native
  service started successfully.
- Added inventory identity `r2-native-edge002` scoped to `cust-b/site-b`,
  `edge-002`, and management address `192.168.1.1`; the historical `b-r1`
  record was preserved unchanged.
- Live task `task-m3-overlap-edge002-20260905` succeeded with TaskAttempt
  `SUCCEEDED`, route `EDGE=edge-002`, capability `device.read.facts`, and
  normalized result hostname `R2`, vendor `cisco`, platform `ios`, version
  `15.6(2)T`.
- This proves the second side of the lab overlapping-subnet path:
  Central -> Edge-2/ALPINE2 -> R2 at `192.168.1.1`. Combined with the earlier
  Edge-1/R1 proof, M3 lab functional overlap is now verified. Production
  readiness remains closed because lab PKI, in-memory task state, single-node
  Central, and other production gates are still outstanding.

### PostgreSQL database creation, schema parity, and live Edge dispatch - 2026-09-05

- Operator requested Central to create the application database and update the
  project environment. A database named `ainet_agent` was created on the
  existing local PostgreSQL service; the existing password was preserved and
  never written to this log.
- Applied `backend/migrations/001_task_attempts.sql` and verified the
  `task_attempts` table exists. Updated `backend/.env` from the placeholder
  database path to `ainet_agent`, preserving the secret value without printing
  it. Container introspection confirmed `TASK_ATTEMPT_BACKEND=postgres` and
  `EDGE_SESSION_BACKEND=redis`.
- Live PostgreSQL lease tests passed: `2 passed` for atomic single-owner claim,
  renewal, and expired-attempt fencing. The PostgreSQL adapter compatibility
  tests also passed.
- The first PostgreSQL-backed Edge dispatch exposed a schema parity gap:
  `credential_ref` was not persisted, so the fail-closed execution gate
  correctly rejected the attempt. Extended the migration and PostgreSQL
  adapter with `credential_ref`; applied the additive database change and
  rebuilt the API container.
- Focused regression result after the fix: `13 passed, 2 skipped`.
- Live proof after the fix: Central API task succeeded through
  PostgreSQL-backed TaskAttempt state -> Redis session -> native Edge-2 on
  ALPINE2 -> R2 at `192.168.1.1`; normalized facts returned hostname `R2`,
  vendor `cisco`, platform `ios`, version `15.6(2)T`. The result was recorded
  as `SUCCEEDED` with `credential_ref` retained only as a reference.
- One earlier live request timed out and was fenced as `EDGE_DISPATCH_FAILED`;
  subsequent Edge debug inspection showed SSH execution succeeding. This was
  treated as transient dispatch evidence and not as a production pass.
- Restore-drill evidence, multi-node PostgreSQL concurrency, and full
  production database backup/restore remain outstanding. No application
  password, token, certificate, private key, or device secret was logged.

### PostgreSQL backup/restore drill - 2026-09-05

- Executed an isolated PostgreSQL backup/restore drill using the existing
  Windows PostgreSQL installation: custom-format `pg_dump`, temporary restore
  database, `pg_restore --exit-on-error`, and SQL validation.
- The restored database contained the `task_attempts` table and three restored
  TaskAttempt rows. The temporary database and dump artifact were removed after
  validation.
- Result: `backup_restore=PASS`, `restore_cleanup=PASS`.
- Durable evidence: `docs/evidence/m5-scale-ha/postgres-restore-drill-20260905.json`.
- Combined with the live atomic claim/renewal/expiry test (`2 passed`),
  DB-ATTEMPT-001 is now VERIFIED. Full controller/PKI/application disaster
  recovery remains a separate DR-001 gate.

### Executable production gate recheck - 2026-09-05

- Ran the V5 fail-closed gate using
  `.agents/skills/ainet-zerotier-platform/scripts/production_gate.py`.
- The initial PostgreSQL gate failed because the gate process started at the
  repository root while `POSTGRES_DSN` is intentionally stored only in
  `backend/.env`; no secret was copied into the root environment or report.
- Added `tools/run_live_postgres_gate.py` to load the backend-local DSN in
  process memory, normalize only the host for the Windows-local test, and run
  `backend/tests/test_postgres_live.py`. The gate recheck then passed
  `LIVE-POSTGRES`, along with `UNIT-PYTHON`, `LIVE-REDIS`, and
  `LIVE-GNS3-OVERLAP`.
- Current production gate report:
  `docs/evidence/production-gates/production-gate-20260905-230722.json`.
- The remaining functional gate failure is `LIVE-PKI-OVERLAY`; its validator
  correctly requires observed client denial after overlay deauthorization and
  production TLS-terminator rejection after certificate revocation.
- Release metadata (`version`, exact git commit, licensing decision) is still
  deliberately unconfigured, so the overall result remains `FAIL` as required.
- No application source runtime behavior was changed in this step beyond the
  gate wiring; no credentials, tokens, certificates, or private keys were
  logged.

### PKI/ZeroTier evidence recheck - 2026-09-05

- Ran `tools/validate_pki_overlay_evidence.py` and the executable production
  gate after the PostgreSQL work.
- The controller evidence records a successful private ZeroTier test:
  deauthorization produced client `ACCESS_DENIED`, removed the assigned
  overlay IP, and authorization was restored afterward. Central application
  certificate revocation and active-session disconnect are also recorded.
- The validator correctly fails only `tls_terminator`: current evidence is
  `PASS_LAB_COMPOSE`/dynamic gateway harness, not a repeatable production
  terminator deployment result. The disposable Nginx test observed an HTTP
  response instead of rejecting the revoked certificate before HTTP.
- Updated the PKI evidence README to reflect the actual state; no evidence
  values were promoted manually and no security gate was weakened.
- Latest production gate: `UNIT-PYTHON`, `LIVE-REDIS`, `LIVE-POSTGRES`, and
  `LIVE-GNS3-OVERLAP` pass; `LIVE-PKI-OVERLAY` remains fail-closed. Release
  metadata is also intentionally unconfigured.

### TLS terminator blocker confirmation - 2026-09-05

- Inspected the active `backend/docker-compose.yml` mTLS gateway and the
  reference `deploy/mtls/nginx.conf.example`.
- The active Python gateway has lab evidence for dynamic pre-HTTP connection
  closure, but the evidence is explicitly `PASS_LAB_COMPOSE`, not a production
  deployment result. The Nginx CRL harness previously forwarded a revoked
  client request (`HTTP_REACHED_400`), so it cannot be promoted.
- Re-ran `tools/validate_pki_overlay_evidence.py`: result
  `PKI_OVERLAY_EVIDENCE=FAIL incomplete:tls_terminator`.
- No gateway configuration or evidence status was weakened. The exact next
  acceptance requirement is a supervised production-equivalent TLS
  terminator test that rejects a revoked client before forwarding HTTP, with
  repeatable command output and redacted evidence.

### Repeatable Nginx CRL terminator test - 2026-09-05

- Added `tools/test_nginx_tls_revocation.py`, a disposable Docker Nginx test
  using the existing lab CA, a valid client certificate, a revoked client
  certificate, and an in-memory generated CRL. Temporary certificates,
  container, and files are cleaned up automatically.
- The valid client reached the API through Nginx and received `HTTP/1.1 200
  OK`, proving the test path and proxy are active.
- The revoked client was still accepted, producing
  `nginx_tls_revocation=FAIL`. This is recorded as a negative result; no
  production evidence was promoted and the gate remains fail-closed.
- The tested directives match the official Nginx model where `ssl_crl` is a
  PEM CRL used to verify client certificates. The remaining investigation is
  why this Nginx/OpenSSL runtime does not enforce the generated CRL.

### Nginx CRL test correction and lab PASS - 2026-09-05

- Diagnosis showed Nginx/OpenSSL logged `certificate revoked` and returned
  `HTTP 400` while reading request headers; the earlier test incorrectly
  treated any successful TLS socket as acceptance.
- Corrected `tools/test_nginx_tls_revocation.py` to use an upstream sentinel.
  The valid client returned `HTTP 200`, the revoked client returned
  `HTTP 400 Bad Request`, and the upstream recorded exactly one request.
- Result: `nginx_tls_revocation=PASS` at disposable lab scope. This proves the
  revoked request is rejected before proxy forwarding, consistent with the
  official Nginx `ssl_crl` behavior, but it does not prove the approved
  production terminator deployment.
- Added the redacted lab result to the PKI evidence artifact. The production
  validator intentionally remains unchanged and still requires an explicit
  production terminator result.

### Explicit next-agent handoff - 2026-09-05

- Added `docs/HANDOFF_NEXT_AGENT.md` with the exact reading order, verified
  state, blockers, first next action, commands, safety rules, and evidence
  requirements.
- Corrected stale deployment-runbook statements for the verified two-Edge
  overlap proof and PostgreSQL restore drill.
- The next agent must start with an approved persistent production-equivalent
  TLS terminator. It must not promote disposable lab evidence or fill release
  and licensing metadata by assumption.

### CRL reload automation - 2026-09-05

- Added `deploy/mtls/nginx_crl_reload.py` as the minimal deployment helper for
  Nginx CRL rotation. It validates that the PEM CRL is parseable, has an issuer,
  and is not expired; then runs `nginx -t` and reloads only when the CRL hash
  changes. Invalid/expired CRLs fail without reload.
- Added unit coverage for expired-CRL fail-closed behavior and idempotent
  reload behavior. Result: `4 passed` across CRL reload and gateway tests.
- Updated the deployment runbook with the operator command and safety order.
- This is implementation support, not production evidence: the actual
  production supervisor must invoke the helper after the approved revocation
  authority publishes a CRL. `LIVE-PKI-OVERLAY` therefore remains blocked.

### CRL/Nginx validation rerun - 2026-09-05

- Unit and gateway regression tests: `4 passed`.
- Docker Nginx end-to-end test: valid client returned `HTTP 200`; revoked
  client returned `HTTP 400 Bad Request`; upstream hit count remained `1`.
  Result: `nginx_tls_revocation=PASS` for the disposable lab deployment.
- Re-ran the executable production gate. `LIVE-POSTGRES`, `LIVE-REDIS`,
  `LIVE-GNS3-OVERLAP`, and unit gates pass; `LIVE-PKI-OVERLAY` remains fail
  closed because the evidence artifact still distinguishes lab Nginx from the
  approved production terminator. Release metadata is also unconfigured.

### Persistent Nginx staging deployment scaffold - 2026-09-05

- Added `deploy/mtls/nginx-staging.conf` with TLS 1.2/1.3, client CA
  verification, `ssl_crl`, trusted CA, certificate-depth validation, and
  sanitized proxy headers.
- Added `deploy/mtls/nginx.Dockerfile` and a disabled `nginx-staging` Compose
  profile on host port `9444`. The active Python mTLS gateway on `8443` was not
  changed or restarted.
- The staging profile requires an externally supplied `runtime/mtls/ca.crl`
  and remains disabled by default; no CA private key or certificate secret was
  added to the repository.
- Validation: `docker compose config --quiet` PASS and Nginx staging image
  build PASS. Runtime startup was intentionally not performed because the
  approved CRL/production PKI volume is not available.
- Updated the deployment runbook with the exact profile command and
  preconditions. Production gate remains fail-closed until this profile or an
  approved equivalent is deployed persistently and produces redacted revoke
  evidence.

### Nginx staging startup validation - 2026-09-05

- Generated a short-lived empty CRL signed by the lab CA using
  `tools/generate_lab_crl.py --acknowledge-lab-only`; this is a staging-only
  artifact and not production PKI.
- Started the persistent `nginx-staging` Compose profile on port `9444`.
  Container status is running and `nginx -t` reports syntax/configuration
  success.
- A curl smoke test with the currently available lab certificate bundle
  returned client-side exit `58` before a request was sent, indicating the
  local certificate/private-key pair is not usable by that curl invocation.
  This is recorded as NOT PASS for client handshake and does not alter the
  earlier Python disposable Nginx CRL result.
- The active production gateway on port `8443` was not changed. The next
  valid smoke test must use a verified matching client certificate/key pair;
  production PKI evidence remains blocked.

### Persistent Nginx staging CRL test - 2026-09-06

- Verified the matching lab certificate/key pair with Python SSL and connected
  successfully to persistent `nginx-staging` on port `9444` (`HTTP 200`).
- Generated a lab CRL revoking that certificate, reloaded Nginx, and repeated
  the request. Nginx returned `HTTP 400 Bad Request`, proving the revoked
  client was rejected after CRL reload.
- Restored the lab CRL to an empty CRL, reloaded Nginx, and verified the valid
  client returned to `HTTP 200`. The active gateway on port `8443` was not
  changed.
- Added redacted evidence at
  `docs/evidence/pki-overlay/nginx-staging-live-20260906.json`.
- This is persistent staging evidence, not production evidence; the approved
  production PKI/terminator target and release metadata are still required.

### Licensing and release-readiness assessment - 2026-09-06

- Read the V5 licensing guardrail and upstream-reference instructions before
  making release metadata changes.
- Reviewed current official upstream material for ZeroTierOne, Redis and
  PostgreSQL. The evidence confirms that ZeroTier core and the controller/
  nonfree portions must be tracked separately. Redis licensing is version
  sensitive, so the runtime version must be pinned before a commercial
  decision is made.
- Added `docs/licensing-matrix.md` with component role, version/pin status,
  license status, redistribution concerns, official sources, and required
  release actions. No secret, token, certificate, or private key was written.
- Updated `LIC-001` in `docs/traceability/requirements-matrix.md` from
  `PLANNED` to `IMPLEMENTED_UNVERIFIED`. This is not a production approval.
- Left `release.version`, `release.git_commit`, and
  `release.licensing_decision` as `<CONFIGURE>` in the production gate because
  no operator/legal approval or immutable release identity has been supplied.
- Security implication: unpinned or source-available components can create
  unreviewed redistribution obligations and make the production artifact
  non-reproducible; the fail-closed gate remains required.
- Licensing implication: self-hosted deployment does not imply free
  commercial redistribution. Exact build flags, image digests, SBOM, notices,
  and approval references remain outstanding.
- Commands executed: repository `rg`/`Get-Content` inspection of licensing,
  traceability, compose and dependency metadata; official-source web review.
- Tests: no application code changed; no runtime test was required for this
  documentation-only assessment.
- Remaining work: operator selects release version/commit, pins component
  versions/digests, generates SBOM/notices, obtains licensing decisions, and
  supplies the approved production PKI terminator evidence.
- Next-session handoff: read `docs/HANDOFF_NEXT_AGENT.md` and
  `docs/licensing-matrix.md`; do not change the gate licensing field by
  assumption. The next executable work should be release pin/SBOM preparation
  or the approved production-equivalent PKI terminator, depending on operator
  authorization.

### Release-readiness verification - 2026-09-06

- `git diff --check` for the licensing matrix, traceability matrix, and session
  log: PASS.
- `python tools/validate_pki_overlay_evidence.py`: FAIL closed with
  `incomplete:tls_terminator`. This is expected because the current artifact
  is still lab/staging scope and does not claim the approved production
  terminator.
- Executed the production gate. Report:
  `docs/evidence/production-gates/production-gate-20260906-023506.json`.
  The required Redis, PostgreSQL, GNS3 overlap and unit checks passed; the
  overall gate remains FAIL because release version/commit/licensing metadata
  are unconfigured and `LIVE-PKI-OVERLAY` is incomplete.
- No application source, runtime secret, certificate, private key, or device
  credential was changed by this release-readiness work.

### Local image digest inventory - 2026-09-06

- Read-only Docker metadata inspection confirmed the active local Redis image
  is `redis:7-alpine`; local digests for Redis, Nginx base, API, mTLS gateway,
  and Nginx staging were recorded in
  `docs/evidence/release-readiness/image-digests-20260906.json`.
- The artifact is explicitly marked `LOCAL_DOCKER_LAB_OBSERVATION` and
  `production_ready: false`. Local `latest` image digests are not treated as
  signed release artifacts and do not alter the production gate.
- Security implication: immutable digest capture improves reproducibility, but
  provenance, signing, registry ownership, SBOM, and release approval are
  still missing.
- Licensing implication: the observed Redis 7 image requires exact minor
  version/license confirmation; the tag alone is insufficient for approval.
- Command executed: read-only `docker image ls --digests` and `docker ps`.
- No container was stopped, recreated, pulled, or modified by this inventory.
- Next step: choose an approved release pin, generate SBOM/license notices,
  and obtain the operator/legal decision before configuring gate metadata.

### Release manifest and runbook linkage - 2026-09-06

- Added `docs/production/release-manifest.template.json` as the single
  structured template for approved version, commit, image digests, Edge
  binary hash/signature, ZeroTier build/licensing reference, SBOM and test
  evidence.
- Linked the template and current lab digest inventory from the deployment
  runbook. The runbook now requires SBOM/notices and an approved licensing
  reference before production approval.
- Kept all placeholders fail-closed. No release version, commit, legal
  approval, signature, or SBOM was invented or entered into the production
  gate.
- Validation: template JSON parsed successfully; no application runtime was
  changed and no container was restarted.

### SBOM readiness assessment - 2026-09-06

- Checked the host for `syft`, `trivy`, `cyclonedx`, and `pip-licenses`; no
  approved SBOM generator was detected.
- Reviewed `backend/requirements.txt`, `edge/go.mod`, and `edge/go.sum`.
  Go direct dependencies are versioned/checksummed, while the Central Python
  requirements remain partially unpinned and are not sufficient as an
  immutable release lock.
- Added `docs/evidence/release-readiness/sbom-gap-20260906.json` with the
  fail-closed findings and required actions. It is explicitly not a production
  SBOM and does not claim production readiness.
- No dependency, image, container, or application source was changed.
- Next step requires selecting/approving an SBOM tool and release dependency
  lock policy. Installing a tool or changing dependency versions should be
  done as a separately approved release-engineering action.

### Local CycloneDX SBOM generation - 2026-09-06

- Pulled the official `anchore/syft:latest` image after explicit operator
  authorization and ran read-only scans against the local API, mTLS gateway,
  and Nginx staging images.
- Generated CycloneDX JSON artifacts:
  `central-api-sbom-20260906.json`, `mtls-gateway-sbom-20260906.json`, and
  `nginx-staging-sbom-20260906.json` under
  `docs/evidence/release-readiness/`. SHA-256 hashes are recorded in
  `sbom-gap-20260906.json`.
- Central SBOM parsed successfully and contained 2932 components. The
  artifacts remain local-build evidence, not signed production SBOMs.
- Updated the SBOM gap artifact from generator-missing to
  `PARTIAL_LOCAL_SBOM`. Production blockers remain: pin Syft by digest, lock
  Python dependencies, establish image provenance/signing, and complete
  release/license approval.
- Docker applications were not stopped or modified; only the Syft utility
  image was pulled and short-lived read-only scanner containers were run.

### Python candidate lockfile - 2026-09-06

- Read `pip freeze` from the local `backend-api:latest` image and added
  `backend/requirements.lock.txt` with exact package versions.
- Corrected package-name normalization to match the image output and verified
  the lockfile has no differences from the image's `pip freeze` output:
  `LOCK_MATCHES_IMAGE_FREEZE`.
- Updated the SBOM gap evidence to `CANDIDATE_LOCK_CREATED`. This lockfile is
  not yet the production lock: hashes, package-index policy, clean rebuild,
  vulnerability/license review, and signed artifact provenance remain
  required.
- No active container was modified or restarted. The lockfile is a release
  candidate only; the unpinned `backend/requirements.txt` remains unchanged
  to preserve current development behavior.

### Clean Central release-candidate build definition - 2026-09-06

- Added `backend/Dockerfile.release`, which installs only
  `backend/requirements.lock.txt` for a clean release-candidate build.
- The base image remains intentionally unpinned in this candidate definition;
  production must replace it with an approved immutable digest after registry
  and provenance review.
- The existing `backend/Dockerfile` and active API image are unchanged.
- Next command is an isolated Docker build tagged as a local release
  candidate, followed by a package-freeze comparison and smoke tests.

### Clean Central candidate build verification - 2026-09-06

- Built isolated image `ainet-api:release-candidate-20260906` from
  `backend/Dockerfile.release`.
- Build succeeded using the candidate lockfile. Image digest:
  `sha256:04caaf95e7be7748f5db84aa21d20670e907a32b596879d4dcdd3406438459c9`.
- Smoke imports for FastAPI, asyncpg, Redis and Netmiko passed:
  `CENTRAL_IMPORT_SMOKE=PASS`.
- Candidate `pip freeze` matched `backend/requirements.lock.txt`:
  `CANDIDATE_LOCK_MATCHES`.
- Generated and parsed candidate CycloneDX SBOM with 2932 components at
  `docs/evidence/release-readiness/central-api-release-candidate-sbom-20260906.json`.
  Hash is recorded in `sbom-gap-20260906.json`.
- Active API, gateway, staging Nginx, Redis, PostgreSQL, and Edge runtimes
  were not replaced or restarted. This is still a local candidate, not a
  signed or approved production release.
- Remaining work: pin the Python base image by approved digest, add package
  hashes/index policy, scan vulnerabilities/licenses, produce Edge SBOM, and
  obtain release approval.

### Python base image digest pin - 2026-09-06

- Updated `backend/Dockerfile.release` to pin `python:3.12-slim` to the
  digest observed during the clean candidate build:
  `sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`.
- This is a reproducibility improvement for the local candidate. Registry
  provenance, signature verification, and production approval remain open.
- Active Docker Compose Dockerfiles and running containers were not changed.
- Next step: rebuild this digest-pinned candidate and confirm the digest and
  smoke tests remain stable.

### Digest-pinned Central candidate verification - 2026-09-06

- Rebuilt `ainet-api:release-candidate-20260906-pinned` with
  `--pull=false`; the build reused the explicitly pinned Python base digest.
- Candidate image digest:
  `sha256:2a96f0b48b5c5005935f63cf906a691ec0e5ab1fd61c976ab3ad07160dc14fb0`.
- Pinned candidate import smoke test passed:
  `PINNED_CENTRAL_IMPORT_SMOKE=PASS`.
- `git diff --check` passed for the changed release evidence and Dockerfile.
- No active Compose service was replaced, restarted, or reconfigured.
- Remaining blockers: package hashes, vulnerability/license scan, Edge SBOM,
  image signature/provenance, approved production PKI terminator, and release
  approval metadata.

### Central candidate vulnerability/license scan - 2026-09-06

- Pulled `aquasec/trivy:latest` and recorded its image digest in the SBOM
  evidence. Scanned `ainet-api:release-candidate-20260906-pinned` with
  vulnerability and license scanners, severity filter HIGH/CRITICAL,
  ignoring unfixed findings.
- JSON result is valid at
  `docs/evidence/release-readiness/central-api-trivy-20260906.json` with 3
  HIGH vulnerabilities and 319 license records.
- Findings are `CVE-2026-69247`, `CVE-2026-69249`, and
  `GHSA-537c-gmf6-5ccf`, all affecting `cryptography==46.0.7`; Trivy reported
  fixed versions 50.0.0, 49.0.0, and 48.0.1 respectively.
- Updated SBOM evidence to `VULNERABILITIES_FOUND` and
  `RELEASE_BLOCKED_PENDING_REMEDIATION`. Dependency upgrade was not performed
  automatically; it requires compatibility tests and a fresh scan.
- No active service or container was changed. The scan ran in a disposable
  read-only scanner container.

### Cryptography vulnerability remediation candidate - 2026-09-06

- Trivy findings were isolated to `cryptography==46.0.7`. A pip dry-run in the
  candidate image confirmed `cryptography==48.0.1` is installable with the
  current direct dependency set.
- Updated the Central dependency constraint to `cryptography>=48,<49` and the
  candidate lockfile to `48.0.1`. This changes source dependency policy but
  does not alter any running container.
- Next step is an isolated clean rebuild, smoke/import test, focused Central
  test suite, and a fresh Trivy scan. The change remains a release candidate
  until those checks pass.

### Cryptography second remediation candidate - 2026-09-06

- The 48.0.1 candidate still had two HIGH advisories. A dry-run confirmed
  `cryptography==50.0.0` is installable with the current dependency set.
- Advanced the candidate constraint to `cryptography>=50,<51` and lockfile to
  `50.0.0`. This remains a candidate and is not deployed to active services.
- Next step is to rebuild, run smoke/focused tests, and rescan before deciding
  whether this remediation can be retained.

### Cryptography remediation v2 verification - 2026-09-06

- Built `ainet-api:security-candidate-20260906-v2` with
  `cryptography==50.0.0`; image digest is
  `sha256:a0cadb2f1c2158109d609e0b72d723fae67afc37b6f0392199c910a7cc51739b`.
- Import smoke test passed and reported `cryptography=50.0.0`.
- Trivy HIGH/CRITICAL scan passed with zero vulnerabilities and 319 license
  records. Evidence is `central-api-trivy-security-candidate-v2-20260906.json`.
- Generated and parsed the v2 CycloneDX SBOM with 2932 components at
  `central-api-security-candidate-v2-sbom-20260906.json`; SHA-256 is recorded
  in the evidence artifact.
- Updated SBOM status to `SECURITY_SCAN_PASS_CANDIDATE`. This applies only to
  the scanned local candidate and selected severity scope; it is not a final
  production approval.
- Active Compose services and Edge runtimes were not changed or restarted.

### Edge dependency remediation and SBOM v3 - 2026-09-06

- Initial Edge scan found 35 HIGH/CRITICAL findings caused by Go stdlib
  `1.21.13` and `golang.org/x/crypto v0.31.0`.
- Upgraded Edge module metadata to Go `1.26.6`, `golang.org/x/crypto v0.55.0`,
  and `golang.org/x/sys v0.47.0`. `go mod tidy` completed and
  `go test -race ./...` passed for all Edge packages.
- Rebuilt `ainet-edge:security-candidate-20260906-v3`; image digest is
  `sha256:f365718a5b37b2dd8a61e72182d1b841127124518dc0fc1d5b4f9b11d1021b85`.
- Trivy HIGH/CRITICAL scan passed with zero vulnerabilities and 8 license
  records. Evidence: `edge-trivy-security-candidate-v3-20260906.json`.
- Generated and parsed Edge CycloneDX SBOM with 96 components at
  `edge-security-candidate-v3-sbom-20260906.json`; hash is recorded in
  `sbom-gap-20260906.json`.
- Updated the aggregate readiness status to
  `CENTRAL_EDGE_SECURITY_SCAN_PASS_CANDIDATES`. This is candidate evidence
  only; image signing/provenance, production base-image policy, license
  approval, and PKI production evidence remain open.
- No native Edge, Docker Compose service, customer device, or credential was
  modified or restarted.

### Edge v3 scan evidence and signing gap - 2026-09-06

- Edge v3 SBOM parsed with 96 components and Trivy reported zero HIGH/CRITICAL
  vulnerabilities with 8 license records.
- Current rebuilt Edge binary SHA-256 is
  `337FD8ED97D0131E4C7C216903873D5F0400C1FC4D2EB221299ED7B925F89922`;
  the image digest and scan hashes are recorded in
  `docs/evidence/release-readiness/sbom-gap-20260906.json`.
- The artifact remains `LOCAL_UNSIGNED_CANDIDATE`. No Cosign signature was
  fabricated: official Sigstore guidance requires an OCI registry for normal
  container signing/verification, while this candidate exists only in the
  local Docker daemon.
- Production blocker remains: approved registry, signing identity/keyless
  policy, signature bundle/attestation, and verification evidence are needed.

### Signing and attestation policy scaffold - 2026-09-06

- Inspected repository configuration for registry, Cosign, Sigstore, Rekor and
  release-signature settings; no approved registry or signing identity is
  configured.
- Added `docs/production/image-signing-policy.md` with immutable digest,
  signature, identity, attestation, SBOM and fail-closed deployment rules.
- Linked the policy from the deployment runbook. No key, certificate,
  signature, token, or external deployment was created.
- Official Sigstore guidance was reviewed; normal container signing requires
  an OCI registry, which the current local-only candidates do not have.
- Next step requires an operator-approved OCI registry and signing identity or
  keyless CI policy. Until then, release signing remains NOT_READY.

### Full regression after security upgrades - 2026-09-06

- Go Edge full race suite: PASS for all packages.
- First Python full-suite run reported `118 passed, 3 skipped, 1 error`; the
  only error was Windows `WinError 5` while pytest tried to create its system
  temp directory. No test assertion failed.
- Re-ran the same suite with workspace-local
  `--basetemp=tmp/pytest-full-20260906`: `119 passed, 3 skipped in 3.18s`.
- This confirms the Central security dependency upgrade and Edge toolchain
  upgrade do not regress the existing Python/Go test suites under the
  repository-supported test setup.
- The workspace-local pytest temp directory is test output only; no runtime
  service, Edge node, customer device, or credential changed.

### Executable SBOM/signing release gate - 2026-09-06

- Added `tools/validate_release_evidence.py`, a fail-closed validator for
  Central/Edge scan status, SBOM artifact presence, signed Edge artifact state,
  release metadata, image digest, SBOM hash, and production approval.
- Added required gate `RELEASE-SBOM-SIGNING` to
  `docs/production/production-gate.json`.
- The validator intentionally fails under current state because the Edge
  artifact is unsigned and release manifest fields remain placeholders. This
  prevents documentation-only evidence from being mistaken for production
  approval.
- No runtime service or artifact was replaced; only validator/gate contract
  and documentation were added.

### Full production gate recheck - 2026-09-06

- Executed the complete production gate after adding
  `RELEASE-SBOM-SIGNING`.
- Report: `docs/evidence/production-gates/production-gate-20260906-030931.json`.
- Passing gates: `UNIT-PYTHON`, `LIVE-REDIS`, `LIVE-POSTGRES`, and
  `LIVE-GNS3-OVERLAP`.
- Failing gates: `LIVE-PKI-OVERLAY` because production TLS terminator evidence
  is incomplete, and `RELEASE-SBOM-SIGNING` because signing/release approval
  metadata is absent. The global release fields are also unconfigured.
- This confirms the gate is fail-closed and reflects the current evidence;
  no result was manually promoted to PASS.

### Release signing operational runbook - 2026-09-06

- Added `docs/runbooks/release-signing-runbook.md` with the operator inputs,
  registry/digest/sign/attest/verify sequence, secret-handling rules, and
  exact evidence required by the release gate.
- Linked the runbook from the deployment runbook.
- No registry login, token, key, signature, attestation, or external push was
  attempted because no approved registry or signing identity is configured.
- Production status remains FAIL by design until the operator supplies those
  external release controls.

### GitHub GHCR/Cosign workflow scaffold - 2026-09-06

- Added manual-only `.github/workflows/release-sign.yml` using GHCR,
  `GITHUB_TOKEN`, GitHub OIDC, Cosign, and CycloneDX SBOM attestation.
- Added `docs/production/github-ghcr-release.md` with setup, dispatch,
  identity-verification, and evidence instructions; linked it from the
  signing runbook.
- The workflow is intentionally not triggered automatically and has not been
  executed because no approved release tag/GHCR publication decision exists.
- No registry credential, private key, OIDC token, device secret, or image was
  pushed by this session.
- Remaining work: operator enables GHCR package writes, approves the release
  commit/tag, reviews action pinning, runs the workflow, and supplies the
  resulting digest/signature/attestation evidence to the production gate.
- Added the Cosign installer step to the workflow; action versions are still
  tags and must be SHA-pinned during release hardening before production use.

### Remote/worktree scope safety check - 2026-09-06

- Read-only remote inspection confirmed `origin/main` currently contains only
  the older service layout; `edge/` and the V5 Edge/service implementation are
  not present in the remote tree.
- The local worktree contains many unrelated modifications/deletions and
  untracked V5 files. A workflow-only push would be incomplete, while pushing
  the entire worktree could publish unrelated operator changes.
- No files were staged, committed, or pushed after this discovery. The scope
  must be selected explicitly before external repository mutation.

### GitHub remote readiness check - 2026-09-06

- Repository remote is configured as `https://github.com/AntLink/ai-network-agent.git`
  on branch `main`.
- GitHub CLI/authentication was not available in the current Windows
  environment, so workflow dispatch or push was not attempted.
- No external repository state was changed. The workflow remains local until
  the operator pushes the reviewed files and confirms GitHub Actions package
  permissions/OIDC policy.

### Git CLI connectivity retest - 2026-09-06

- Git CLI is available: `git version 2.45.1.windows.1`.
- Read-only `git ls-remote --heads origin main` succeeded and returned remote
  main commit `3a4856a2f2700aa4df3285608292e33bedda2e62`.
- This confirms Git remote connectivity; it does not establish permission to
  push or dispatch Actions. No external repository state was changed.

### Candidate regression test result - 2026-09-06

- First focused test invocation without `PYTHONPATH=backend` failed during
  collection with `ModuleNotFoundError: No module named 'app'`; this was a
  command-environment error, not a dependency regression.
- Re-ran with the repository-required `PYTHONPATH=backend` setting. Result:
  `16 passed in 3.36s` for overlay provider, Edge control, and Edge identity
  contract tests.
- The failed invocation and corrected command are both recorded for handoff
  clarity. No source/runtime secret was exposed.

### Branch release-prep publication - 2026-09-06

- Operator selected option 2: publish the reviewed V5 release-preparation work
  to a separate branch, preserving `main`.
- Created local branch `v5-release-prep`.
- Committed the selected Central/Edge implementation, tests, release workflow,
  deployment/security documentation, evidence, traceability, and related
  frontend changes in commit `df059e5` (`Prepare V5 release and GitHub signing workflow`).
- Pushed the commit successfully to `origin/v5-release-prep`.
- Pull request entry point:
  `https://github.com/AntLink/ai-network-agent/pull/new/v5-release-prep`
- Unrelated worktree changes, runtime logs, caches, environment files, and
  pre-existing deletions were not included in that commit.
- Production gate remains fail-closed/not ready: release approval metadata,
  signed release artifacts, production PKI/overlay evidence, and the first
  controlled GitHub Actions signing run are still required.
- Security/licensing: no credentials, tokens, private keys, or device secrets
  were written to this session log or pushed by this operation.
- Next handoff: review the branch diff and workflow, configure GHCR/OIDC and
  signing policy, run the workflow with an approved tag, then update the
  release manifest and production-gate evidence only after verification.

### Release workflow hardening - 2026-09-06

- Corrected the GitHub release workflow to checkout the operator-supplied
  immutable `release_tag` with full history before building artifacts.
- Added Edge SBOM generation and extended Cosign signing, verification, and
  CycloneDX attestation to both Central and Edge images.
- Extended the uploaded release evidence artifact to include both SBOM files.
- Updated `docs/production/github-ghcr-release.md`; combined signed release
  manifest publication remains a production approval requirement.
- Validation: workflow YAML parse passed and `git diff --check` passed.

### Immutable release tag guard - 2026-09-06

- Added fail-closed validation for the workflow input: only semantic version
  tags matching `vMAJOR.MINOR.PATCH` are accepted.
- The workflow now verifies the checked-out commit exactly matches the
  requested tag before building or publishing any image.
- Updated the operator release guide with this requirement.
- No release tag was created and no GitHub Actions run was started.

### Remote release-tag readiness check - 2026-09-06

- Confirmed `origin/v5-release-prep` is synchronized at commit `5553559`.
- No `v*` release tag currently exists on the remote repository.
- No tag was created automatically because release version and approval are
  production-significant operator decisions.
- Next operator action: approve a semantic release version, create the tag on
  the reviewed commit, then dispatch the manual GitHub signing workflow.

### Approved release tag publication - 2026-09-06

- Operator approved release version `v0.1.0`.
- Created and pushed annotated tag `v0.1.0` from branch `v5-release-prep`.
- Local tag dereferences to commit `c9da6b147d27001ce7a1fda7b886233589559637`.
- Remote tag publication was confirmed with `git ls-remote`.
- The GitHub signing workflow has not yet been dispatched; GHCR/OIDC and
  package-write settings still need operator verification.

### GitHub workflow checkout failure remediation - 2026-09-06

- Operator reported workflow failure with `/usr/bin/git` exit code 128 and
  Node.js 20 deprecation warnings.
- The workflow's release-tag guard was corrected to compare the resolved tag
  commit with the actual checked-out `HEAD`, rather than `GITHUB_SHA` from the
  workflow dispatch ref.
- The Node.js warning is non-fatal and is tracked separately for action SHA/
  runtime modernization.
- The fix requires merging the updated workflow to the default branch before
  rerunning the tag workflow; the immutable `v0.1.0` tag is not moved.
- No GitHub Actions run or production release was initiated; no credentials,
  signing keys, tokens, or device secrets were used or recorded.

### Release manifest evidence automation - 2026-09-06

- Added workflow generation of a per-run release manifest evidence artifact.
- The manifest records the immutable Central/Edge image references, SBOM
  hashes, Edge binary hash, workflow commit, and run reference.
- `approved_by`, licensing approval, and `production_ready` remain explicitly
  unconfigured/false; the workflow cannot make a release production-ready by
  itself.
- Validation: workflow YAML parse passed and `git diff --check` passed.
