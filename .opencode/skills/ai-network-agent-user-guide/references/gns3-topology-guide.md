# GNS3 And Topology Guide

Routes:

```text
/gns3
/topology
/topology-builder
```

Use `/gns3` to view GNS3 server state, projects, nodes, links, and templates.

Use `/topology` to view the saved or live topology.

Use `/topology-builder` to edit topology layout and save it as JSON.

Agent topology generation:

```text
buatkan topologi GNS3 untuk static routing 2 router Cisco dan 2 PC
buatkan topologi GNS3 untuk BGP 2 Cisco dan 1 MikroTik
buatkan topologi lab OSPF multi area
```

Expected flow:

1. Agent lists available GNS3 templates.
2. Agent maps requested device types to template IDs.
3. Agent generates topology draft.
4. UI shows plan and preview.
5. User approves creation.
6. Backend creates project, nodes, links, snapshot.
7. Backend verifies topology from live GNS3 API.
8. Topology is saved for `/topology` and `/topology-builder`.

Important:

- Agent must use templates that already exist in GNS3.
- If a template is missing, agent should say which template is missing.
- Draft generation is read-only.
- Project/node/link creation requires approval.

