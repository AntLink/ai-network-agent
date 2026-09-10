---
operator: Codex
milestone: Edge review and hardening
objective: Review every Edge Go source file with DeepSeek and ChatGPT, synthesize verified findings, and apply safe fixes.
repository_state: Existing worktree preserved; no reset or commit performed.

## Scope inspected
- All 25 non-test Go source files under edge/cmd and edge/internal.
- All 20 Edge Go test files and relevant callers for compatibility.
- Control, bundle, credentials, discovery, executor, security, SNMP, telemetry.

## REUSE / EXTEND / REFACTOR / CREATE
- REUSE: existing Edge packages, protocol, discovery, executor, transports, tests.
- EXTEND: facts SSH hardening, normalized vendor dispatch, Windows transport port invariant.
- REFACTOR: not performed; no parallel subsystem created.
- CREATE: none.

## Consultant review
- DeepSeek and ChatGPT received the same redacted source-only packets in small batches.
- Review covered control/bundle/signing/credentials, discovery, executor, security, SNMP, telemetry.
- Consultant suggestions were treated as untrusted input and checked against actual code/callers.

## Implemented files
- edge/internal/executor/facts.go: temporary pinned known_hosts, strict host key checking, explicit SSH port, sshpass environment mode instead of password argv, 1 MiB bounded output, debug file mode 0600.
- edge/internal/executor/normalized.go: explicit Cisco/MikroTik parser selection; unknown vendors no longer become Cisco.
- edge/internal/executor/windows_transport.go: coherent default WinRM port (TLS 5986, non-TLS 5985) when port is unspecified.

## Commands and results
- gofmt -w internal/executor/facts.go internal/executor/normalized.go internal/executor/windows_transport.go: PASS.
- go test ./...: PASS.
- go test -race ./...: PASS.

## Security implications
- SSH host-key verification and output bounds improved. Password is no longer passed as sshpass argv; it remains process environment because legacy IOS compatibility still uses sshpass.
- SNMPv2c, Telnet, serial plaintext limitations remain explicit follow-up items; no insecure silent migration was made.
- No credentials, tokens, keys, or customer secrets were logged.

## Traceability / requirements
- Relevant V5.3 invariants: capability execution, credential_ref, bounded protocol/outputs, transport separation, semantic normalization, session logging.
- Dedicated requirement rows should be linked when this slice is committed.

## Remaining work / handoff
- Add regression tests for unknown vendor, SSH argv absence and host-key mismatch, output cap, and WinRM port matrix.
- Confirm and then harden discovery scope normalization, stale session cleanup, journal I/O locking, and keystore file permission policy.
- Review complete Edge test coverage with go test -race before rebuilding/deploying binaries.
- No production-ready claim; production gate remains authoritative.

## Follow-up hardening
- Added explicit device_id to the Edge envelope and rejected command bundles whose attempt/device identity does not match the envelope (payload fallback retained for compatibility).
- Re-ran formatting and Edge regression tests after the control-boundary change.
- go test ./...: PASS. go test -race ./...: PASS (no race report).
- No commit/push or binary deployment performed in this session.

## Discovery hardening
- edge/internal/discovery/probe.go: added optional AllowedTargets scope enforcement, canonical IP normalization, duplicate suppression, normalized exclusions, explicit configuration errors, and per-probe timeout defaulting to 5 seconds.
- edge/internal/discovery/probe_test.go: added regression tests for invalid configuration, scope/duplicate handling, and timeout cancellation.
- Verification: go test ./... PASS; go test -race ./... PASS.
- Existing callers remain compatible because new options are optional and the function return type is unchanged.
- Remaining: wire Central-approved policy into AllowedTargets at the main discovery boundary, then add control session cleanup/journal I/O hardening.

## Central policy wiring
- Edge main.go now forwards optional Central-approved llowed_targets into discovery.RunBounded; canonical IP scope is enforced when present.
- Central task envelope now includes llowed_targets equal to the already policy-planned discovery targets for ARP/ICMP capabilities. Existing target planning remains the Central policy authority.
- Tests: Edge go test -race ./... PASS; Central 	ests/test_edge_contracts.py and 	ests/test_discovery_policy.py: 12 passed, 1 existing pytest cache warning.
- Note: the warning is local pytest cache directory contention, not a test failure.

## Session and journal reliability hardening
- edge/internal/control/server.go: stale sessions older than 5 minutes are cleaned during new handshakes.
- Journal results are copied under the session mutex and persisted after unlock; a dedicated journal mutex serializes atomic file writes. Existing package compatibility helper remains for tests.
- Verification: go test ./... PASS; go test -race ./... PASS.
- No credentials or secret material logged; no production deployment or commit/push performed.

## Regression coverage
- Added stale-session cleanup regression test and unknown-vendor normalization regression test.
- SSH regression initially exposed non-22 known_hosts formatting; fixed pinned host entry to use [host]:port for non-default ports.
- Verification: focused SSH/normalization tests PASS; go test ./... PASS; go test -race ./... PASS.
- No production deployment, commit, or push performed.

## Security regression evidence
- Added bounded-output regression test and pinned host-key mismatch regression test.
- The mismatch test uses a dedicated server helper so the expected rejected SSH handshake is not reported as an unrelated test failure.
- Verification: focused security tests PASS; go test ./... PASS; go test -race ./... PASS.
- No secrets, deployment, commit, or push performed.

## 2026-09-09 — Edge keystore transport validation and race fix

- Objective: continue the Edge reliability/security slice without exposing credentials.
- Reuse/extend decision: EXTEND existing `edge/internal/credentials.KeyStore`; preserve legacy `Resolve` behavior for SSH/console and add purpose-aware validation for SNMP.
- Changes:
  - Added `PurposeSSH`, `PurposeConsole`, and `PurposeSNMP` plus `ResolveFor`.
  - SNMP polling now validates `credential_ref` using the SNMP community field and permits community-only local entries.
  - SSH/console validation still requires a username.
  - Keystore errors do not echo credential values or references.
  - Fixed a race in SSH stdout/stderr capture by using independent bounded buffers; combined output behavior remains unchanged.
- Tests:
  - `go test ./...` — PASS.
  - `go test -race ./...` — PASS.
  - New coverage includes SNMP-only credentials, transport-specific validation, unsupported purpose, and error non-disclosure.
- Security: passwords, SNMP communities, and host keys remain Edge-local; no secrets were added to this log.
- Remaining work: validate live SNMP telemetry against the actual Edge devices and continue frontend/backend contract cleanup; do not claim production readiness from unit tests alone.
## 2026-09-09 — Live Edge detail no longer dispatches UI telemetry tasks

- Root cause: Edge detail automatically called `POST /api/v1/tasks/capability` for SNMP polling. This produced recurring 404s in stale/local backend deployments and exposed task-result JSON in the UI.
- Decision: REUSE the authenticated `/api/v1/discovery/live` stream; remove frontend task polling from Edge detail. The page now derives device presence and device rows from live Edge observations and retains only the bounded observation summary.
- Verification: `npm.cmd run build` — PASS. TypeScript compilation and Vite production build completed successfully.
- UX/security: removed the `Poll SNMP telemetry` action from Edge detail; no raw task/attempt JSON is rendered there. Credential-bearing task dispatch is no longer initiated by opening or refreshing an Edge detail page.
- Remaining limitation: CPU/memory values for managed devices require the Edge to publish device telemetry observations or a separate server-side telemetry projection. This change intentionally does not fabricate values when those observations are absent.
## 2026-09-09 — Safe recovery after telemetry scheduler wiring attempt

- A scheduler wiring attempt exposed a PowerShell newline/escape issue and temporarily truncated `edge/cmd/ainet-edge/main.go`.
- Recovery: restored the latest available local `tmp/pr-gate-worktree/edge/cmd/ainet-edge/main.go` snapshot, then restored normalizer compatibility with `NormalizeRouterOSFacts` alias. No secret or credential file was touched.
- Verification after recovery:
  - `go test ./...` — PASS.
  - `go test -race ./...` — PASS.
- Decision: do not claim live device telemetry scheduler complete yet. The next implementation should be isolated in a new package/file with focused tests before wiring it into `main.go`, then use an explicit target allowlist and Edge-local `credential_ref`.
## 2026-09-09 — Isolated device telemetry collector

- Added edge/internal/telemetry/device.go as an isolated collector package.
- Target policy: explicit IP allowlist, maximum 256 targets, duplicate rejection, required device_id and credential_ref, no unspecified/multicast targets.
- SNMP credentials resolve locally by purpose; observations intentionally omit credential_ref, community, password, and host key.
- Vendor profiles currently provide bounded OIDs for Cisco and MikroTik/RouterOS; unknown vendors receive no guessed OIDs.
- Added tests for target validation, OID selection, stable non-secret observation IDs.
- Verification:
  - go test ./internal/telemetry ./internal/credentials ./internal/snmp — PASS.
  - go test -race ./internal/telemetry — PASS.
  - go test ./... — PASS.
- Runtime wiring is intentionally pending until an explicit target-file contract is reviewed; this prevents accidental unrestricted SNMP scans and avoids another main.go regression.
## 2026-09-09 — Runtime wiring deferred after edit-tool safety failure

- The isolated telemetry package remains intact.
- Two attempts to edit the large legacy main.go via PowerShell replacement caused temporary file corruption; both were recovered from the local tmp/pr-gate-worktree snapshot.
- Final verification after recovery:
  - go test ./... — PASS.
  - go test -race ./... — PASS.
- Decision: defer runtime wiring until a patch-capable editor or a small dedicated entrypoint file can be used safely. No production binary update or live telemetry claim is made in this session.
## 2026-09-09 — Isolated telemetry runtime entrypoint

- Added edge/cmd/ainet-edge-telemetry/main.go.
- The worker uses the existing mTLS control client and heartbeat scheduler, reads an explicit Edge-local SNMP target allowlist, polls through the isolated telemetry collector, and submits only non-secret observations.
- Added edge/config/telemetry-targets.example.json as a non-secret configuration example; it contains no real credential or device secret.
- The existing ainet-edge main binary remains unchanged by this wiring.
- Verification:
  - go test ./... — PASS.
  - go test -race ./... — PASS.
  - go build ./cmd/ainet-edge ./cmd/ainet-edge-telemetry — PASS.
- Operational note: the telemetry worker is a separate process for this stage; it must be configured with the same Central URL, mTLS identity, customer/site scope, local keystore, and target file before live use.
## 2026-09-09 — Telemetry scheduler test hardening

- Added scheduler tests for valid target JSON, malformed/unscoped targets, and context cancellation.
- Runtime entrypoint remains isolated at edge/cmd/ainet-edge-telemetry; main Edge binary is unchanged.
- Verification:
  - go test ./internal/telemetry — PASS.
  - go test -race ./... — PASS.
  - go build ./cmd/ainet-edge ./cmd/ainet-edge-telemetry — PASS.
## 2026-09-09 — Telemetry worker operational runbook

- Added docs/runbooks/edge-telemetry-worker.md.
- Documented Edge-local target allowlist, keystore separation, mTLS startup, UDP/161 validation, live observation endpoint, and stale TTL verification.
- No password, community, certificate private key, or token was added to repository or session log.
## 2026-09-09 — Live telemetry readiness validation

- Repository check found only the non-secret telemetry target example; no real target or keystore was present in the workspace, so no live device polling was attempted.
- Backend test run initially hit a Windows pytest temp-directory permission issue; rerun with isolated basetemp succeeded.
- Verification: 26 backend tests passed, with one existing pytest cache warning.
- Live gate remains pending until an operator supplies/places the Edge-local target allowlist and confirms SNMP is enabled on the lab Cisco/MikroTik devices.
## 2026-09-09 — Telemetry worker cross-platform artifacts

- Built Windows amd64 telemetry worker: edge/dist/ainet-edge-telemetry-windows-amd64.exe
- Built Linux amd64 telemetry worker: edge/dist/ainet-edge-telemetry-linux-amd64
- SHA-256:
  - Windows: 83E08D47CA50E5206E91F211F704E6608CA6AF1FB26A6E1AA13FB94697EC029B
  - Linux: 13885E70263E3B0660BC4A9F6B4A1EB03F81AB834EEDC1E2054780818B8D86ED
- These are local build artifacts only; no live deployment or secret packaging was performed.
## 2026-09-09 — Telemetry worker service templates

- Added deploy/edge-telemetry/ainet-edge-telemetry.service for Linux systemd.
- Added deploy/edge-telemetry/install-windows.ps1 for a Windows startup Scheduled Task.
- Templates use placeholders for identity/scope and do not contain credentials, tokens, or private keys.
- Operational deployment remains pending until the real Edge target allowlist and local keystore are provisioned.
## 2026-09-09 — Telemetry traceability

- Added traceability row EDGE-TELEMETRY-001 for allowlisted Edge SNMP telemetry, local credential resolution, non-secret observations, and TTL behavior.
- Status remains IMPLEMENTED-UNVERIFIED because live Cisco/MikroTik evidence has not yet been collected.
## 2026-09-09 — Edge UI metric mapping

- Edge detail now maps CPU, memory, and latency from fresh SNMP observation attributes when present.
- Missing metrics remain 0/empty according to the existing table contract; the UI does not fabricate live values.
- Frontend production build completed successfully after the change.
## 2026-09-09 — Telemetry regression gate

- git diff --check completed without whitespace errors for the telemetry/UI/runbook scope.
- go test -race ./... — PASS, including the isolated telemetry worker and scheduler.
- No live device evidence was generated; production/live status remains fail-closed.`r`n## 2026-09-09 — Live telemetry handoff checklist

- Added docs/runbooks/edge-telemetry-live-checklist.md.
- Checklist covers binary verification, Edge-local mTLS and keystore placement, explicit SNMP target allowlist, UDP/161 reachability, Central live-observation evidence, secret redaction, and stale/offline TTL verification.
- No credentials, communities, private keys, or tokens were recorded.
- Verification: 26 backend tests passed; go test -race ./... passed.
- Frontend build was started but stopped after prolonged Vite silence; no frontend build result is claimed from this run.
- Live telemetry remains IMPLEMENTED-UNVERIFIED until an operator-configured target file and keystore are run on the active Edge.
## 2026-09-09 — Live endpoint contract regression

- Added regression coverage for GET /api/v1/discovery/live.
- Verified Edge scoping: an observation from another edge is excluded.
- Verified Central-authoritative freshness and TTL: fresh observations are marked fresh, expired observations are marked stale.
- Tests use a synthetic operator JWT; the endpoint remains protected and anonymous access is not enabled.
- Verification: 10 discovery observation tests passed; existing pytest cache warning only.
- Live device telemetry evidence is still pending; this change proves the API contract, not device availability.
## 2026-09-09 — Telemetry submit failure visibility

- Extended edge/internal/telemetry/scheduler.go with RunWithErrorHandler.
- Submit failures are now reported through an injected callback while periodic polling continues; failures are no longer silently discarded.
- Connected the standalone telemetry worker to write a generic submit error to stderr. No credential value or device secret is included.
- Preserved Run compatibility for existing callers.
- Verification: go test -race ./... passed; go build ./cmd/ainet-edge ./cmd/ainet-edge-telemetry passed.
- Live deployment and production readiness remain unchanged and fail-closed.
## 2026-09-09 — Full regression gate and test bootstrap fix

- Fixed backend/tests/conftest.py to add repository root to sys.path, allowing deploy.mtls tests to run consistently from the backend working directory.
- Initial full suite collection failed only because deploy was not importable from that working directory; no application runtime failure was observed.
- Verification: 220 backend tests passed, 3 skipped; go test -race ./... passed.
- Existing pytest cache warning remains Windows filesystem-only and does not affect test results.
- No live device, production host, credential, or external service was modified.
## 2026-09-09 — Static quality gate

- go vet ./... passed for all Edge packages.
- git diff --check passed for telemetry, endpoint tests, runbook, and session-log scope.
- Git reported only the existing LF/CRLF normalization warning for backend/tests/conftest.py.
- No runtime or external infrastructure changes were made.
## 2026-09-09 — Operational handoff finalized

- Updated docs/handoff/next-agent.md with the exact live telemetry evidence procedure and fail-closed completion criteria.
- Handoff explicitly requires Edge-local target allowlist, local keystore, mTLS scope, UDP/161 validation, authenticated live endpoint checks, and TTL stale testing.
- No secret material was added. EDGE-TELEMETRY-001 remains IMPLEMENTED-UNVERIFIED pending live evidence.
## 2026-09-09 — Fail-closed live telemetry verifier

- Added tools/verify_live_telemetry.py.
- Verifier calls the authenticated live observation endpoint, enforces Edge scope, fresh SNMP reachability, subject IP, and latency, and writes only redacted public evidence.
- Operator token is accepted only through an environment variable and is never printed or persisted.
- Added verifier usage to docs/runbooks/edge-telemetry-live-checklist.md.
- Verification: py_compile and CLI help passed.
- Live evidence remains pending until executed against an active Edge.
## 2026-09-09 — Live verifier regression tests

- Added tests/test_verify_live_telemetry.py covering accepted fresh/reachable SNMP, rejection of stale/non-reachable observations, Edge scope mismatch, and secret-field redaction.
- Verification: 4 tests passed.
- No live request or credential was used.
## 2026-09-09 — Final local slice audit

- Audited telemetry verifier, tests, scheduler, worker entrypoint, and backend test bootstrap for literal newline corruption and accidental secret material.
- No credentials, communities, private keys, or hardcoded operator tokens were found; token handling remains environment-only.
- git diff --check passed for the slice. The only repository warning is normal Windows LF/CRLF normalization.
- Local telemetry slice is ready for operator-run live evidence; production readiness is not claimed.
## 2026-09-09 — Repository root regression classification

- Edge race suite remains PASS.
- Root tests were executed with isolated basetemp: 32 passed, 1 skipped, 13 failed.
- Eight failures are non-live GNS3 integration tests requiring inventory devices not present in the local inventory fixture.
- Five failures are legacy stabilization tests expecting anonymous API access; current operator authentication correctly returns 401.
- These are separate test-harness/fixture alignment items. Security was not weakened and no inventory was fabricated.
- Telemetry slice status remains unchanged; no live infrastructure was modified.
## 2026-09-10 — Root test harness alignment

- GNS3 mutation tests now require explicit RUN_LIVE_GNS3=1 and no longer inject credential fallback values.
- Stabilization API tests now use a synthetic operator JWT; production authentication remains fail-closed.
- Device detail test skips when its optional legacy inventory fixture is absent rather than fabricating a device.
- Verification: root test suite 36 passed, 10 skipped.
- Skips are environment-gated: 9 live GNS3 tests and 1 missing local inventory fixture.
## 2026-09-10 — Final baseline verification

- go test -race ./... passed.
- Python py_compile passed for verifier and all touched test/bootstrap files.
- git diff --check passed for the complete current slice.
- Only normal Windows LF/CRLF normalization warnings remain.
- Baseline is ready for operator-run live telemetry evidence; no live infrastructure was changed.
## 2026-09-10 — Live verifier environment check

- Checked only presence of CENTRAL_URL, EDGE_ID, and OPERATOR_TOKEN in the local environment.
- None of the three parameters is configured, so no live request was attempted.
- No token or endpoint value was printed or recorded.
- Live evidence remains pending operator-side environment setup.
## 2026-09-10 — Live TLS validation

- Ran the live verifier using the local `.env` URL and a JWT generated only in process memory.
- Initial request correctly failed closed because the server presented a self-signed CA not trusted by the default Windows trust store.
- Added explicit `--ca-file` support to the verifier; retry with the available local CA still failed certificate-chain validation, so no evidence file was accepted.
- TLS verification was not bypassed and no live device mutation occurred.
- Next operational action is to supply the exact CA chain that signed the Central endpoint certificate, then rerun the verifier.
## 2026-09-10 — TLS blocker identified

- Read-only certificate inspection confirmed `central.crt` is issued by the available `AI Network Agent Lab CA`.
- `central.crt` expired on 2026-09-06, while the current date is 2026-09-10; this explains the verifier failure after supplying `ca.crt`.
- The certificate also advertises SANs `central`, `localhost`, and `172.21.0.1`; the live URL hostname must be included in the replacement certificate.
- No TLS verification bypass was used and no certificate/private key was modified.
- Next action: renew the Central server certificate with the correct production hostname/SAN, install it at the TLS terminator, then rerun the verifier.
## 2026-09-10 — Central certificate renewal preparation

- Confirmed no CA private key is present in the workstation/repository; only CA and expired Central certificate are available.
- Added deploy/production/central-server-cert.cnf.example with SAN for `ainet.antlinx.com`, `central`, `localhost`, and loopback.
- Updated deployment runbook with the approved-CA renewal procedure.
- No certificate, private key, TLS terminator, or production host was modified.
## 2026-09-10 — Local live verifier attempt

- Ran tools/verify_live_telemetry.py against Central local `http://127.0.0.1:8000` using an operator JWT created only in process memory.
- Central responded successfully, but verifier returned `NOT READY: no fresh reachable SNMP observation returned`.
- No payload, token, or credential was printed; no device mutation occurred.
- Local live gate is therefore blocked on starting/configuring the Edge telemetry worker and receiving a fresh SNMP observation.
## 2026-09-10 — Local Edge telemetry prerequisites

- Binary and mTLS files referenced by `.env` exist locally.
- No real Edge-local `telemetry-targets.json` or keystore was found in the repository/workspace; only the non-secret example target file exists.
- Worker was not started with guessed targets or credentials.
- The remaining local prerequisite is an operator-created allowlist and keystore containing the approved Cisco/MikroTik target references; secrets must remain outside repository/logs.
## 2026-09-10 — Local keystore audit

- Found a temporary Edge test keystore with ref `b-r1`, but its entry contains SSH fields only (`username`, `password`, `host_key`) and no SNMP community.
- No SNMP target allowlist exists. The existing keystore was not repurposed or copied into an active runtime.
- This confirms the live telemetry blocker is specifically SNMP credential provisioning and target allowlist creation, not Central API availability.
## 2026-09-10 — Cisco SNMP lab and Edge route diagnosis

- Cisco GNS3 console SNMP read-only configuration completed successfully with a process-local random community; the value was not logged.
- Local temporary keystore and target allowlist were created outside repository tracking using UTF-8 without BOM.
- Windows telemetry worker started and stayed alive for 20 seconds, proving binary/config parsing and control runtime startup.
- Central still had no fresh SNMP observation because Windows has no route to `192.168.1.1`; ping failed and route lookup showed no matching route.
- Correct next deployment target is the Alpine/GNS3 Edge attached to the device LAN, not the Windows Edge for this overlapping-subnet lab.
## 2026-09-10 — Alpine telemetry deployment attempt

- GNS3 TEST-EDGE metadata confirmed project open; ALPINE1 console is 5022 and IOSv1 is 5008.
- Binary, mTLS public materials, local SNMP keystore, and target allowlist were transferred to Alpine1 over a temporary local HTTP server and GNS3 console; no base64 transfer was used.
- Telemetry worker started on Alpine1, but Central did not receive a fresh SNMP observation during the verification window.
- Worker was stopped afterward because it reused `edge-001` and must not compete with the primary Edge control session.
- Windows-to-device routing was already proven absent; Alpine remains the correct execution location. Live telemetry is still unverified pending control-channel/log diagnosis and SNMP reachability confirmation.
## 2026-09-10 — MCP console execution evidence

- Used the repository MCP console tools with `approved_by=mohfa`; no alternate manual telnet path was used.
- ALPINE1 confirmed as Alpine Linux; route includes `192.168.1.0/24` on the LAN interface.
- MCP console probe confirmed Cisco `192.168.1.1` reachable with 0% packet loss.
- Port `172.21.0.1:8443` is reachable, but HTTPS response closes during handshake; telemetry log reports repeated `control hello failed ... Post https://172.21.0.1:8443/v1/control/hello: EOF`.
- No telemetry worker process is currently running on ALPINE1.
- This evidence points to the Central TLS/control listener or mTLS certificate validation, not the Alpine LAN route or Cisco reachability. No credentials or secrets were recorded.
## 2026-09-10 — MCP telemetry recovery

- Used MCP `net_console_interactive` to start the Alpine1 telemetry worker and inspect its runtime log.
- Rebuilt/restarted only the local `mtls-gateway` profile after adding bounded, secret-free gateway error logging and safe TLS close handling; gateway tests: 4 passed.
- Initial gateway errors were identified as `ConnectionRefusedError` to the API upstream during API container recreation.
- After API/gateway startup completed, API logs showed repeated successful `POST /api/v1/control/discovery/observations` (HTTP 200), heartbeat, and task-poll requests from the Edge through mTLS gateway.
- MCP console confirmed Cisco `192.168.1.1` remained reachable from ALPINE1. Live telemetry path is now operational in the local lab; the worker remains running for observation.
- No credential, token, private key, or SNMP community was recorded.
## 2026-09-10 — Final local telemetry validation

- MCP console validation on ALPINE1: telemetry worker process is running and Cisco `192.168.1.1` is reachable over the local LAN.
- Central/TLS gateway metrics and API logs confirm successful discovery-observation requests; the old EOF lines are historical startup failures.
- MCP console validation on ALPINE2: LAN interface `192.168.1.20/24` and Cisco `192.168.1.1` reachability are healthy, but no telemetry worker is installed/running there.
- Edge-002 deployment is intentionally not started because the repository has no `edge-002` client certificate/key; generating or reusing another Edge identity would violate PKI isolation.
- Targeted backend/gateway/live-gate tests passed: 18 passed using repository basetemp.
- Frontend production build passed (`tsc && vite build`); only existing Vite/Rolldown dependency and chunk-size warnings remain.
- Next safe action: provision a dedicated edge-002 certificate/key through the approved PKI workflow, then deploy the same telemetry worker to ALPINE2 and verify overlapping-subnet observations.
## 2026-09-10 — Edge-002 live SNMP proof

- MCP console confirmed ALPINE2 has the dedicated `edge-002` certificate/key and the main Edge binary; no Edge-001 identity was reused.
- A controlled lab test temporarily stopped Edge-002 main process, transferred the already-built telemetry binary, and used the existing Edge-002 local keystore reference `b-r1` without logging its secret.
- Initial telemetry URL without `/api` returned HTTP 404; corrected to `https://172.21.0.1:8443/api` according to the deployed control route.
- Live verifier then returned: `edge-002`, 568 observations, 1 fresh reachable SNMP observation for `192.168.1.1`, latency approximately 10 ms, vendor Cisco.
- Telemetry worker was stopped and the main Edge-002 binary was restored. MCP console confirmed `control session ready` for `edge-002`.
- Fixed missing `ssl` and `urllib.parse` imports in `tools/verify_live_telemetry.py`; temporary verifier was removed after use.
- Edge-002 overlapping-subnet lab evidence is now recorded; persistent telemetry scheduling still belongs in the Edge service lifecycle rather than a competing second control session.
## 2026-09-10 — Telemetry integrated into main Edge binary

- Extended `edge/cmd/ainet-edge/main.go` to load an Edge-local telemetry target allowlist and run the SNMP scheduler in the existing authenticated control session.
- Added scoped runtime flags: `--discovery-customer-id`, `--discovery-site-id`, `--telemetry-targets-file`, `--telemetry-interval`, and `--telemetry-ttl`.
- The main Edge binary now submits telemetry through `control.Client.SubmitDiscoveryObservations`; no second control session is required.
- Missing customer/site scope fails closed when a telemetry target file is configured. Empty target file means telemetry scheduler remains disabled.
- Updated `docs/runbooks/edge-telemetry-worker.md` with the integrated deployment command and duplicate-session warning.
- Verification: `go test ./cmd/ainet-edge ./internal/telemetry ./internal/control` passed; both Edge binaries built successfully.
- Live Edge-002 proof remains recorded above; its main process was restored after the controlled telemetry test.
## 2026-09-10 — Integrated telemetry live deployment

- Built Linux/amd64 `edge/dist/ainet-edge-linux` from the integrated main Edge binary.
- Deployed it to ALPINE2 via MCP console and started one `ainet-edge` process with `--telemetry-targets-file`, customer/site scope, 15-second interval, and 45-second TTL.
- No standalone telemetry worker remains active on ALPINE2; the main Edge process is the sole control-channel owner.
- MCP console confirmed the integrated process remains running without runtime errors.
- Central API logs confirmed repeated HTTP 200 heartbeat and `/api/v1/control/discovery/observations` requests after the integrated binary started.
- This closes the local implementation slice for single-session telemetry scheduling. Existing source/runtime discovery flag differences must be reconciled before packaging a production updater; production readiness remains false.
## 2026-09-10 — Integrated passive discovery scheduler

- Objective: reconcile the old Edge discovery startup flags with the current main Edge runtime without creating a second worker or bypassing policy boundaries.
- Evidence inspected: `edge/internal/discovery/local.go`, `probe.go`, `service_scan.go`, `edge/internal/telemetry`, Central discovery schemas and Edge control ingestion.
- Decision: EXTEND existing `internal/discovery` and `internal/control.Client`; no parallel discovery subsystem.
- Implementation: added `edge/internal/discovery/scheduler.go`; main Edge now publishes local interface/route/ARP observations through the existing mTLS session. Optional service checks are bounded to observed ARP addresses and common management ports only; no CIDR expansion, nmap, shell scan, or credential transmission.
- Compatibility: `--discovery-interval-seconds`, `--discovery-ttl-seconds`, and `--discovery-service-scan` are retained as explicit aliases/controls for existing lab launch commands and map to the bounded scheduler.
- Verification: Go tests for discovery/main/telemetry/control passed; Linux amd64 binary built; ALPINE2 deployed with one main Edge process (PID 1904 at verification); Central returned HTTP 200 for repeated heartbeat and discovery observation submissions.
- Security: customer/site/edge scope remains required; observation IDs include Edge scope; no secrets are placed in observations or logs.
- Remaining: deploy equivalent binary to ALPINE1/Windows after their maintenance window; run full live verifier and update production evidence only after operator token is available.
## 2026-09-10 — ALPINE1/ALPINE2 convergence

- ALPINE1 was found running the integrated main Edge plus a duplicate standalone telemetry worker. The standalone worker was stopped.
- ALPINE1 was upgraded to the same Linux amd64 main binary and started with scoped passive discovery flags for `cust-a/site-a`.
- ALPINE2 remains on the same integrated binary for `cust-b/site-b`.
- Live evidence: both Edge processes remained active; Central returned HTTP 200 for repeated heartbeat and discovery observation requests.
- Important compatibility finding: the previous ALPINE1 launch file used `--enable-command-bundles` and bundle-key flags, but the current source main binary does not define those flags and the Central-client path does not execute command bundles. The new deployment intentionally omits unsupported flags instead of silently claiming mutation support. Command-bundle reintroduction is a separate implementation task and must be tested fail-closed before enabling.
- Temporary binary transfer server was stopped after deployment.
## 2026-09-10 — Signed command-bundle wiring

- Reused existing `internal/bundle`, `internal/executor/bundle_transport.go`, and `internal/security` instead of creating another execution subsystem.
- Main Edge task poller now recognizes `command.bundle.execute` only when `--enable-command-bundles` is explicitly set.
- Enabling requires a Central Ed25519 public key and trusted signer key ID; bundle identity, signature, digest, phases, transport, and local credential resolution are validated before execution.
- Result contains status, phase/step metadata, output sizes/hashes, and execution fingerprint; raw command output is not returned.
- Feature remains OFF on ALPINE1/ALPINE2. Both run the updated binary and continue sending heartbeat/discovery observations successfully.
- Focused tests and build passed; temporary transfer server stopped.
- Remaining gate: perform an explicitly approved signed lab bundle test using a non-production device, then add evidence before enabling mutation in any customer Edge.
## 2026-09-10 — Command-bundle executable gates

- Central tests: `17 passed` for command-bundle construction/signing, dispatch approval, and mutation safety using the repository virtual environment.
- Edge tests: `go test -race ./...` passed across main Edge, bundle, control, credentials, discovery, executor, security, SNMP, and telemetry packages.
- Live mutation gate remains intentionally blocked: the active local runtime has no configured Central signing key/public-key pair for a controlled lab dispatch. No new key was generated and no device mutation was sent.
- Default runtime behavior remains read-only; `--enable-command-bundles` is not enabled on ALPINE1 or ALPINE2.
## 2026-09-10 � Signed command-bundle lab activation

- Reused the existing lab public-key file and Central signer configuration; no new private key was generated and no secret material was logged.
- Reconciled the non-secret signer key identifier between Central and ALPINE1 (`local-build-only`).
- Restarted ALPINE1 with the explicit bundle flags and verified one active Edge process with `--enable-command-bundles`, trusted public-key path, and bounded discovery settings.
- Removed the stale duplicate read-only ALPINE1 process; ALPINE2 was not changed and remains bundle-disabled.
- Central logs confirmed the restarted ALPINE1 control session and repeated HTTP 200 heartbeats. Existing evidence `docs/evidence/m2-transport/live-signed-command-bundle-central-edge-r1-20260908.json` records the prior safe lab read-only bundle as VERIFIED; no production mutation was performed.
- Security: bundle execution is limited to explicit runtime enablement, signer identity, digest/signature/expiry/phase checks, local credential reference resolution, and sanitized result metadata. Production readiness remains false.
- Remaining: run a fresh Central-dispatched signed lab bundle only if a current task/approval API evidence record is required; keep ALPINE2 and customer Edges disabled until that evidence is captured.

## 2026-09-10 � Fresh lab read-path check after bundle activation

- Central inventory read via `net_list_devices` succeeded and confirmed `r1-native-edge001` is scoped to `edge-001` / `cust-a` / `site-a`.
- ALPINE1 local reachability was verified independently: `192.168.1.1` replied to ICMP and TCP/22 was open; Cisco SSH banner was present.
- Central `device.read.facts` through the current task path returned an SSH timeout, so a fresh signed-bundle dispatch was not forced. This is an execution-path/credential or transport negotiation blocker, not a LAN reachability failure.
- No device configuration was changed. Existing verified read-only signed-bundle evidence remains authoritative until the current task path produces a new attempt record.

## 2026-09-10 � ALPINE1 credential diagnosis

- ALPINE1 has `/usr/bin/ssh` and `/usr/bin/sshpass`; the Edge executor includes the IOSv legacy-KEX fallback.
- The active ALPINE1 keystore does not contain `r1-lab` (username and pinned host key are absent). This explains the Central facts timeout despite ICMP/TCP/22 reachability.
- Existing `b-r1` artifacts belong to the Edge-B/IOSv2 context and were not copied to ALPINE1 because overlapping-subnet credentials and host keys must remain site-scoped.
- No password was printed, transferred into logs, or guessed. The next safe action is to reprovision ALPINE1's `r1-lab` credential through the protected deployment path, then retry the read-only facts and signed-bundle evidence.

## 2026-09-10 � Lab credential reset attempt and cleanup

- IOSv1 console was located and confirmed reachable; an authenticated read-only console check returned IOSv software information.
- A temporary lab credential transfer was attempted using the user-provided candidate password. IOSv1 rejected SSH authentication, so no repeated guessing or router reset was performed.
- The temporary ALPINE1 keystore entry was removed and Edge was restarted with the signed-bundle verifier still enabled but no usable device credential; execution therefore remains fail-closed.
- Temporary HTTP transfer server was stopped. No production device or configuration was changed.
- Blocker: the current IOSv1 admin password must be reset or supplied through a protected local provisioning path before Central facts and fresh signed-bundle evidence can pass.

## 2026-09-10 � ALPINE1 lab credential provisioned

- Provisioned the explicitly supplied lab-only `r1-lab` credential and pinned IOSv public host key into ALPINE1's protected keystore; the secret value is omitted from this log.
- Restarted ALPINE1 with one active signed-bundle-enabled Edge process. Temporary transfer server was stopped after installation.
- Direct ALPINE1 SSH diagnostic to IOSv1 succeeded with legacy KEX and returned the IOSv software banner, proving the local credential, host, and transport path are valid.
- Central `GET /devices/r1-native-edge001/facts` still returned 504 and Central audit classified it as `EXEC` from `user=system`; this indicates the current facts endpoint is bypassing the Edge route or using a separate Central credential path. No device configuration was changed.
- Next implementation target: make the facts/read endpoint use the authoritative Execution Routing Resolver and Edge task path, then rerun the signed read-only evidence.

## Follow-up: EDGE/DIRECT UI execution routing verification — 2026-09-10

- Operator: Codex
- Objective: ensure device detail/facts execution and UI behavior distinguish EDGE devices from DIRECT devices.
- Reuse/Extend decision: EXTEND existing `/devices/{device_id}/facts`, capability task endpoint, execution routing resolver, Edge facts executor, inventory metadata, and frontend device detail loader; no parallel jobs or transport subsystem created.
- Implementation:
  - EDGE facts now resolve through the existing capability task route and Central lease/Edge dispatch path.
  - DIRECT facts continue through the existing Central device service/driver path.
  - Inventory contains only non-secret `credential_ref` metadata for Edge routing; credentials remain Edge-local.
  - Frontend Edge detail avoids direct Central interfaces/routes/health calls and consumes routed Edge facts; Direct detail retains Central calls.
- Live evidence:
  - `r1-native-edge001` returned `execution_location=EDGE`, `edge_id=edge-001`, and normalized Cisco facts through `Central -> Edge -> IOSv`.
  - `r1-m1` remained a Central/DIRECT request and its failure was a Central SSH timeout; it was not routed through Edge.
  - Central accepted and deduplicated live observations for edge-001, edge-002, and edge-windows-001.
- Lab remediation:
  - Rebuilt Edge as Linux amd64; corrected an earlier accidental Windows PE binary transfer.
  - Refreshed the disposable lab Edge SSH host-key/credential state after IOSv host-key regeneration.
  - Refreshed the local Central container with current Edge heartbeat/discovery schemas.
  - Moved the malformed disposable-lab discovery store to a recoverable `.pre-edge-schema-fix` backup; a new validated store was generated.
- Verification:
  - `python -m compileall` passed.
  - Frontend production build passed with existing Vite chunk/deprecation warnings only.
  - Routing/task regression tests: 13 passed, 1 warning.
  - Live EDGE facts: passed.
- Security: no secret values were written to this log; Edge payloads use credential references only; SSH host-key pinning remains enforced.
- Remaining work: commit/push this implementation slice, then validate the UI detail page against the live Edge observations and add a dedicated API/UI regression test for EDGE-vs-DIRECT detail behavior.
### Regression coverage follow-up — 2026-09-10

- Added `backend/tests/test_device_execution_routing.py`.
- Test 1 verifies EDGE facts create `device.read.facts` capability dispatch with edge/customer/site and credential reference metadata.
- Test 2 verifies DIRECT facts call the existing Central `device_service.facts` path and do not dispatch to Edge.
- Result: 2 passed (one existing pytest cache warning only).
- Frontend production build remains successful; existing Vite optimization/chunk warnings are non-blocking.