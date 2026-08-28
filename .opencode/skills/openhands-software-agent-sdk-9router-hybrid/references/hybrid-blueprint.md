# Hybrid Blueprint: OpenHands Software Agent SDK + 9Router

Use this blueprint when implementing the AI Network Agent backend and its frontend-facing agent workflow.

Target behavior:

```text
AI Network Agent = Network Administrator + Software Engineer Copilot
```

OpenHands software-agent-sdk handles code/workspace work. AI Network Agent backend tools handle Linux, Cisco, MikroTik, Aruba, GNS3, Containerlab, topology, approvals, audit, and verification.

## File / folder blueprint

### Backend

```text
backend/
  app/
    agent/
      orchestrator.py
      session_store.py
      event_bus.py
      state_machine.py
      intent_classifier.py
      risk.py
      approvals.py
      planner.py
      executor.py
      verifier.py
      provider_router.py
      sdk_bridge.py
      audit.py
      tools/
        devices.py
        workspace.py
        linux.py
        cisco.py
        mikrotik.py
        aruba.py
        topology.py
        gns3.py
        containerlab.py
        labs.py
        validation.py
    api/
      v1/
        endpoints/
          agent.py
          agent_sessions.py
          agent_events.py
          agent_approvals.py
          agent_runtime.py
```

### Frontend

```text
src/
  api/
    agent.ts
  types/
    agent.ts
  views/
    agent/
      index.tsx
      components/
        AgentSidebar.tsx
        ChatComposer.tsx
        MessageBubble.tsx
        ExecutionPlanCard.tsx
        ApprovalCard.tsx
        ProgressTimeline.tsx
        DeviceContext.tsx
        StreamStatusBadge.tsx
```

## Runtime responsibilities

- `OpenHands software-agent-sdk` owns code/workspace tool execution behavior.
- `9Router` owns model/provider selection and fallback.
- FastAPI owns authentication, approval policy, device/lab integration, audit, and event relay.
- Frontend owns rendering and user interaction only.
- Network drivers own vendor command translation and device execution.
- The LLM should produce structured intent for network operations, not raw uncontrolled SSH sessions.

## Capability routing

Route inventory and device management tasks to device tools:

```text
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
```

The device inventory is dynamic and must be read from the backend inventory behind `/api/v1/devices`. Any device added from `http://localhost:5173/devices` should be available to the agent without code changes.

Route software tasks to OpenHands SDK:

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
```

Route Linux admin tasks to backend Linux tools:

```text
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
```

Route network device tasks to vendor tools:

```text
cisco.get_interfaces
cisco.get_routes
cisco.get_running_config
cisco.generate_config
cisco.deploy_config
cisco.verify_change

mikrotik.get_interfaces
mikrotik.get_routes
mikrotik.get_addresses
mikrotik.generate_config
mikrotik.deploy_config
mikrotik.verify_change
```

Route lab/topology tasks to lab tools:

```text
lab.list_projects
lab.get_topology
lab.generate_topology
lab.save_topology
gns3.get_project
gns3.get_nodes
gns3.templates.list
gns3.project.create
gns3.node.create_from_template
gns3.link.create
gns3.snapshot.create
topology.generate_from_intent
topology.save_snapshot
topology.verify_against_gns3
containerlab.deploy
containerlab.inspect
```

## GNS3 template topology generation

The topology generator must use templates already present in GNS3.

Backend source-of-truth endpoints:

```text
GET    /api/v1/gns3/templates
POST   /api/v1/gns3/projects/create
POST   /api/v1/gns3/projects/{project_id}/nodes/create
POST   /api/v1/gns3/projects/{project_id}/links/create
POST   /api/v1/gns3/projects/{project_id}/snapshots/create
GET    /api/v1/topology?project_id={project_id}
POST   /api/v1/topology
```

Recommended internal files:

```text
backend/app/agent/tools/gns3.py
backend/app/agent/tools/topology.py
backend/app/agent/topology_planner.py
backend/app/agent/template_resolver.py
```

Flow:

```text
User asks for topology
-> list GNS3 templates
-> resolve template candidates by vendor/platform/kind
-> generate topology draft
-> produce plan and visual preview
-> approval
-> create or open project
-> create nodes from selected template IDs
-> create links
-> save topology snapshot JSON
-> create GNS3 snapshot
-> verify live nodes and links
-> stream final result
```

Draft schema:

```ts
interface TopologyDraft {
  projectName: string
  engine: "gns3"
  nodes: Array<{
    id: string
    name: string
    role: "router" | "switch" | "pc" | "server" | "nat" | "cloud"
    vendor: "cisco" | "mikrotik" | "aruba" | "linux" | "other"
    templateId: string
    templateName: string
    x: number
    y: number
  }>
  links: Array<{
    source: string
    target: string
    sourcePort?: string
    targetPort?: string
    purpose?: string
  }>
}
```

Rules:

- Never invent unavailable template IDs.
- If a needed Cisco/MikroTik/Aruba/Linux template is missing, return a clear missing-template finding.
- If more than one template matches, show the selected template in the plan and ask clarification when the choice is risky.
- Draft generation is `READ_ONLY`.
- Creating projects, nodes, links, snapshots, deleting topology objects, or restoring snapshots is `APPROVAL_REQUIRED`.
- Prefer creating a new project for generated topology unless the user explicitly asks to modify an existing project.
- Persist the generated topology via `POST /api/v1/topology` so topology builder and topology page show the same layout.

## Recommended state machine

```text
Thinking -> Planning -> Waiting approval -> Running -> Verifying -> Completed
                     \-> Failed
```

## Conversation flow

1. User sends a request.
2. Backend resumes or creates a session.
3. Orchestrator loads current device inventory from `/api/v1/devices`.
4. Orchestrator resolves requested device names, IDs, hostnames, vendor, platform, transport, and device type.
5. Orchestrator collects current state from the selected devices.
6. Agent produces a plan.
7. If the change is risky, return an approval event and wait.
8. After approval, execute the task.
9. Verify results.
10. Persist session and audit events.
11. Stream the full result back to the UI.

## Dynamic device inventory contract

Expected device fields:

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

Optional fields such as `console_host`, `console_port`, `credential_profile`, `tags`, `role`, `lab_id`, and `project_id` should be preserved when present.

Vendor routing rules:

```text
vendor/platform contains cisco or ios    -> cisco tools
vendor/platform contains mikrotik/routeros -> mikrotik tools
vendor/platform contains aruba/aos-cx   -> aruba tools
vendor/platform contains linux/ubuntu/debian/rhel/embedded -> linux tools
unknown vendor/platform                 -> clarification or generic read-only health only
```

Device management operations:

- Add/edit/delete devices are inventory operations and should usually require user confirmation from chat.
- Delete device is `APPROVAL_REQUIRED`.
- Editing `management_address`, `transport`, credentials, or vendor/platform is `APPROVAL_REQUIRED`.
- Listing, health, facts, interfaces, routes, config read, and service status are `READ_ONLY`.
- GNS3 template listing and topology draft generation are `READ_ONLY`.
- GNS3 project/node/link/snapshot creation is `APPROVAL_REQUIRED`.

## Risk workflow

Use this workflow for changes:

```text
User request
-> Intent classification
-> Collect state
-> Plan
-> Risk analysis
-> Dry run
-> Approval
-> Execute
-> Verify
-> Audit
```

Read-only checks can skip approval, but still need events, source/evidence labels, and clear output.

## OpenHands SDK bridge

`backend/app/agent/sdk_bridge.py` should:

- create the OpenHands `LLM`,
- use 9Router-compatible model/base URL settings,
- create an OpenHands `Agent`,
- expose `TerminalTool`, `FileEditorTool`, and `TaskTrackerTool` only for workspace-safe tasks,
- bind conversations to the project workspace,
- translate SDK events into AI Network Agent stream events,
- block or approval-gate risky workspace commands.

Do not expose OpenHands or 9Router credentials to the frontend.

## Design rules

- Keep device facts and session facts backend-owned.
- Keep the UI structured and stateful.
- Never expose secrets or direct shell access in the browser.
- Preserve vendor-aware output for Cisco, MikroTik, Aruba, Linux, and lab engines.
- Distinguish backend snapshot evidence from live command output.
- Do not claim command execution unless a tool result or `command_output` event exists.
- Every risky action needs an approval and an audit record.
