# ADR-0001: Direct mTLS Control Channel with Optional ZeroTier Overlay

- Status: Accepted for Milestones 1–3
- Date: 2026-09-05
- Scope: Central ↔ Edge control and customer-LAN execution

## Context

The platform must execute device operations locally from the appropriate Edge
and must support customers with overlapping LAN subnets. ZeroTier can provide
overlay connectivity, but making every task depend on a ZeroTier controller
would add an unnecessary runtime dependency to the first secure vertical slice.

## Decision

The authoritative Central ↔ Edge control channel uses direct HTTPS with mutual
TLS. The Edge polls Central for capability tasks and submits results through
that channel. Device SSH/SNMP/NETCONF/RESTCONF execution remains local to the
Edge customer LAN.

ZeroTier remains an optional replaceable overlay managed through
`OverlayProvider`. A ZeroTier client may run on the Edge when overlay
connectivity, maintenance access, or site isolation requires it. ZeroTier is
not the mandatory proxy for normal task execution, and Central does not route
all customer LAN prefixes globally.

## Consequences

- Milestone 1 can be proven with Central-to-Edge mTLS and GNS3 LAN access only.
- Overlay controller outage does not automatically stop an already reachable
  Central ↔ Edge control path.
- Production overlay deauthorization remains a separate acceptance gate.
- Private controller/root deployment and ZeroTier licensing must be reviewed
  before enabling overlay features commercially.
- Edge enrollment, certificate revocation, session revoke, and task routing
  remain Central responsibilities regardless of overlay availability.

## Rejected alternatives

- Making Central SSH directly to customer devices: breaks overlapping subnet
  isolation and weakens Edge-local execution boundaries.
- Making every task depend on ZeroTier: unnecessarily couples the control plane
  to overlay availability and controller configuration.
- Treating `zerotier-cli leave` as the primary revoke workflow: it is local
  cleanup, not authoritative controller-side membership deauthorization.
