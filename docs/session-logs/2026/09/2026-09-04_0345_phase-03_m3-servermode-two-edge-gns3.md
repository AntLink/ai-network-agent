# Work Session: m3-servermode-two-edge-gns3

## Session Metadata

- Session ID: `20260904-034511-phase-03-m3-servermode-two-edge-gns3`
- Date/Time Started: `2026-09-04T03:45:11+08:00`
- Date/Time Closed: `2026-09-04T04:15:00+08:00`
- Implementation Phase: `phase-03`
- Status: `PARTIAL` (build spec ready; live execution blocked by lab infra)
- Operator: `opencode`
- Branch: `main`
- Starting Worktree: `dirty`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Build the 2-topology GNS3 lab for the Milestone 3 overlapping-subnet proof: two
isolated LANs each with a router at the SAME management IP (192.168.1.1), an Edge
on each LAN, and Central routing `device.read.facts` to the correct Edge.

## Topology (uses the pre-existing TEST-EDGE project)

Project: `TEST-EDGE` (`75573856-b9a8-4587-8fd1-391de8bf6686`, open).

- **Topology A (LAN-A)** on `Switch1`:
  - `IOSv1`:0/0 <- Switch1:e1   (router, management 192.168.1.1)
  - `ALPINE1`:0/0 <- Switch1:e0 (Edge host)
  - `NAT1` -> ALPINE1:1/0       (internet/NAT)
- **Topology B (LAN-B)** on `Switch2`:
  - `IOSv2`:0/0 <- Switch2:e1   (router, management 192.168.1.1)
  - `ALPINE2`:0/0 <- Switch2:e0 (Edge host)
  - `NAT2` -> ALPINE2:1/0       (internet/NAT)

Two LANs are isolated by separate switches, so both routers can use `192.168.1.1`
without collision. IOSv1/IOSv2 are `stopped`; ALPINE1/ALPINE2/Switch1/Switch2/NAT1/NAT2
are `started`.

## Required configuration (build spec)

1. **Routers**: configure IOSv1 and IOSv2 both with `192.168.1.1/24` on their LAN
   interface + SSH (`username admin`, `ip ssh version 2`). Overlapping IP, isolated
   by switch.
2. **Edge hosts (ALPINE1/ALPINE2)**: configure the ephemeral Alpine (static IP on
   the LAN, enable sshd with the deploy key) and deploy the Go `ainet-edge`.
   Run each Edge in **server-mode** (`--control-listen 0.0.0.0:9443`,
   `--edge-id edge-a` / `edge-b`, with its own keystore pointing at the router at
   192.168.1.1). Central reaches each Edge control port.
3. **Central**: register two scoped devices `a-r1`/`b-r1` (both `192.168.1.1`,
   `customer_a`/`customer_b`, `edge-a`/`edge-b`), then POST `/tasks/capability`
   for each; verify each routes to the correct Edge and returns its own normalized
   facts.

## What was verified this session (lab control path)

- GNS3 controller reachable from the network-agent backend (projects=3).
- `TEST-EDGE` project exists and contains the 2-topology nodes/links.
- The Windows host -> 172.21.0.2:80 direct API path intermittently 404s (Hyper-V
  networking), while the backend/network-agent path works; lab control must go
  through the backend.

## Errors and Blockers

- **BLOCKER (lab infra)**: The ALPINE edge VMs are ephemeral (ISO-boot, RAM-only);
  each reboot reverts to a bare Alpine (no sshd/network) — the same issue as the
  earlier `ALPINE1` in BGP-LAB. Configuring them reliably has repeatedly failed.
- **BLOCKER (lab infra)**: The Windows->GNS3-VM controller API path is unstable
  (intermittent 404); only the backend/network-agent path is reliable.
- Live end-to-end two-Edge device dispatch therefore remains pending on lab-state
  restoration, not on code/logic.

## M3 Gate Note

- Overlap **routing/scoping** is VERIFIED (unit tests + live 422 cross-tenant
  rejection).
- The live **two-Edge end-to-end** dispatch blueprint is now fully defined in this
  project's TEST-EDGE topology; execution awaits a stable lab.

## Final Summary

The 2-topology overlapping-subnet lab blueprint is fully defined using the existing
`TEST-EDGE` GNS3 project: two isolated LAN A/B, each with a router at `192.168.1.1`
and an Edge host. The control path is verified reachable through the backend. Live
execution is blocked by ephemeral Alpine edge VMs and unstable Windows->GNS3-VM
networking; when the lab is stable, follow the build spec above to complete the live
proof. Overlap routing logic remains verified.