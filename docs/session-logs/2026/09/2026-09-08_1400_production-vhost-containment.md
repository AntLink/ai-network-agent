# Session Log — Production Vhost Containment

- operator: Codex
- current milestone: M4 Production Operations / containment
- session objective: lock the incomplete public browser/API deployment before frontend and authentication work continues
- repository state: active mature repository; unrelated working-tree changes preserved
- skill contract: `ainet-zerotier-platform` V5.3

## REUSE / EXTEND / REFACTOR / CREATE

- REUSE: existing Nginx vhost, health route, separate Edge mTLS vhost
- EXTEND: Nginx deployment documentation and production evidence
- REFACTOR: none
- CREATE: containment evidence and this session log

## Decision

The browser/API deployment was a smoke test of routing and TLS, not a
feature-complete frontend release. Anonymous API reads were previously
observable, so the public application vhost is fail-closed until
`API-AUTH-001` and frontend acceptance evidence pass.

## Files changed

- `deploy/production/nginx/ainet.antlinx.com.conf`
- `docs/evidence/m4-production-operations/ainet-vhost-lock-20260908.json`
- this session log

## Commands/tests

- inspected the current Nginx vhost and existing production evidence
- local configuration now returns 403 for `/api/` and `/`, while `/health`
  remains proxied
- live reload/HTTP verification is pending the safe production SSH path

## Security and licensing

- public application data access is blocked by design
- Edge control remains isolated behind client mTLS
- no credentials, tokens, certificates, or private keys were recorded
- no licensing decision changed

## Remaining work / handoff

- apply and verify the same lock on the production host
- implement authenticated operator boundary
- complete frontend functionality and acceptance tests
- rerun production gate before considering unlock

Start the next session by verifying live `/health` remains 200 and `/`,
`/api/` return 403. Do not unlock the public vhost until the listed gates pass.

## Local-only continuation

- production server is now locked and is out of scope for this workstream
- audited the frontend and found MSW was started unconditionally from
  `src/main.tsx`
- fixed the bootstrap so MSW starts only when `VITE_USE_MOCKS=true`
- local real-backend build passed with `VITE_USE_MOCKS=false`
- build result: 4524 modules transformed; Vite build exit 0
- warnings remain for dependency optimization and large chunks; they are not
  production approval evidence

## Edge transport continuation

- extended `edge/internal/executor/bundle_transport.go` with a Windows
  transport configuration and explicit PowerShell remoting runner
- added `edge/internal/executor/windows_transport.go` using bounded
  `Invoke-Command` over WinRM/PowerShell Remoting on Windows Edge
- added explicit `serial-over-tcp` opt-in for serial lines exposed by a
  terminal server
- added native `COMx`/`/dev/tty*` support using `go.bug.st/serial`, with
  prompt synchronization, bounded output, timeout, cancellation, and local
  keystore credential resolution
- Telnet and terminal-server TCP prompt sessions retain bounded output,
  timeout, local-keystore authentication, and no SSH fallback
- `https_api` remains intentionally deferred because it requires typed vendor
  adapters rather than a generic unsafe HTTP command runner

## Verification

- `go test -race ./...`: PASS
- Windows/amd64 Edge cross-build: PASS
- no production deployment performed

## Remaining work

- live test Telnet/terminal-server against an approved lab endpoint
- live test WinRM/PowerShell Remoting against an approved Windows lab host
- live test native serial against an approved COM/tty device

## Local GNS3 console verification

- TEST-EDGE is open on GNS3 VM `172.21.0.2`
- IOSv1 Telnet port 5008: TCP connection accepted
- IOSv2 Telnet port 5011: TCP connection accepted
- MikroTik-CHR3 terminal-server console port 5018: TCP connection accepted
- MikroTik read-only `/system resource print` returned prompt, uptime, and
  version evidence; no configuration command was sent
- Evidence: `docs/evidence/m2-transport/gns3-console-readonly-live-20260908.json`
- This proves local console reachability, not yet full Central-to-Edge signed
  bundle execution for every transport profile

## Transport regression continuation

- Re-ran Edge `go test -race ./...`: PASS for command, bundle, control,
  credentials, discovery, executor, and security packages.
- Added and passed an in-process terminal-server handshake test covering login,
  password prompt, command execution, bounded prompt output, and cleanup.
- Re-ran the focused Central contract suite with a workspace-local pytest
  temporary directory: `16 passed`; the first attempt's Windows temporary
  directory permission error was environmental and did not reproduce.
- Added `docs/evidence/m2-transport/transport-contract-regression-20260908.json`.
- Transport decision remains explicit: SSH and console are the active lab
  gates; WinRM/PowerShell Remoting is code-complete for Windows Edge but awaits
  a Windows lab target; HTTPS vendor API remains fail-closed and deferred.
- No production host, public vhost, device configuration, credential, token,
  certificate, or private key was changed or recorded.

## Live-test boundary

- GNS3 API confirmed current `TEST-EDGE` metadata: ALPINE1 telnet console
  `5022` and MikroTik-CHR3 telnet console `5018`, both started.
- A non-invasive workstation probe did not provide an authenticated raw Edge
  shell; the endpoint responded with an SSH identification banner instead of
  the expected telnet console stream. No credential guessing or node
  reconfiguration was attempted.
- The live Central -> active Edge -> signed terminal-server bundle gate is
  therefore **PENDING**. Connector reachability and contract/regression gates
  remain PASS.

## Frontend local continuation

- Reused the existing alert API client and added `acknowledgeBackendAlert`;
  the Alerts page now calls `PATCH /api/v1/alerts/{id}` with
  `status=acknowledged` instead of showing a success toast without a backend
  mutation.
- Local real-backend frontend build (`VITE_USE_MOCKS=false`) passed: 4524
  modules transformed; only existing dependency/chunk-size warnings remain.
- Discovery UI now dispatches the existing policy-scoped endpoint instead of a
  fake success toast. Local API verification returned `accepted`, planned 254
  targets, `probes_started=false`, and `target_dispatch=EDGE_REQUIRED`.
- Evidence: `docs/evidence/m2-transport/frontend-discovery-policy-dispatch-20260908.json`.
- Credentials UI now submits profiles to `POST /api/v1/credentials`; the
  secret field is controlled only in memory and cleared after a successful
  save. The UI no longer reports a fake connection-test success because the
  backend test endpoint requires a target device and is not implemented yet.
- Frontend real-backend build after the credentials change: PASS, 4524
  modules transformed.
- Discovery “Add” action now calls the backend add endpoint with validated
  device identity and customer/site/edge context; the backend creates the
  inventory record and rejects duplicate device IDs.
- Discovery policy tests: `7 passed`; frontend build after this change: PASS,
  4524 modules transformed.
- Backup UI now uses the real download endpoint with encoded backup IDs. View
  is download-backed; Compare remains explicitly unavailable until a backend
  comparison endpoint exists, and Restore remains blocked in the UI until an
  authenticated `network-admin` dispatch path is wired.
- Frontend build after backup changes: PASS, 4524 modules transformed.
- Authentication audit found no existing login/token issuance endpoint or
  backend operator-token verifier. Sensitive backend routes already require
  `X-Authenticated-Operator` plus an allowed role, but a frontend-only
  identity header would be spoofable. No fake login or bypass was added;
  restore, approval, and task-sensitive actions remain fail-closed.
- Next security slice: implement a real Central authentication boundary and
  then bind frontend operator sessions to those backend-issued credentials.
- Production remains locked; no deployment or public API change was made.

## Authentication boundary continuation

- Reused the existing FastAPI configuration/router and added a real Central
  authentication boundary at `/api/v1/auth/login` and `/api/v1/auth/me`.
- Password verification uses PBKDF2-SHA256; access tokens are signed HS256
  bearer tokens with an explicit expiry. Missing operator ID, password hash,
  or JWT secret fails closed with service-unavailable/unauthorized behavior.
- No password, token, signing secret, certificate, or private key was written
  to this log or repository. No real operator credentials were configured.
- Changed/added: `backend/app/core/auth.py`,
  `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/router.py`,
  `backend/app/core/config.py`, `backend/.env.example`, and
  `backend/tests/test_operator_auth.py`.
- Verification: `11 passed` for operator-auth plus discovery-policy focused
  tests; Python compile check passed for the new auth modules.
- Traceability: `API-AUTH-001` moved from BLOCKED to PARTIAL. The boundary is
  implemented, but all sensitive routes still need bearer-dependency
  migration and the frontend operator session is not yet wired.
- Security decision: do not replace the existing fail-closed legacy operator
  checks with an unverified compatibility bypass. Production remains locked.

## Sensitive-route bearer migration

- Replaced legacy operator-header authorization on privileged task approval,
  dispatch, retry/replay, Edge revoke/quarantine/clear-quarantine, backup
  restore, and Edge rollout endpoints with FastAPI bearer dependencies backed
  by the signed Central token boundary.
- Role separation is explicit: network-operator may perform task approval and
  retry/replay actions; network-admin is required for Edge lifecycle, backup
  restore, and rollout operations.
- Existing route tests were migrated to signed bearer test tokens; no real
  credentials or secrets were introduced.
- Verification: sensitive-route regression plus auth/backup/update suites
  `41 passed`; Python compile check passed. No `X-Authenticated-Operator` or
  `X-Operator-Role` authorization use remains in the affected API endpoints.
- `API-AUTH-001` remains PARTIAL: frontend login/session binding and the
  anonymous-read exposure audit are still required before production unlock.

## Frontend operator session binding

- Reused the existing React/Vite login surface and backend API client. Login
  now calls `/api/v1/auth/login`, keeps the signed session only in
  `sessionStorage`, and automatically adds `Authorization: Bearer` to real
  backend requests.
- Added a route guard for the existing `FullLayout`; when real backend mode is
  enabled without a session, the UI redirects to `/auth/auth2/login`. Mock
  mode remains available for UI development.
- Changed/added: `src/api/network/backend-client.ts`,
  `src/views/auth/authforms/auth-login.tsx`, `src/routes/Router.tsx`, and
  `src/components/auth/require-backend-auth.tsx`.
- Verification: `npm run build` PASS (`4540 modules transformed`); backend
  sensitive-route/auth regression remains `41 passed`.
- This is not production-ready evidence yet: browser login against a configured
  Central instance and anonymous-read API coverage still need live local
  verification. Production remains locked.

## Anonymous-read boundary evidence

- Added router-level bearer protection to Central application APIs for devices,
  tasks, audit, credentials, discovery, topology, backups, alerts, GNS3,
  vendor APIs, terminal, policy, agent, and related application surfaces.
- `/api/v1/auth/*` remains the login/identity exception; `/api/v1/control/*`
  remains the Edge control-channel exception and retains Edge identity/mTLS
  checks plus bearer protection on operator lifecycle actions.
- Added `backend/tests/test_api_auth_boundary.py`: anonymous reads of nine
  application data paths and `/auth/me` return `401`.
- Evidence: `docs/evidence/m4-production-operations/api-auth-boundary-local-20260908.json`.
- Verification: full backend suite `211 passed, 3 skipped`; frontend build
  remains PASS. `API-AUTH-001` remains PARTIAL only because authenticated
  browser smoke against configured Central and production-gate rerun are not
  yet complete.

## Local authenticated login smoke

- Added an in-process Central smoke test for the complete login contract:
  correct credentials receive a bearer token, `/auth/me` accepts it, and a
  protected `/devices` read succeeds; incorrect credentials return `401`.
- Evidence: `docs/evidence/m4-production-operations/api-auth-login-smoke-local-20260908.json`.
- Verification: focused auth suite `8 passed`; full backend suite `213 passed,
  3 skipped`. No real credentials, tokens, or secrets were logged.
- Remaining boundary: this proves Central application behavior locally, not a
  browser against the public hostname/TLS path. Production remains locked and
  the production gate has not been marked ready.

## Production gate authentication integration

- Added required gate `API-AUTH-001` to `docs/production/production-gate.json`
  so authentication evidence is part of the executable fail-closed release
  gate rather than only a traceability note.
- Gate rerun result: PASS, report
  `docs/evidence/production-gates/production-gate-20260908-145117.md` and
  matching JSON. This PASS validates the configured local/repository gates; it
  does not authorize production deployment because external hostname/TLS and
  operational approvals remain separate.
- No production host, DNS, Cloudflare, Nginx, certificate, credential, or
  overlay state was changed.

## Frontend preview smoke

- Ran the built frontend with `vite preview` on local loopback. The login page
  rendered with operator/password/sign-in controls and no browser console
  errors.
- Requested `/dashboard` without a session and observed redirect to
  `/auth/auth2/login`, proving the anonymous route guard.
- Evidence: `docs/evidence/m4-production-operations/frontend-auth-route-guard-local-20260908.json`.
- No password was entered in the browser; authenticated login is proven by the
  in-process Central API smoke test. Public hostname/TLS browser smoke remains
  pending and production stays locked.

## Authenticated browser smoke continuation

- Started Central with temporary local-only auth configuration and Vite preview
  with loopback CORS/API settings; no values were persisted to repository or
  evidence.
- Browser login succeeded, redirected to `/dashboard`, and the protected
  `/api/v1/devices` request returned `200`; browser console reported no errors.
- Fixed a real UI defect discovered during the test: the Base UI sign-in
  button needed explicit `type="submit"`. Frontend rebuild passed (`4540
  modules transformed`).
- Evidence: `docs/evidence/m4-production-operations/frontend-authenticated-smoke-local-20260908.json`.
- Local preview and Central smoke processes were stopped afterward. The
  dashboard load showed an existing local GNS3 project request; no production
  system was involved. Public hostname/TLS smoke remains the next external
  boundary.

## Frontend navigation alignment

- Reused the canonical `src/layouts/full/vertical/sidebar/sidebaritems.ts`
  navigation source and aligned labels with implemented platform capability
  areas: AI & Operations, Network, Lab & Simulation, Execution Context,
  Automation & Safety, and Platform Security.
- Added visible safety/context badges: Terminal `PRIVILEGED`, Discovery
  `SCOPED`, GNS3 `LAB`, Production `LOCKED`, and Credentials `SECURE`.
- No new route or parallel navigation subsystem was created.
- Verification: frontend build PASS (`4540 modules transformed`); browser
  preview confirmed all six headings and badges render. Production was not
  opened or changed.

## Frontend degraded-mode repair

- User-observed issue: the menu rendered, but the `Execution Context ->
  Overview` page displayed `Failed to load environment dashboard` while the
  local GNS3 controller was intentionally unavailable.
- Evidence from the Central log: the GNS3 driver attempted `localhost:3080`
  and received `ClientConnectorError`; this is an optional lab-provider
  outage, not an authentication failure.
- Reused the existing environment data loader and changed
  `src/api/environments/index.ts` so an unavailable GNS3 provider returns an
  empty project set and leaves the overview usable in degraded mode.
- Verification: frontend production build PASS (`4540 modules transformed`);
  authenticated browser audit of 22 navigation routes found no page errors
  except the environment overview before the fix. After the fix, the overview
  rendered successfully with `No project selected` and no browser console
  errors.
- GNS3-specific pages still depend on the controller and must report its
  disconnected state until the GNS3 VM/controller is started. Production was
  not opened or changed.

## Frontend device contexts and settings navigation

- Reused the existing Devices page, backend device loader, Agent assistant-ui,
  and Settings page rather than creating parallel pages.
- Devices now presents three explicit contexts: `GNS3 Devices` with a project
  selector, `Edge Devices` for customer/site/edge-routed inventory, and
  `Direct Devices` for direct-IP inventory.
- Normalized frontend device metadata now preserves execution location, Edge,
  customer/site, project, and source classification. Edge classification takes
  precedence over virtual-device classification so an Edge-routed lab device
  is not incorrectly shown as a direct GNS3 device.
- Removed the duplicate Agent Chat navigation entry and kept `/agent` as the
  single agent workflow entry. The dashboard primary action now also points
  to `/agent`, avoiding two competing agent paths.
- Settings already had the required eight categories; the navigation was
  validated for General, AI, Devices, SSH, GNS3, Containerlab, Security, and
  Notifications.
- A hook-order defect found during browser validation (React error #310) was
  fixed by keeping the Devices filtering hooks unconditional before render
  guards.
- Verification: frontend build PASS (`4540 modules transformed`); local
  authenticated browser validation shows 2 GNS3, 5 Edge, and 5 Direct devices,
  Agent Chat route, all eight Settings categories, and no browser console
  errors. Evidence:
  `docs/evidence/m4-production-operations/frontend-device-contexts-local-20260908.json`.
- Production remains locked and unchanged.

## Next-session handoff

1. Start the GNS3 VM/controller and repeat the live lab menu test; expected
   controller endpoint is the configured GNS3 integration, not the production
   host.
2. Exercise one authenticated read and one approval-protected operation from
   the UI against the local Central/Edge lab path; keep production locked.
3. Add durable evidence for the frontend menu audit and degraded GNS3 state,
   then update traceability if the tested route behavior changes.
4. Do not unlock production or change the production gate until external
   hostname/TLS, PKI, overlay, and deployment evidence are complete.

## Local services restarted

- Restarted the local Central API with temporary local-only authentication
  configuration; health check returned HTTP 200 on `127.0.0.1:8000`.
- Restarted the frontend preview; HTTP 200 confirmed on `127.0.0.1:4173`.
- No production service, DNS, Cloudflare, certificate, overlay, or device
  configuration was changed. Temporary credentials were not written to this
  log or repository.

## Frontend visual refresh

- Reused the existing `FullLayout`, Header, Dashboard, Devices, assistant-ui,
  and Settings routes; no alternate frontend framework or parallel API was
  introduced.
- Refreshed the NOC shell with rounded workspace framing, responsive content
  width, Central/ GNS3/ Edge/ AI status indicators, and clearer production
  lock visibility.
- Refreshed the dashboard with an operational hero, direct Agent Chat and
  Devices actions, operational snapshot heading, and safety banner while
  retaining the existing live summary cards, health chart, and device table.
- Verification: TypeScript/Vite production build PASS (`4540 modules
  transformed`). Production remained locked and unchanged.

## Agent workspace session handling

- Diagnosed `Failed to load AI agent workspace` from Central logs: the browser
  was sending expired/invalid bearer sessions and protected Agent dependencies
  returned repeated HTTP 401 responses. Direct authenticated checks for the
  device and containerlab endpoints succeeded; GNS3 being offline is a
  separate degraded lab condition.
- Updated `src/api/network/backend-client.ts` so a protected request receiving
  HTTP 401 clears the session and redirects to `/auth/auth2/login?reason=session-expired`.
  This prevents a stale session from being presented as a generic workspace
  or inventory failure.
- Frontend build PASS (`4540 modules transformed`). No credentials or tokens
  were written to this log; production remained locked and unchanged.

## Agent dependency smoke

- Re-authenticated with the temporary local operator and checked the Agent
  dependency endpoints: devices, containerlab labs, GNS3 local configuration,
  agent sessions, 9Router status, and tasks all returned HTTP 200.
- The remaining GNS3 controller connection refusal is represented as a lab
  degraded state; it is not allowed to block the authenticated Agent workspace.
- Browser automation was unavailable during this retry, so final visual Agent
  confirmation remains a manual local check after signing in again.

## Agent degraded lab tolerance

- Updated `src/views/agent/index.tsx` so Agent requires authenticated device
  inventory and execution-plan state, but does not block the workspace when
  optional GNS3/Containerlab providers are unavailable.
- Optional lab failure is now handled as degraded context and remains visible
  through the existing backend-status panel; chat and guarded workflow remain
  available.

## Devices page context refinement

- Reused the existing Devices page and `DeviceStatusTable` to make execution
  context explicit in every row: `GNS3`, `Edge`, or `Direct IP`.
- Edge rows show available `edge_id`, customer, and site context; GNS3 rows
  show project/lab context; direct rows show the management address context.
- This preserves overlapping management IPs as separate device identities and
  keeps the existing Open, SSH, Run Command, Configure, Backup, Edit, and
  Delete actions.
- Frontend build PASS (`4540 modules transformed`). Production remained locked
  and unchanged.

## Edge detail site view

- Extended the existing `/devices/:id` detail route; no parallel Edge page or
  duplicate inventory subsystem was created.
- When the opened device is in `EDGE` execution context, the page derives the
  Edge scope from `edge_id` and loads the existing full device inventory through
  `useDevices()`.
- The detail view shows Edge identity, customer/site context, Edge status,
  connected-device count, online/degraded summary, and a reusable device table
  for every device assigned to the same Edge. Grouping uses `edge_id`, never
  management IP, so overlapping LAN addresses remain isolated.
- If the inventory request fails, the selected device detail remains usable and
  the Edge inventory panel reports a recoverable degraded state.
- Verification: `npm.cmd run build` PASS (`4540 modules transformed`); only
  existing Vite optimization and large-chunk warnings remain. Production was
  not touched.

## Live Edge inventory refresh

- Extended the existing SWR hooks instead of adding a second telemetry client.
- `useDevices()` and `useDeviceDetail()` now revalidate every 5 seconds and on
  window focus, retaining the last good view while a refresh is in flight.
- Edge Site View therefore updates device membership, status, CPU/memory,
  latency, last-seen, interfaces, and routes from the latest Central inventory
  response without a manual page reload.
- This is controlled live polling of Central's current Edge inventory, not a
  new high-frequency PostgreSQL heartbeat writer or an unimplemented browser
  WebSocket. The Edge/Central telemetry channel remains the source of truth.
- Production was not touched.

## Edge-authoritative runtime status

- Live inspection confirmed GNS3 controller `172.21.0.2` is reachable and the
  `TEST-EDGE` project is open; ALPINE1 and ALPINE2 are reported `started` by
  the GNS3 API. This proves the lab nodes are powered, not that their Edge
  processes have completed the Central mTLS HELLO/READY handshake.
- Added the read-only Central endpoint `/api/v1/control/status`, backed by the
  existing in-memory/Redis Edge session registry. It reports ready state,
  heartbeat age, TTL, and online/offline status.
- Frontend inventory now applies this authoritative Edge status to every child
  device. If an Edge session is offline or expired, all devices owned by that
  `edge_id` are displayed offline, regardless of a stale device snapshot.
- The Edge detail panel now exposes `Control Channel` and `Edge Last Seen`, so
  operators can distinguish an active Edge from a merely running GNS3 VM.
- No direct guest-console command or device mutation was executed. Production
  remains locked.

## Live GNS3 Edge connectivity evidence

- GNS3 API `http://172.21.0.2/v2` responded successfully; GNS3 version is
  `2.2.61` and project `TEST-EDGE` is `opened`.
- GNS3 reports ALPINE1 and ALPINE2 as `started`. Read-only console inspection
  confirmed `/usr/local/bin/ainet-edge` and the OpenRC service are running.
- ALPINE1 is configured with Edge ID `edge-001`; ALPINE2 with `edge-002`.
  Both currently attempt the configured Central control address
  `172.21.0.1:8443`, but the guest sockets remain `SYN_SENT`.
- Host validation confirmed Central API `127.0.0.1:8000` is healthy, while no
  listener is present on `127.0.0.1:8443` or `172.21.0.1:8443`.
- Conclusion: the lab Edge processes are running but not connected to Central;
  this is a control-channel listener/routing blocker, not a frontend inventory
  issue. Until the mTLS listener is available, Edge child devices must be
  displayed offline/fallback and must not be reported online.

## Local lab mTLS listener activated

- Docker Desktop engine was not available to the current shell, and the compose
  profile required runtime secrets not present in this local process. Reused the
  repository's `deploy/mtls/revocation_gateway.py` directly with the existing
  runtime lab certificates.
- Local gateway is listening on `0.0.0.0:8443` and proxies to the local Central
  API at `127.0.0.1:8000`. This is a temporary lab process, not production.
- ALPINE1 (`edge-001`) established a live TCP control connection to
  `172.21.0.1:8443`; direct TLS 1.3 validation from the Alpine console returned
  `Verification: OK` for the Central certificate.
- ALPINE2 (`edge-002`) reaches the listener and completes the TLS endpoint
  probe, but its Edge process is currently closing/retrying the control session;
  it is not yet confirmed online at the Central session registry.
- Central was restarted locally so the new read-only Edge status endpoint is
  loaded. Health returned HTTP 200. Production was not restarted or changed.

## Frontend live status verification

- Frontend preview at `127.0.0.1:4173` returned HTTP 200 after the rebuild.
- Devices inventory and device detail both call the authenticated
  `/api/v1/control/status` path through the existing API client, refresh every
  5 seconds, and retain the last good response during revalidation.
- `applyEdgeRuntimeStatus` forces all devices with the affected `edge_id` to
  `offline` when the Central Edge session is offline/expired. The detail view
  exposes the control-channel state and last heartbeat timestamp.
- TypeScript/Vite build PASS (`4540 modules transformed`).

## Redis-backed Edge session recovery

- ALPINE2 diagnostics showed valid identity (`CN=edge-002`), valid dates,
  correct route to `172.21.0.1`, successful TLS 1.3 verification, and repeated
  `HELLO` failures with HTTP 500.
- Central stderr identified the exact cause: Redis connection refused at
  `127.0.0.1:6379` while creating the Edge session. This affected session
  creation, not the Edge certificate or LAN route.
- Started the existing local Redis binary in lab mode on `127.0.0.1:6379`.
  Redis responded `PONG`.
- Live Redis session evidence now shows both records with `ready=1` and fresh
  `last_seen`: `edge-001/alpine1-live` and `edge-002/alpine2-live`.
- Central logs subsequently returned HTTP 200 for `control/hello`,
  `control/ready`, and heartbeat/task polling. Both Edge control channels are
  now active in the local lab.

## Local frontend login fetch failure fixed

- Browser diagnostics showed `OPTIONS /api/v1/auth/login` and other API
  preflight requests returning HTTP 400 while the preview frontend was served
  from port `4173`.
- Root cause: the development CORS allowlist contained only ports `5173` and
  did not include the Vite preview origins `localhost:4173` and
  `127.0.0.1:4173`.
- Updated the Central default configuration and both environment examples to
  include the two preview origins. Production still requires an explicit
  allowlist and was not changed.
- Restarted only the local Central API. Health returned HTTP 200.
- CORS preflight for `http://127.0.0.1:4173` returned HTTP 200 with matching
  `access-control-allow-origin` and credentials enabled.
- Result: the login request is no longer blocked by browser CORS. Edge sessions
  may briefly reconnect during the local Central restart; Redis and the mTLS
  lab gateway remain unchanged.

## Local operator authentication enabled

- After CORS was fixed, the login endpoint correctly returned HTTP 503 because
  `AUTH_OPERATOR_ID`, `AUTH_OPERATOR_PASSWORD_HASH`, and `AUTH_JWT_SECRET` were
  intentionally unset in the local runtime.
- Configured the local-only operator identity `admin` in the ignored root
  `.env`; the password is stored as a PBKDF2 hash and the JWT signing secret is
  generated locally. No cleartext password or token was written to this log.
- Restarted only the local Central API. Login returned an access token with
  role `network-admin`; authenticated `/api/v1/auth/me` returned operator
  `admin`.
- Production credentials and production services were not changed.

## Devices UI Edge-first view

- The Devices page previously rendered the Edge child-device table directly
  under the Edge scope, which made the Edge sessions themselves invisible.
- Added a live `useEdgeRuntimeStatuses` hook using the authenticated
  `/api/v1/control/status` endpoint with the same five-second refresh policy.
- Edge scope now renders one card per active/known Edge session, including
  online/offline state, control readiness, heartbeat age, TTL, boot ID, and
  known-device count. This allows both `edge-001` and `edge-002` to be shown
  simultaneously.
- Child devices are rendered only after the operator presses `Open devices` on
  a specific Edge card; device scope remains isolated by `edge_id`.
- GNS3 and Direct scopes, pagination, and existing device CRUD actions remain
  unchanged.
- Frontend production build PASS: 4540 modules transformed and Vite bundle
  completed successfully. Existing non-blocking Vite chunk-size/optimization
  warnings remain.

## Edge list/table and dedicated Edge detail page

- Replaced the Edge card grid with a table showing Edge ID, status, control
  readiness, boot ID, heartbeat, session age/TTL, and an Open action.
- Added route `/devices/edge/:edgeId` and a dedicated Edge detail view.
- Open now navigates to the new page instead of expanding devices inline.
- The Edge detail view refreshes runtime status and inventory live, shows the
  control-channel metadata, and renders only devices whose `edge_id` matches
  the selected Edge.
- Frontend build PASS: 4541 modules transformed. Existing Vite optimization
  and chunk-size messages remain warnings only.

## GNS3 Edge topology verification

- Live GNS3 controller `TEST-EDGE` was queried at `172.21.0.2`.
- Confirmed active links:
  - `ALPINE1 <-> Switch1 <-> IOSv1`
  - `ALPINE2 <-> Switch2 <-> IOSv2`
  - `MikroTik-CHR3 <-> Switch2`
  - Additional cross-link: `Switch1 <-> Switch2`
- The cross-link means the two lab LANs are currently one connected Layer-2
  domain; this is not yet a clean overlapping-subnet isolation test.
- `Switch1` and `Switch2` are GNS3 `ethernet_switch` nodes without a
  management IP or device protocol. They can be represented as topology
  observations, but cannot be discovered as managed SSH/SNMP devices by Edge.
- Central inventory currently contains stale/mismatched Edge records: Edge
  `edge-001` has IOSv1 plus legacy R1-A and MT1 records, while Edge `edge-002`
  has IOSv2 but no switch record. This must be reconciled with the live lab
  topology before claiming the expected two-device-per-Edge result.
- No GNS3 links or inventory records were changed in this diagnostic step.

## Active local Edge display reconciliation

- The requested local display scope is now explicitly `native-alpine`.
- Added topology-only inventory records for `Switch1`/`edge-001` and
  `Switch2`/`edge-002`, matching the live GNS3 Ethernet Switch nodes. They are
  marked `topology-only` and `warning`; they are not treated as SSH-managed
  devices because the GNS3 switch nodes have no management IP.
- Edge detail filtering now includes only records tagged `native-alpine`, so
  legacy overlap records such as R1-A and MT1 remain preserved in inventory
  but do not appear in the active ALPINE1/ALPINE2 lab view.
- Expected local display after refresh:
  - ALPINE1 / edge-001: Switch1, IOSv1
  - ALPINE2 / edge-002: Switch2, IOSv2
- Central API verification after the inventory update returned exactly two
  active lab records per Edge: `edge-001` = IOSv1 + Switch1 and `edge-002` =
  IOSv2 + Switch2.

## Live Edge inventory audit

- The Edge detail page currently reads child-device identity from Central
  inventory and only overlays the live Edge control-session status. It is not
  yet a live Edge-discovery view.
- Live `/api/v1/discovery` evidence confirms `edge-001` is submitting local and
  ARP observations from Alpine1, but `edge-002` currently has no discovery
  observations in the repository.
- The discovery endpoint exposes raw observations, while the current UI
  adapter expects scan results with a `devices` array; therefore the raw Edge
  observations are not yet rendered as live device rows.
- Do not claim device `online` from inventory alone. The next implementation
  must normalize Edge observations by `edge_id`, apply freshness/TTL and
  reachability semantics, and use inventory only as optional enrichment.

## Live Edge observation path implemented

- Added Central `received_at` stamping for authenticated Edge discovery
  observations. This makes freshness authoritative at Central and tolerates
  clock skew in GNS3 Alpine nodes.
- Added authenticated `GET /api/v1/discovery/live?edge_id=...`, returning
  observation source, state, age, TTL, and `fresh` status.
- Edge detail now consumes this live endpoint every five seconds. Inventory is
  used only to enrich the row; managed devices are marked online only when a
  fresh ARP/ICMP/SSH/SNMP/API observation exists. Topology-only switches remain
  warning rather than falsely becoming SSH-online.
- Backend compile and frontend build PASS (`4541 modules transformed`).
- Current lab evidence still has no fresh observation after the Central restart
  (`edge-001` has historical observations; `edge-002` has none). The Alpine
  Edge runtime must be started with its local discovery customer/site settings
  enabled so the next scheduled observation is submitted. Until then the UI
  correctly shows the managed devices as offline/unknown instead of claiming
  they are live.

## Alpine discovery profile preparation

- Extended `edge/installers/alpine/ainet-edge.confd` for ALPINE1 with the
  explicit discovery scope `cust-a/site-a`, 60-second interval, and 300-second
  observation TTL.
- Added `edge/installers/alpine/ainet-edge-edge002.confd.example` for ALPINE2
  with `edge-002`, `cust-b/site-b`, the same bounded interval/TTL, and the
  existing mTLS/keystore/journal paths.
- These profiles enable the existing Edge-local discovery scheduler; they do
  not create a second scanner or bypass Central policy. They must be copied to
  the respective Alpine nodes and restarted there before live observations can
  be claimed.
- The current GNS3 topology has a `Switch1 <-> Switch2` cross-link and
  MikroTik attached to Switch2. Therefore ALPINE2 can report IOSv2 and
  MikroTik observations when their IP/MAC entries are present; the GNS3
  Ethernet Switch itself has no management IP and remains topology-only.

## Verification checkpoint

| Check | Command | Result |
|---|---|---|
| Frontend type/build | `npm.cmd run build` | PASS — 4541 modules, exit 0 |
| Edge runtime tests | `go test ./...` from `edge/` | PASS — all packages |
| Alpine1 profile | inspect `edge/installers/alpine/ainet-edge.confd` | PASS — customer/site discovery flags present |
| Alpine2 profile | inspect `edge/installers/alpine/ainet-edge-edge002.confd.example` | PASS — profile added |
| Live Central freshness | `GET /api/v1/discovery/live?edge_id=...` | PASS - both Edge IDs online and fresh observations received |

## Remaining handoff

1. Copy the ALPINE1 profile to `/etc/conf.d/ainet-edge`, then restart the
   service.
2. Copy the ALPINE2 example to its `/etc/conf.d/ainet-edge`, then restart the
   service with its enrolled `edge-002` certificate.
3. Wait one discovery interval and verify Central live observations for both
   Edge IDs. Confirm IP/MAC/vendor fields in the Edge detail page.
4. If an observation is absent, inspect the Alpine interface/ARP state and the
   Edge service log; do not mark the live gate complete from Central inventory.

## Live Alpine acceptance

- The initial ALPINE2 binary was stale and rejected the discovery flags. A
  Windows-built binary was also rejected by Alpine with `Exec format error`; it
  was replaced with a cross-compiled `linux/amd64` build.
- The final binary was delivered by temporary HTTP download, not base64 through
  the interactive console. SHA-256 verified on both sides as
  `22ca9fa2dc9aa7778d8feafa6e93e02e603faff56afc27a318ad8c77e6e207c8`.
- ALPINE1 and ALPINE2 now run with discovery scopes `cust-a/site-a` and
  `cust-b/site-b`, respectively. Both control sessions are `ready=true,
  online`.
- Central live endpoint evidence after the 60-second discovery interval:
  - `edge-001`: 11 observations, 8 fresh.
  - `edge-002`: 10 observations, 10 fresh, including
    `192.168.1.1 / 0c:22:59:a8:00:00` (IOSv2) and
    `192.168.1.2 / 0c:e7:ee:b5:00:00` (MikroTik-CHR3).
- Added `mt3-native-edge002` inventory enrichment so Edge-002 detail can map
  the live IP/MAC observation to MikroTik. `Switch2` remains topology-only
  because the GNS3 Ethernet Switch has no management IP.
- Temporary workstation HTTP server was stopped after download. No device
  credentials or private keys were written to this session log.

## Final status and handoff

- Status: PARTIAL/LOCAL-LIVE-PROVEN. The live Alpine discovery slice is proven
  in GNS3; production readiness is unchanged and must not be inferred from
  this lab result.
- Next UI check: refresh the frontend with Ctrl+F5, open Devices -> Edge, open
  `edge-002`, and inspect the live observation table plus enriched device rows.
- Keep the GNS3 Switch1/Switch2 cross-link documented; it is not a valid
  isolated overlapping-subnet acceptance topology.

## ALPINE1 binary compatibility checkpoint

- ALPINE1 was tested with the new `linux/amd64` binary
  `22ca9fa2dc9aa7778d8feafa6e93e02e603faff56afc27a318ad8c77e6e207c8`.
- The process started and retained discovery flags, but its control hello
  returned intermittent HTTP 500/EOF while ALPINE2 remained healthy.
- ALPINE1 was restored to the previously proven discovery-capable binary
  `ainet-edge-linux-telemetry2`, SHA-256
  `3ba534681bc7c4ea2bee930edea5599b67e5b09ea7c4439d12d6ddf4db303ba6`.
- After recovery, ALPINE1 returned `ready=true/online` and continued sending
  fresh observations. This is a compatibility containment decision, not a
  production release decision; the new binary needs a separate Edge-001
  handshake regression investigation before rollout.

## Edge list session deduplication

- The control status endpoint intentionally exposes individual ephemeral Redis
  sessions, including historical/offline records until their TTL expires.
- The Devices Edge list was incorrectly rendering every session as a separate
  Edge. Extended `loadBackendEdgeStatuses()` to group by `edge_id`, prefer a
  ready/online session, select the newest heartbeat, and return only active
  Edge identities to the UI.
- This leaves Redis/task routing semantics unchanged and fixes the operator
  view to show only the two active lab Edges: `edge-001` and `edge-002`.
- Frontend build after the change: PASS, 4541 modules, exit 0.

## Edge-001 IOSv1 live status correction

- IOSv1 was initially shown `offline` because ALPINE1's ARP cache had no
  `192.168.1.1` entry; the Edge discovery collector correctly did not infer
  reachability from Central inventory alone.
- ALPINE1 was tested with two successful pings to `192.168.1.1`, producing MAC
  `0c:f5:2c:51:00:00` in the local neighbor table.
- After the discovery interval, Central reported `edge-001` with 9 fresh
  observations including the IOSv1 IP/MAC. The UI should now show IOSv1
  online after refresh.
- Switch1 remains warning/topology-only by design because the GNS3 Ethernet
  Switch has no management IP or Edge-managed protocol endpoint.

## Devices page scope simplification

- Removed the GNS3 scope card and project selector from the Devices page.
- Devices page now exposes only `Edge Devices` and `Direct Devices`; GNS3
  integration remains available in its dedicated lab/topology surfaces.
- Default Devices scope is now Edge so the operator immediately sees the two
  active Edge identities.
- Frontend build after the change: PASS, 4541 modules, exit 0.

## Edge table telemetry enrichment

- Extended the live Edge status adapter and Devices -> Edge table with OS,
  management IP, MAC address, CPU, memory, and latency columns.
- Management IP and MAC are derived from fresh `source=local` Edge discovery
  observations when the control-status payload does not provide them.
- OS and resource/latency metrics are accepted from optional Central control
  telemetry fields (`os`, `management_ip`, `mac_address`, `cpu_percent`,
  `memory_percent`, `latency_ms`). The current heartbeat contract does not yet
  emit those metrics, so the UI renders an explicit `—` rather than invented
  values until telemetry is implemented.
- Existing Edge session deduplication and live polling remain unchanged.
- Verification: `npm.cmd run build` PASS; TypeScript/Vite build completed with
  4541 modules. Only existing Rolldown/plugin and large-chunk warnings remain.

## Live Edge host telemetry contract

- Extended `PresenceHeartbeat` with OS, management IP, MAC address, CPU
  percentage, memory percentage, and Central round-trip latency.
- Go Edge now collects non-secret host telemetry from `/etc/os-release`, local
  interfaces, `/proc/stat`, and `/proc/meminfo`. Latency is measured from the
  authenticated heartbeat request and reported on the next heartbeat.
- Central stores telemetry in the Edge session registry, including Redis, and
  exposes it through `/api/v1/control/status`. Existing session TTL and
  fail-closed routing behavior are unchanged.
- Added a Central contract test: `18 passed` for Edge control and resilient
  session tests.
- Built Linux/amd64 binary for lab rollout:
  `tmp/ainet-edge-linux-telemetry3`, SHA-256
  `aebca3c42e2d3bf94504f8833293510e8f4b256ee7f415112eb994e498e45817`.
- The binary has not been deployed to Alpine in this session. Until ALPINE1
  and ALPINE2 are updated and restarted, the UI may continue showing `—` for
  telemetry fields. No credentials or private keys were logged.

## Telemetry lab rollout checkpoint

- `ainet-edge-linux-telemetry3` was transferred over temporary HTTP to both
  Alpine consoles with SHA-256 verification and service restart.
- The new Edge build did not establish a stable control session in the live
  lab; Central returned intermittent 500/EOF and the prior runtime also
  exposed stale 422/403 records. The Central API and mTLS gateway were
  restarted with the updated source, but the handshake regression remained
  for Edge-001.
- To avoid leaving the lab in a degraded state, ALPINE1 was restored to the
  proven `telemetry2` binary (`3ba534...303ba6`) and ALPINE2 to the proven
  discovery binary (`22ca9f...e207c8`), both verified by SHA-256. Edge-002
  returned online; Edge-001 still requires a separate handshake investigation.
- Telemetry code remains in the repository and is not marked live-proven.
  The next safe action is to reproduce the new heartbeat against an isolated
  Central test endpoint, then roll out only after HELLO/READY and heartbeat
  compatibility tests pass.

## Telemetry rollout completed

- Root cause was fixed in `deploy/mtls/revocation_gateway.py`: the gateway
  previously forwarded a fragmented upstream response after reading only one
  socket chunk, causing a valid `Content-Length` header with an incomplete
  body and Edge `unexpected EOF`. The gateway now reads complete headers and
  body by `Content-Length`; chunked responses remain rejected fail-closed.
- Added a regression test for fragmented upstream responses. Gateway tests:
  `4 passed`.
- Central and mTLS gateway were restarted, direct mTLS HELLO returned HTTP 200
  with a complete WELCOME response, and both Alpine Edges were reinstalled
  with telemetry binary SHA-256
  `aebca3c42e2d3bf94504f8833293510e8f4b256ee7f415112eb994e498e45817`.
- Live Central status evidence after rollout:
  - `edge-001`: online, Alpine Linux v3.18, management IP `192.168.42.188`,
    MAC `0c:b4:1b:dc:00:00`, CPU about 3.47%, memory about 50.30%, latency
    about 15.7 ms.
  - `edge-002`: online, Alpine Linux v3.18, management IP `192.168.42.124`,
    MAC `0c:ca:16:70:00:00`, CPU about 3.40%, memory about 50.48%, latency
    about 15.0 ms.
- Telemetry is now live-proven in the local GNS3 lab. Production readiness is
  unchanged and must not be inferred from this lab evidence.

## Device SNMP telemetry preparation

- Cisco IOSv1 was configured through its GNS3 console with a lab-only
  read-only SNMPv2c community and lab location, then saved to startup
  configuration. The community value is intentionally omitted from this log.
- MikroTik CHR3 console was reached, but its login rejected the locally
  available credential and the console returned to the login prompt. No
  MikroTik configuration change was applied and no further password guesses
  were attempted.
- An Alpine-side `snmpget` validation could not run because the Alpine image
  does not contain `net-snmp-tools`; this is an environment/package gap, not
  proof that Cisco SNMP polling works.
- Edge host telemetry is live. Device-level SNMP polling (CPU/memory and
  device RTT) remains unimplemented until the SNMP transport/credential
  contract is added and the MikroTik credential is corrected. It must not be
  marked complete based on the Cisco configuration alone.

## MikroTik CHR3 credential and SNMP retry

- The replacement MikroTik node is `MT1` on GNS3 console port `5012`.
- The node was reachable and already presented an authenticated RouterOS
  prompt; the supplied admin credential was applied locally without recording
  its value.
- SNMP is enabled and the lab location is configured. The read-only SNMP
  community already existed, so the duplicate-add attempt was not treated as
  a failure.
- No credential value was written to this session log, source code, or
  evidence artifacts.
- Device-level SNMP polling remains pending until Alpine has SNMP tooling and
  the Edge SNMP transport/credential contract is implemented.

## Follow-up validation on replacement MikroTik

- GNS3 currently maps replacement MikroTik `MT1` to console port `5012`.
- A read-only SNMP setup was applied successfully; a repeated community-add
  returned the expected duplicate-name error, while SNMP status showed enabled.
- The admin password was set locally using the operator-provided value; the
  value is intentionally absent from all repository artifacts.
- An attempt to install Alpine `net-snmp-tools` on both Edge consoles did not
  complete before the console session closed, and `snmpget` was not present on
  the follow-up check. Device SNMP polling is therefore still not proven.
- Follow-up confirmed Alpine v3.18 has only the `main` repository active by
  default; `net-snmp-tools` is supplied by `community`. The community entry
  was enabled on ALPINE1, but both repository indexes returned temporary fetch
  errors from the lab network, so package installation remains incomplete.

## Edge SNMP transport slice

- Added `edge/internal/snmp/client.go` with a bounded SNMPv2c polling contract
  for system description, system name, uptime, RTT, and optional profile OIDs
  for CPU/memory. The resolved community is accepted only as local runtime
  configuration and is not part of task or telemetry payloads.
- Added unit coverage in `edge/internal/snmp/client_test.go` for normalized
  value conversion and missing local credential rejection.
- `go test ./...` passed and `go build ./cmd/ainet-edge` passed.
- A Linux build was repeated after the SNMP package addition; its SHA-256
  remained identical to the deployed telemetry binary because the package is
  not yet wired into the Edge runtime path. It was not falsely promoted as a
  live SNMP-enabled release.
- Live device polling is not yet claimed: Alpine package repository access is
  still unreliable and the new client is not yet wired to the periodic device
  inventory scheduler or Central telemetry endpoint.

## SNMP capability wiring and Alpine deployment

- Added read-only capability `device.read.telemetry` to the Central/Edge
  contract and Edge control validation.
- Edge resolves the SNMP community from its local credential keystore and
  returns normalized SNMP facts; no SNMP secret is accepted in the task
  envelope.
- Added capability registry and request validation for bounded optional OID
  profile parameters.
- Edge tests passed (`go test ./...`); Central contract/capability tests passed
  (`7 passed`).
- Built Linux amd64 binary with SHA-256
  `a3908ce351137d10f778cfcb5e1edb7a1ac28ba3403230a10bc5b18275e0dfdc`.
- Transferred by temporary local HTTP and activated successfully on ALPINE1
  and ALPINE2; both OpenRC services report started and the expected hash was
  verified on each Edge.
- Live SNMP device polling remains pending until device telemetry tasks are
  issued with local SNMP community references and vendor OID profiles.

## SNMP capability runtime deployment

- Added `device.read.telemetry` to the Edge envelope validation, capability
  advertisement, Central request schema, capability registry, and dispatch
  handshake.
- The Edge handler resolves `credential_ref` locally and uses only the local
  SNMP community; task payloads contain target metadata and bounded OID
  profile values, never secrets.
- Edge regression passed and Central capability/contract tests passed.
- Linux binary was rebuilt and transferred over temporary HTTP to ALPINE1 and
  ALPINE2; each Edge verified SHA-256
  `a3908ce351137d10f778cfcb5e1edb7a1ac28ba3403230a10bc5b18275e0dfdc` and
  restarted successfully.
- Live dispatch still requires a keystore entry containing the SNMP community
  and a Central task carrying the approved vendor OID profile; this is the
  next test gate.
- Added regression coverage for `device.read.telemetry`: bounded OID profile
  parameters are accepted, while `community` and `snmp_community` payload
  fields are rejected as secrets. Central contract/capability tests now pass
  (`8 passed`); Edge full test suite remains passing.
- Central local API was restarted from the backend working directory so the
  new contract is loaded; port `8000` is listening again.
- Added the lab SNMP community reference to the local keystores on ALPINE1
  and ALPINE2 using an on-node backup-first update; the keystore backups use
  the `.bak-snmp` suffix and remain outside the repository. Both Edge services
  restarted successfully. No community value was recorded here.
- Live mTLS probe confirmed `HELLO` and `READY` through the active gateway
  using the runtime Edge identity. A direct `/control/task` probe returned
  404 because current Central dispatch is intentionally created through
  `/api/v1/tasks/capability` and then polled by Edge; no orphan task was
  created. The next live gate is an authenticated Central capability request.
- The live telemetry probe was stopped at that gate: direct mTLS identity and
  session establishment succeeded, but task creation must use the authenticated
  Central operator API. No live SNMP task was issued without an operator token.

## UI telemetry action and live gate follow-up (2026-09-09)

- The authenticated Agent page was inspected after operator login. A chat request
  failed before producing an agent response, so no configuration action was
  attempted through chat.
- Extended the existing Edge detail page with a read-only `Poll SNMP telemetry`
  action. It uses the existing authenticated `apiRequest` path and dispatches
  only `device.read.telemetry`; no secret or community value is entered in the
  browser.
- Added the Central frontend capability client and rebuilt the frontend
  successfully. TypeScript passed; Vite completed with existing bundle-size and
  dependency optimization warnings.
- The first authenticated UI dispatch reached Central and Edge and was recorded
  as a TaskAttempt, but failed closed with `SNMP_CREDENTIAL_NOT_CONFIGURED` for
  the Edge-local credential reference. This proves routing/auth/task plumbing,
  but not SNMP data collection.
- Rebuilt the Edge binary with the current SNMP credential model. Transfer to
  ALPINE1 was attempted through the GNS3 console, but the console did not return
  the expected hash/status output, so deployment is not claimed complete.
- Next action: free ALPINE1's console session, redeploy the rebuilt binary with
  hash verification, then repeat the authenticated UI poll and capture the
  normalized SNMP result. No secrets are recorded here.
- Follow-up completed: the first transfer exposed a Windows-format binary and
  failed with `Exec format error`. The binary was rebuilt explicitly for
  Linux/amd64, transferred successfully, SHA-256 verified on ALPINE1, and the
  OpenRC service returned `started`.
- The authenticated UI poll was retried after redeployment. A final normalized
  SNMP result is still pending; the earlier attempt remained blocked by the
  Edge-local credential reference and no secret value was logged.
- Read-only inspection of ALPINE1's keystore confirmed the active references
  include `r1-lab` and `mt1-lab`, with one non-empty community field; the UI
  action was corrected from the obsolete `a-r1` reference to `r1-lab` and the
  frontend bundle was rebuilt and preview service restarted.
- The post-rebuild browser click did not create a new audit task, so the next
  debugging step is the UI event/target binding rather than another Edge
  binary transfer. No device mutation was performed.
- Changed the Edge detail page to automatically request the safe
  `device.read.telemetry` capability when the Edge is online and a managed
  device target is present. Refresh cadence is bounded to 60 seconds; the
  manual poll button remains available. This is a UI convenience layer only;
  production continuous telemetry should still be Edge-scheduled and must not
  turn PostgreSQL into a high-frequency heartbeat sink.
- TypeScript validation passed with `npx tsc --noEmit`.
- Browser verification after the rebuilt preview confirmed the Edge detail page
  renders the automatic telemetry path and keeps the manual button only as an
  operator fallback. The authenticated live dispatch succeeded through
  `edge-001` to IOSv using the local credential reference; normalized response
  included `R1.lab.local`, Cisco IOS/IOSv system description, uptime ticks, and
  measured latency. No device mutation was performed.
- Automatic polling is intentionally bounded to an immediate request on page
  load when the Edge is online plus a 60-second refresh interval. This avoids
  requiring a click while preventing an uncontrolled high-frequency task loop.
- Fixed the empty CPU/Memory/Latency cells: the UI now sends bounded vendor
  SNMP OID profiles for Cisco and MikroTik and merges the returned telemetry
  into the matching Edge device row. Latency is populated from `latency_ms`;
  CPU and memory populate when the configured vendor OIDs return numeric data.
- TypeScript validation passed after the mapping change. No credentials or
  SNMP community values were recorded.
- Removed the raw `Latest device telemetry` JSON card from the Edge detail UI
  at operator request. Background telemetry polling and table metric mapping
  remain active; raw task output is kept in the existing audited task path.
- Extended Edge detail to materialize fresh Edge discovery observations as
  device rows when Central inventory has no matching `native-alpine` record.
  Each discovered row is scoped by `edge_id` and MAC/IP context, and changes
  to `offline` when the Edge is offline or the observation expires. Frontend
  production build passed after this change.
- Extended the same telemetry path to Edge-002 discovery targets. When no
  inventory record exists, the first scoped discovered target is polled using
  the Edge-local lab credential reference and vendor OID profile; its returned
  metrics are merged into the matching row. Other discovered rows remain
  offline/unknown for CPU and memory until their own SNMP identity and policy
  credential mapping are configured. No secrets were recorded.
- Enabled read-only SNMP on the current Edge-002 Cisco IOSv console and
  confirmed SNMP was already enabled on the current MikroTik MT1 console; the
  duplicate community entry was left unchanged. Edge-002's actual keystore
  contains `b-r1`, so the UI mapping was corrected to that local reference.
- Frontend TypeScript and production build passed. Follow-up live tasks still
  report `SNMP_POLL_FAILED`, so Edge-002 CPU/memory/latency are not claimed as
  live evidence yet; the remaining check is SNMP response reachability/OID
  compatibility from the running Edge process.
- MT1 console inspection confirmed it had no IP address on the connected
  interface. Assigned the lab management address `192.168.1.2/24` to `ether1`
  and verified MT1 SNMP remained enabled. Bidirectional reachability between
  MT1 and ALPINE2 then passed with zero packet loss. The UI now prioritizes the
  Edge-002 MikroTik inventory target for its automatic telemetry request.
- Edge-002 frontend build passed after the target-priority adjustment. Live
  SNMP metric success remains subject to the running Edge process consuming the
  current local keystore reference and returning compatible MikroTik OIDs.
- Corrected the frontend again so telemetry polling is multi-target: all
  managed Cisco/MikroTik devices on an Edge are requested in parallel and each
  result is merged by `device_id`; Cisco is no longer replaced by the MikroTik
  target. TypeScript and frontend production build passed. No raw telemetry
  JSON is rendered.
- Edge-002 task inspection confirmed MikroTik system facts and latency succeed,
  while CPU/memory fields were absent and therefore rendered as safe zero
  fallbacks. Corrected the MikroTik memory OID profile to use total memory
  rather than free memory; CPU and memory must be reverified against the
  running Edge binary/device MIB response.
- Restricted `Add Device` and `Import CSV` management actions to the Direct
  Devices table. Edge detail tables keep only the policy-scoped `Discover
  Devices` action and remain discovery/inventory views without direct-device
  add/import controls.
- Tightened the Devices filter layout with a wider search field and bounded
  filter columns so controls do not spread excessively across the page.
  TypeScript and frontend production build passed.
- Further tightened the desktop filter grid to fixed-width columns aligned to
  the left, eliminating the remaining excessive horizontal spread caused by
  fractional grid columns.
- Compactened the Devices toolbar further: reduced header/filter gaps, reduced
  filter widths, and aligned Add/Discover/Import buttons in one compact group.
- Restored the original Discover Devices button sizing and moved the compact
  filter layout to the desktop breakpoint with smaller fixed tracks and tight
  spacing.
- Replaced the fixed desktop filter grid with a compact flex-wrap toolbar so
  Search and all dropdowns use uniform minimal spacing without empty grid
  tracks.
- Live MT1 polling still showed `0%` CPU and `0%` memory while latency was
  valid, confirming connectivity and SNMP facts but not the vendor metrics.
  Corrected the MikroTik profile to the RouterOS MIKROTIK-MIB scalar OIDs:
  `mtxrHlProcessorLoad` (`...14988.1.1.3.11.0`) and
  `mtxrHlMemoryUsage` (`...14988.1.1.3.12.0`). No secrets were recorded.
  Frontend TypeScript and production build passed; live re-verification is
  still required after the browser loads the new bundle.
- Follow-up live inspection showed MT1 was being represented only as an ARP
  discovered `Other` row, so the UI sent no MikroTik OID profile and could
  only display latency. Added the MT1 MAC OUI prefix `0c:28:e5` to the
  discovered-vendor normalizer so the telemetry request selects MikroTik
  CPU/memory OIDs. No secrets were recorded.
- Live task evidence then exposed an Edge dispatch bug: the control handler
  routed `device.read.telemetry` through the SSH facts executor instead of the
  SNMP executor. Fixed the Go handler, cross-compiled Linux AMD64, deployed
  to ALPINE2, and verified the service is started with the new binary hash.
  The subsequent task still returned only RouterOS facts plus latency and no
  CPU/memory fields, so the remaining blocker is device-side OID availability
  or the active Edge session path; CPU/memory are not claimed as verified.
- Architecture boundary reaffirmed: SNMP polling and credential resolution
  belong to Edge; Central only authorizes/routes the capability and exposes
  the normalized result through its API; Frontend consumes typed fields for
  tables. Browser inspection is QA-only and is never an application data
  source. Edge detail does not render raw telemetry JSON.
- MT1 console supplied authoritative RouterOS resource OIDs: CPU load via
  HOST-RESOURCES-MIB `1.3.6.1.2.1.25.3.3.1.2.1`, used memory via
  `1.3.6.1.2.1.25.2.3.1.6.65536`, and total memory via
  `1.3.6.1.2.1.25.2.3.1.5.65536`. Updated Central, UI, and Edge defaults;
  cross-compiled and deployed Edge-002. Live polling still returns facts and
  latency but no CPU/memory fields, so metric availability remains unverified.
- Built the current Edge as Windows AMD64 at `tmp/edge-windows-test/ainet-edge.exe`
  and verified its CLI starts with the expected options. Added a test launcher
  that requires local CA/certificate/key/keystore files and never embeds
  secrets. Full Windows control-channel installation remains pending until
  approved Windows Edge identity files are supplied; no secrets were logged.
- Created a separate lab identity `edge-windows-001` signed by the local lab
  CA, copied only the CA certificate and lab keystore into the Windows test
  package, and started the Windows Edge process with the local Central URL.
  The process is running; Central session visibility/control-channel success
  still requires a live handshake check and is not claimed as passed. Private
  key contents and credential values were not logged.
- Windows recognition verification completed: the first launcher target
  `https://172.21.0.1:8443/api` was the GNS3-side gateway and closed the
  connection because its Central upstream was unavailable from this host.
  The Windows-local Central mTLS gateway at
  `https://127.0.0.1:8443/api` was selected instead, while TLS SNI/Host
  remains `central`. The Windows launcher was updated and restarted.
  A certificate-verified TLS 1.3 probe using the same CA/client identity
  received HTTP 200 `WELCOME` and a Central session for `edge-windows-001`;
  the Edge process is running with that endpoint. This proves Central accepts
  the Windows Edge identity in the local lab. No secret material was logged.
- Extended the Windows runtime path: CPU and memory now use bounded fixed
  PowerShell/CIM queries on Windows, while the existing interface collector
  supplies the primary IPv4 and MAC. Windows discovery now reads the local
  ARP cache without scanning and the launcher enables scoped discovery for
  `cust-windows/site-windows` every 15 seconds. Linux test suite passed with
  `go test -race ./...`; Windows AMD64 binary rebuilt. Restarted Edge and
  observed `control session ready` for `edge-windows-001`. Central-side live
  UI refresh is still required to confirm the resulting observation rows;
  no raw credentials or private key material was logged.
- Added credential-free passive enrichment for Edge discovery: Windows ARP
  observations now attempt bounded reverse-DNS hostname resolution and carry
  OUI-based `vendor_hint`, inferred `platform_hint`, device-class hint, and
  confidence metadata. Unknown model/platform values remain explicitly
  unknown; authoritative model/platform still requires SNMP/SSH/API. Linux
  tests remain green and the Windows AMD64 binary was rebuilt/restarted.
- Follow-up UI verification found the running Vite preview was serving the
  previous `dist` bundle while concurrent builds were still active. Stopped
  only the stale build processes, completed one clean `npm.cmd run build`,
  confirmed the new Edge detail bundle contains `platform_hint` and
  `Unknown (inferred)`, and restarted preview on port 4173. The Windows Edge
  process remains active with a Central-ready session.
- Diagnosed an apparent all-offline state: the running backend had the old
  discovery enum and rejected every batch containing the new `service` source
  with HTTP 422. Restarted Central after the schema update, restarted the
  Windows Edge to establish a fresh session, and observed only the expected
  startup deferral plus `control session ready`; no new 422 rejection was
  recorded. The Edge now resubmits ARP and service observations normally.
- Added an Edge-native bounded service scanner in Go. It probes only up to 64
  IPs already observed in the local ARP cache, checks a fixed small port set
  with 700ms connection and 250ms banner limits, caps workers at eight, and
  emits `service` observations with service/banner/platform hints and
  `REACHABLE` state. It does not invoke nmap, expand CIDRs, use credentials,
  or scan arbitrary targets. Central discovery schema now accepts the service
  evidence and Edge detail merges it into the corresponding ARP device row to
  avoid duplicates. Linux `go test -race ./...` passed; Windows binary was
  rebuilt and restarted with `--discovery-service-scan` enabled. CDP/LLDP
  packet parsing remains a separate evidence source and is not claimed by
  this slice.
- Improved the internal service scanner's evidence parsing: bounded HTTP
  header/SSH banner reads now produce model hints for RouterOS, Cisco, D-Link,
  Windows, and printers when their banners identify them. The scanner remains
  credential-free and conservative; exact model/serial is not fabricated when
  a device does not expose it. Windows binary rebuilt and restarted, with
  Central session ready observed again.
- Added the `Open Ports` field to the shared device status table. Edge detail
  now groups fresh Edge-native `service` observations by management IP and
  attaches typed port/service entries to the matching device row, including
  managed inventory devices and newly discovered devices. Service evidence is
  deduplicated and sorted by port; raw observation JSON is not displayed.
  Frontend TypeScript/Vite production build passed. No credentials, secrets,
  or application-source runtime state were changed.
- Fixed multi-port observation identity in the Edge publisher. The previous
  digest used only the Edge ID and IP/subject, so Central's idempotent upsert
  retained only the last service for a device. The identity now includes the
  observation source and attributes, preserving each distinct port while
  remaining idempotent across periodic scans. Expanded the bounded service
  probe set with common FTP, SMTP, DNS, POP3, NetBIOS, IMAP, SMB, AFP, IPP,
  HTTP-alt, HTTPS-alt, and existing network-management ports; concurrency is
  capped at 16 and targets remain limited to ARP-observed IPs. Edge Windows
  binary rebuilt and restarted with the same local mTLS/keystore configuration.
  `go test -race ./...` passed.
- Consolidated the device-table action controls into one overflow (`...`) menu.
  Existing Open, SSH, Run command, Configure, Backup, Edit, and Delete actions
  remain available, while the table no longer renders a wide row of buttons.
  Frontend TypeScript/Vite build passed; only the existing Vite dependency
  optimization and large-chunk advisories remain.
- Fixed `Open device` for live Edge-discovery rows. Such rows are not always
  persisted in Central inventory, so the action now passes the typed live
  device snapshot to the detail route; the detail page uses it as a safe
  fallback when the inventory endpoint has no matching record. Managed
  inventory devices continue using the normal Central detail response.
  Frontend TypeScript/Vite build passed.
- Simplified Edge discovery identity labels in the UI: RouterOS service ports
  (8291/8728/8729) now map to vendor MikroTik and model `RouterOS`; ports
  139/3389/5985 map to a Windows platform/model hint. Verbose `(inferred)`
  and `(model unavailable)` suffixes are removed from displayed model values,
  while the underlying evidence and conservative inference behavior remain
  unchanged. Frontend TypeScript/Vite build passed.
- Diagnosed the Windows Edge all-offline state after expanding service
  discovery: the mTLS gateway's 64 KiB request ceiling rejected the larger
  bounded observation batch and the Edge reported EOF on heartbeat/discovery.
  Raised the gateway ceiling to a bounded 512 KiB, restarted it with an
  explicit backend `PYTHONPATH`, and confirmed the gateway health listener,
  zero current gateway errors, and renewed Edge control readiness. Existing
  5-second UI status refresh and 15-second Edge heartbeat/discovery schedules
  remain unchanged.
- Fixed the remaining oversized discovery-batch path. Central accepts at most
  512 observations per request; Edge now submits larger bounded scans in
  480-observation chunks. Rebuilt/restarted the Windows Edge and confirmed a
  ready Redis session with refreshed heartbeat and discovery timestamps. The
  mTLS gateway reports zero current errors. Historical EOF lines in the local
  Edge diagnostic log are retained as prior evidence and are not current
  failures.
- Investigated the reported all-offline Windows Edge view. Redis showed the
  Windows session ready with a current heartbeat, and the discovery store
  contained fresh Windows Edge observations. The 404 capability requests were
  historical during backend reload; later capability requests returned 200.
  Restarted the local Vite preview on port 4173 so the browser receives the
  current bundle and live polling code. No device status was forced to online;
  reachability remains based on fresh Edge evidence.
- Rechecked the active runtime: FastAPI OpenAPI contains
  `POST /api/v1/tasks/capability`; an unauthenticated probe returns `401`, and
  recent authenticated capability requests return `200`. Redis shows the
  Windows Edge session ready with a renewing heartbeat. The displayed `404`
  is from an older browser-console request during backend reload, not the
  current route state.
- Reproduced the issue in a separate Chrome tab. The Edge runtime was `online`
  and the live observation table showed fresh observations, while the device
  table preferred an older Central inventory row with `offline` status during
  duplicate collapse. Updated the Edge detail view to normalize IP/MAC matching
  and prefer live `online` observations before deduplicating rows. Rebuilt the
  frontend successfully; browser verification now shows discovered devices as
  `online` with `live Edge (arp)`, and no current browser console errors.
- Reduced duplicate noise in the `Live Edge Observations` summary. Repeated
  polling and multiple service ports for one IP are now collapsed to one row per
  source/IP in the UI. Per-port evidence remains retained by Central and is
  still rendered in the device table's Open Ports column. TypeScript check passed.
- Fixed automatic telemetry polling for discovery-only devices. The Edge detail
  page now sends `device.read.telemetry` only for inventory-managed devices with
  a Central record and credential reference; unregistered discovery observations
  are displayed without generating invalid task requests. This removes the
  repeated `POST /api/v1/tasks/capability` 404 (`Device not found`) errors while
  preserving the distinction between OBSERVED and MANAGED. TypeScript/Vite
  production build passed.
- Polished the Devices page visual hierarchy: improved page spacing, icon-led
  heading, compact device count badge, clearer scope cards for Edge/Direct,
  live-refresh indicator, and a framed Active Edge connectors section. The wide
  Edge table now scrolls cleanly on small screens with stable non-wrapping
  identity/metric cells and lighter hover states. TypeScript check and Vite
  production build passed; browser smoke found the updated labels with no
  console errors.
- Polished the Direct Devices table consistently with the Devices page: rounded
  card treatment, subtle header background, compact result count, clearer device
  identity (hostname plus device ID), consistent filter/button spacing, stable
  column widths, and row hover feedback. TypeScript check and Vite production
  build passed.
- Fixed the Direct Devices action menu scroll lock by rendering its dropdown as
  non-modal. Opening the `...` menu no longer blocks page/table scrolling while
  the action list remains keyboard and pointer accessible. TypeScript check
  passed.
- Shortened the secondary identity label for discovery-only Edge devices. The
  long generated discovery ID is no longer rendered in the table; it displays
  `Edge Discovery`, while the full ID remains available through the element
  title and runtime data. TypeScript check passed.
- Refined the Direct devices table header with context-aware description and
  compact Online/Warning/Offline counters based on the currently filtered
  rows. Edge detail now correctly uses the `Edge devices` title instead of
  inheriting the Direct devices label. TypeScript check and Vite production
  build passed; authenticated browser smoke confirmed the Direct devices
  title, description, counters, and existing action controls.
- Matched the `Discover Devices` toolbar button size to `Add Device` by using
  the same small outline button treatment in the Direct devices view.
