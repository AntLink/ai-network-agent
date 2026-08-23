---
name: network-topology
description: Build and visualize network topology from LLDP, CDP, routing, and VLAN data.
compatibility: OpenCode
---

# Network Topology

Build a map of the network based on discovered data.

## Data Sources
- **LLDP/CDP**: Neighbor relationships (via `device_get_topology` tool).
- **Routing tables**: Next‑hop relationships.
- **VLANs**: Trunk/access relationships.
- **Interface IPs**: Subnet relationships.

## Topology Construction
1. Discover all devices in inventory.
2. For each device, query `device_get_topology` (LLDP/CDP/neighbors).
3. Build a graph (nodes = devices, edges = links).
4. Use routing and VLAN data to infer Layer 3 topology.
5. Present the topology as an interactive graph or adjacency list.

## Output
- List of nodes (device id, hostname, model).
- List of links (source, destination, interface, speed).
- Visual representation (Mermaid or DOT format recommended).
