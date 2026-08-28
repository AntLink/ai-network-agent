---
name: openhands-software-agent-sdk-9router-hybrid
description: Design or implement the hybrid backend architecture for AI Network Agent using OpenHands software-agent-sdk as the agent engine and 9Router as the model routing layer, including file/folder blueprints, backend endpoints, event schemas, streaming, sessions, approval flow, and frontend state contracts.
metadata:
  opencode/autoinvoke: "true"
---

# OpenHands Software Agent SDK + 9Router Hybrid

Use this skill when the task is about the hybrid architecture for AI Network Agent:

- OpenHands software-agent-sdk as the agent/workspace engine.
- 9Router as the model routing layer.
- FastAPI as the integration gateway to devices, labs, approvals, audit, and UI streaming.

This skill is for architecture and implementation planning. It complements, but does not replace:

- `opencode-codex-9router-agent` for Codex-specific orchestration.
- `assistant-ui-session-manager` for thread and session persistence.
- `assistant-ui-backend-contract` for typed frontend-backend contracts.
- `assistant-ui-dashboard-chat` for the ChatGPT-like `/agent` UI.
- `assistant-ui-streaming-integration` for streamed rendering behavior.
- `ai-network-agent-backend-integration` for concrete backend endpoint wiring.
- `ai-network-agent-frontend` for broader frontend layout and page work.

## Core intent

The hybrid stack should let the project behave like a combined Network Administrator + Software Engineer Copilot:

- session-aware,
- workspace-aware,
- approval-aware,
- stream-friendly,
- vendor-aware,
- code-aware,
- test-aware,
- and safe for network automation workflows.

Do not collapse this into a generic chatbot or a direct SSH launcher.

## Capability split

Use OpenHands software-agent-sdk for software/workspace tasks:

- read/search project files,
- write or patch code,
- run workspace commands,
- run lint/test/build,
- inspect logs and error output,
- maintain task checklists,
- summarize diffs and implementation results.

Use AI Network Agent backend tools for network and infrastructure tasks:

- Linux admin checks and guarded operations,
- Cisco IOS/IOSv inspection, backup, config generation, deployment, and verification,
- MikroTik RouterOS inspection, backup, config generation, deployment, and verification,
- Aruba/AOS-CX inspection and configuration workflows,
- GNS3, Containerlab, topology, lab lifecycle, and validation.
- GNS3 topology generation from templates already available on the GNS3 server.

Do not use OpenHands TerminalTool as a free-form replacement for network device drivers. Device execution should stay behind typed backend tools, policy checks, approvals, and audit logging.

## Dynamic device inventory

The agent must manage devices dynamically from the AI Network Agent inventory, including devices added later through the `/devices` UI.

Treat these backend endpoints as the source of truth:

```text
GET    /api/v1/devices
POST   /api/v1/devices
PUT    /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}

GET    /api/v1/devices/{device_id}
GET    /api/v1/devices/{device_id}/health
GET    /api/v1/devices/{device_id}/facts
GET    /api/v1/devices/{device_id}/interfaces
GET    /api/v1/devices/{device_id}/routes
GET    /api/v1/devices/{device_id}/config
GET    /api/v1/devices/{device_id}/services
```

Every agent run should resolve device names, hostnames, IDs, vendors, platforms, management addresses, and transports from the current inventory. Do not rely on hardcoded device lists such as only `R1`, `MK-1`, or `ubuntu`.

When a new device is added on `http://localhost:5173/devices`, the agent should be able to:

- discover it through `GET /api/v1/devices`,
- classify it by `vendor`, `platform`, `transport`, and `device_type`,
- route read-only checks to the correct driver/tool family,
- ask for clarification when vendor/platform is unsupported or ambiguous,
- require approval before configuration, restart, delete, or destructive actions,
- record actions and verification results with the `device_id` from inventory.

Required device fields:

```text
id
hostname
management_address
vendor
platform
transport
status
device_type
```

Optional fields such as `console_host`, `console_port`, tags, lab/project IDs, credential profile, and role should be preserved and forwarded to the relevant tool layer when present.

## GNS3 template-based topology generation

The agent should be able to generate GNS3 topologies from templates that already exist in GNS3.

Treat these endpoints as the source of truth:

```text
GET    /api/v1/gns3/templates
POST   /api/v1/gns3/projects/create
POST   /api/v1/gns3/projects/{project_id}/nodes/create
POST   /api/v1/gns3/projects/{project_id}/links/create
POST   /api/v1/gns3/projects/{project_id}/snapshots/create
GET    /api/v1/topology?project_id={project_id}
POST   /api/v1/topology
```

The agent must not invent unavailable appliance/template IDs. It should first list templates, map the user intent to available template names and categories, then build a topology draft.

Example user request:

```text
buatkan topologi gns3 untuk routing bgp 2 router cisco dan 1 mikrotik
```

Expected flow:

```text
1. List GNS3 templates.
2. Select matching Cisco IOSv and MikroTik CHR templates.
3. Generate topology draft: nodes, links, interface plan, coordinates, labels, and project name.
4. Return `plan` + topology preview.
5. Ask approval before creating project/nodes/links.
6. Create project.
7. Create nodes from selected template IDs.
8. Create links using available adapter/port mapping.
9. Save topology JSON snapshot for the UI topology builder.
10. Create GNS3 snapshot/checkpoint.
11. Verify project nodes and links from live GNS3 API.
```

Topology generation tools:

```text
gns3.templates.list
gns3.project.create
gns3.node.create_from_template
gns3.link.create
gns3.snapshot.create
topology.generate_from_intent
topology.save_snapshot
topology.verify_against_gns3
```

Safety:

- Listing templates and generating a draft is `READ_ONLY`.
- Creating a project, node, link, or snapshot is `APPROVAL_REQUIRED`.
- Deleting nodes, links, projects, or restoring snapshots is `APPROVAL_REQUIRED`.
- The agent should prefer creating a new lab/project for generated topologies unless the user explicitly chooses an existing project.
- If multiple templates match, ask clarification or choose the safest default and show it in the plan.

## Required workflow

Prefer this backend flow:

1. User message enters the `/agent` UI.
2. FastAPI creates or resumes a session.
3. The orchestrator chooses the right agent state.
4. OpenHands software-agent-sdk handles conversation/workspace/tool execution.
5. 9Router selects the model tier or provider.
6. The backend emits events for plan, approval, progress, output, and verification.
7. The frontend renders those events as structured UI.

For every risky action, enforce:

```text
User request -> Intent -> Collect state -> Plan -> Risk analysis -> Dry run -> Approval -> Execute -> Verify -> Audit
```

Read-only checks may skip approval, but they should still emit structured events and evidence.

## Required UI states

The agent page must surface these states explicitly:

- `Thinking`
- `Planning`
- `Waiting approval`
- `Running`
- `Verifying`
- `Completed`
- `Failed`

Use these states as chips, timeline steps, or progress cards. Do not hide them inside raw logs.

## Recommended output types

The frontend should be able to render:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `verification`
- `error`
- `done`

Use `workflow_state` for visible lifecycle state. Do not rely only on inferred frontend state.

## Tool namespaces

Recommended backend tool families:

```text
workspace.search_code
workspace.read_file
workspace.write_patch
workspace.run_command
workspace.run_tests
workspace.run_lint
workspace.run_build
workspace.inspect_logs
workspace.summarize_diff

linux.exec_readonly
linux.exec_guarded
linux.service_status
linux.process_list
linux.port_check
linux.docker_status
linux.file_read
linux.file_patch
linux.restart_service
linux.journalctl
linux.verify_change

devices.list
devices.get
devices.health
devices.facts
devices.interfaces
devices.routes
devices.config
devices.services
devices.create
devices.update
devices.delete

cisco.get_facts
cisco.get_interfaces
cisco.get_routes
cisco.get_running_config
cisco.exec_readonly
cisco.generate_config
cisco.validate_config
cisco.backup_config
cisco.deploy_config
cisco.verify_change
cisco.rollback

mikrotik.get_facts
mikrotik.get_interfaces
mikrotik.get_routes
mikrotik.get_addresses
mikrotik.exec_readonly
mikrotik.generate_config
mikrotik.validate_config
mikrotik.backup_config
mikrotik.deploy_config
mikrotik.verify_change
mikrotik.rollback

lab.list_projects
lab.get_topology
lab.start_node
lab.stop_node
lab.generate_topology
lab.save_topology
lab.verify_lab_state
gns3.templates.list
gns3.project.create
gns3.node.create_from_template
gns3.link.create
gns3.snapshot.create
topology.generate_from_intent
topology.save_snapshot
topology.verify_against_gns3
```

## Safety policy

Classify every tool request as one of:

- `READ_ONLY`
- `GUARDED`
- `APPROVAL_REQUIRED`
- `BLOCKED`

Read-only examples:

- Cisco `show ...`
- MikroTik `/print`, `/ip route print`, `/interface print`
- Linux `ip addr`, `ip route`, `systemctl status`, `docker ps`, `journalctl -n`, `ss -tulpen`
- workspace read/search, lint, test, build

Approval-required examples:

- device configuration changes,
- config deploy/restore/rollback,
- Linux package install,
- Linux service restart,
- file writes outside the project workspace,
- Docker compose up/down,
- lab start/stop/destroy,
- GNS3 project/node/link creation,
- GNS3 snapshot restore,
- shell commands that alter state.

Blocked examples:

- destructive filesystem wipes,
- credential exfiltration,
- unrestricted shell/SSH relay from browser,
- device erase/reload without explicit approved workflow.

## Provider routing

Use 9Router tiers or aliases such as:

- `cheap` for discovery and helper calls.
- `coder` for implementation and normal debugging.
- `reasoning` for architecture, troubleshooting, and security-sensitive tasks.

Do not expose provider secrets to the browser.

Suggested routing:

- discovery, summaries, simple classification -> `cheap`
- implementation, normal debugging, code edits -> `coder`
- architecture, security, multi-device changes, production deployment planning -> `reasoning`

## Safety rules

- Risky or destructive network actions require approval.
- Ambiguous targets should trigger clarification, not execution.
- The browser must not run SSH, Telnet, or provider calls directly.
- LLM output for network actions should be structured intent. Vendor drivers translate intent into commands.
- Every execution should produce audit records and verification evidence.
- Distinguish backend snapshots from live command output in user-facing answers.

## When to prefer this skill

Use this skill when the request asks for:

- the hybrid backend blueprint,
- endpoint mapping,
- event schema design,
- session/store design,
- frontend state contracts,
- integration strategy between OpenHands and 9Router,
- software agent capabilities inside AI Network Agent,
- safe Linux/Cisco/MikroTik execution through chat,
- or a unified code + network copilot workflow.
