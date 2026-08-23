---
name: network-troubleshooting
description: Analyze end‑to‑end connectivity problems across network infrastructure.
compatibility: OpenCode
---

# Network Troubleshooting

Diagnose issues systematically. Never change configuration without explicit approval.

## Troubleshooting Workflow
1. Understand the symptom (e.g., "Client in VLAN 30 can't reach internet").
2. Trace the path:
   - Client → Access Switch → Distro Switch → Core → Firewall → Router → WAN → Internet.
3. At each hop, use `device_get_interfaces`, `device_get_routes`, `device_get_config`, `device_get_monitoring`.
4. Identify the failure point (e.g., down interface, missing route, NAT misconfiguration).
5. Present findings and possible causes.
6. **Do not apply changes** — delegate to `network-operator` for changes.

## Common Checks
- Interface status (`show ip interface brief`, `show interfaces`).
- Routing table (`show ip route`).
- VLAN membership.
- Firewall/NAT rules.
- ARP table.
- Connectivity tests (ping from device).
- Logs (`show logging`, `logread`).

## L2/L3 Isolation Techniques (proven in lab, 2026-08-23)

When pings fail but everything "looks connected", isolate layer by layer:

1. **One-way link detection**: compare packet counters at BOTH ends of a
   link (`show interfaces X | i packets`). One side stuck while the other
   increments = broken transport (in GNS3: stale ubridge sockets; fix by
   stop/start of endpoint nodes via API). "connected" status proves nothing.
2. **MAC table classification**: clear `mac address-table dynamic`,
   generate traffic from the client, then check WHICH VLAN the MAC was
   learned in and on which port. Client MAC appearing in VLAN 1 while the
   gateway lives in VLAN 10 = missing/wrong `switchport access vlan`.
3. **ARP as the truth test**: router ARP `Incomplete` + empty client ARP
   table = broadcast domain broken even if link LEDs are up.
4. **Trunk health**: gateway MAC must appear on the trunk port inside the
   expected VLAN's entry; SVI-to-gateway ping exercises the whole tagged path.
5. **Compare against actual cabling**: in GNS3, GET the links API map —
   physical topology may differ from documentation after rework.
