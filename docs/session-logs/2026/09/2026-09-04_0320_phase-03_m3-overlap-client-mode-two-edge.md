# Work Session: m3-overlap-client-mode-two-edge

## Session Metadata

- Session ID: `20260904-032011-phase-03-m3-overlap-client-mode-two-edge`
- Date/Time Started: `2026-09-04T03:20:11+08:00`
- Date/Time Closed: `2026-09-04T03:50:00+08:00`
- Implementation Phase: `phase-03`
- Status: `PARTIAL`
- Operator: `opencode`
- Branch: `main`
- Starting Worktree: `dirty`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Prove the Milestone 3 overlapping-subnet model with **two Edge processes** that
Central can distinguish, using the Edge **client-mode (dial-out to Central)**
approach, avoiding the fragile GNS3 host-tap / ubridge data-plane wiring.

## Scope

### In Scope
- Stand up an mTLS Central (HTTPS on 8443).
- Generate two Edge identities (edge-a, edge-b) signed by the same CA.
- Run two Edge client-mode processes dialing the Central.
- Verify Central distinguishes edge-a from edge-b (multi-Edge enrollment).

### Out of Scope
- Live device SSH execution through both Edges (client-mode does not execute
  device tasks; that requires server-mode `--control-listen`, which is blocked
  by the GNS3 host-tap/LAN reachability + project-open issues).

## Initial Findings

- Edge client-mode (`--control-url`) registers presence (HELLO/READY/heartbeat)
  with Central. It does **not** receive/execute device tasks — that is the
  server-mode (`--control-listen /v1/control/task`) role.
- The Central FastAPI already exposes `/api/v1/control/hello|ready|heartbeat` for
  Edge dial-in (client-mode), enforced by `X-Client-Edge-ID` identity.

## Work Log

### 03:20 - session opened

### 03:25 - stand up mTLS Central
- Started `uvicorn app.main:app --ssl-keyfile central.key --ssl-certfile central.crt`
  on `https://0.0.0.0:8443` (PID 48168). Log: active.

### 03:28 - generate two Edge identities
- Generated `edge-a.crt/key` and `edge-b.crt/key` (CLIENT_AUTH+SERVER_AUTH) signed
  by the existing dev CA into `tmp/m2-edges-pki/`.

### 03:32 - deploy + add hosts
- Deployed CA + edge-a/edge-b certs to GNS3 VM `/opt/m2edges/`.
- Added `172.21.0.1 central` to the GNS3 VM `/etc/hosts`.

### 03:35 - TLS verification
- `openssl s_client -tls1_3 -servername central` with edge-a cert against
  `central:8443` -> **Verify OK, CN=central** (TLS 1.3, AES_256_GCM_SHA384).
- curl with edge-a cert to `https://172.21.0.1:8443/api/v1/control/hello` -> 405
  (TLS handshake succeeded; GET not allowed on POST route).

### 03:40 - run two Edge client-mode processes (systemd units)
- `ainet-edge-a` and `ainet-edge-b` systemd services both `active (running)` with
  correct `--control-url`, `--edge-id edge-a|edge-b`, certs.
- **Blocker**: the Edge client processes opened **no outbound sockets** to the
  Central (empty access log; `ss` shows no 8443 connections; foreground TLS loop
  ran 20s to RC=124 with no output). TLS is verified compatible via openssl/curl,
  yet the Go Edge client does not reach the HTTP handler.

## Errors and Blockers

- **BLOCKER (interop): Edge client-mode Go binary does not reach the Central**
  despite identical TLS 1.3 + client cert + SNI working under openssl/curl. The
  `client.Run` loop silently fails before opening a socket; no error is logged.
  This requires deep Go TLS/uvicorn interoperability debugging.
- **Architecture caveat**: client-mode Edges only report presence; device task
  execution requires server-mode `--control-listen`, which is separately blocked
  by the GNS3 host-tap -> customer-LAN reachability + project-open failures
  (see `2026-09-04_0257_phase-03_m3-live-overlap-two-edge-proof.md`).

## Security / Licensing Notes

- No secrets logged. Client-mode edge certs are development-only.

## M3 Gate Note

- Overlap **routing/scoping** is VERIFIED (resolver unit tests + live 422
  cross-tenant rejection).
- **Multi-Edge live enrollment** and **end-to-end two-Edge device execution**
  remain blocked by lab-infrastructure / edge-Runtime interop, not by routing logic.

## Final Summary

Advanced the multi-Edge control-plane setup: stood up an mTLS Central, generated
two Edge identities, deployed and ran two Edge client-mode processes, and verified
the TLS path is compatible. The Go Edge client-mode binary, however, does not
complete its HTTP hello to the Central (no sockets opened) despite TLS verifying
under openssl/curl — an edge-Runtime/uvicorn interop blocker. Combined with the
server-mode reachability issues, the **live two-Edge end-to-end overlapping-subnet
proof remains pending**; the routing/scoping logic remains verified via unit tests
and live API rejection evidence.