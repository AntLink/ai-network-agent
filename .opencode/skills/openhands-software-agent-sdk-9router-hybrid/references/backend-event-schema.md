# Backend Event Schema

This schema is the contract between the backend agent layer and the `/agent` frontend.

## Session events

```ts
interface AgentSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  deviceIds: string[]
  labId?: string
  status: "idle" | "running" | "error"
}
```

## Message events

```ts
interface AgentMessage {
  id: string
  sessionId: string
  role: "user" | "assistant" | "system" | "tool"
  content: string
  createdAt: string
  type?:
    | "message"
    | "plan"
    | "device_state"
    | "command_output"
    | "config_diff"
    | "topology_draft"
    | "approval"
    | "task_progress"
    | "verification"
    | "workflow_state"
    | "error"
}
```

## Streaming event

```ts
interface AgentEvent {
  type:
    | "message"
    | "workflow_state"
    | "plan"
    | "device_state"
    | "command_output"
    | "config_diff"
    | "topology_draft"
    | "approval"
    | "task_progress"
    | "verification"
    | "error"
    | "done"
  sessionId: string
  deviceId?: string
  deviceIds?: string[]
  message?: string
  payload?: Record<string, unknown>
  state?: "thinking" | "planning" | "waiting_approval" | "running" | "verifying" | "completed" | "failed"
}
```

## Device inventory event

Device-aware events should reference current inventory IDs from `/api/v1/devices`.

```json
{
  "type": "device_state",
  "sessionId": "session-id",
  "deviceId": "linux-ubuntu",
  "payload": {
    "hostname": "ubuntu",
    "vendor": "linux",
    "platform": "ubuntu",
    "management_address": "192.168.210.51",
    "transport": "ssh",
    "device_type": "physical",
    "evidence": "backend_snapshot"
  }
}
```

Inventory CRUD actions should be emitted as audit-capable events:

```json
{
  "type": "task_progress",
  "sessionId": "session-id",
  "deviceId": "new-device-id",
  "payload": {
    "tool": "devices.create",
    "policy": "APPROVAL_REQUIRED",
    "status": "success",
    "message": "Device added to inventory"
  }
}
```

## Workflow state event

```json
{
  "type": "workflow_state",
  "sessionId": "session-id",
  "taskId": "task-id",
  "state": "planning",
  "label": "Planning",
  "detail": "Menyusun rencana eksekusi",
  "activeIndex": 1,
  "eventsCount": 4,
  "createdAt": "2026-08-27T00:00:00Z"
}
```

## Approval event

```json
{
  "type": "approval",
  "sessionId": "session-id",
  "state": "waiting_approval",
  "payload": {
    "risk": "medium",
    "title": "Approve OSPF configuration",
    "deviceIds": ["cisco-iosv-r1", "cisco-iosv-r2"],
    "backupStatus": "required",
    "commandsPreview": ["router ospf 1", "network 10.0.0.0 0.0.0.255 area 0"]
  }
}
```

## Progress event

```json
{
  "type": "task_progress",
  "sessionId": "session-id",
  "state": "running",
  "payload": {
    "step": "backup",
    "status": "success",
    "message": "Running configuration backed up"
  }
}
```

## Command output event

```json
{
  "type": "command_output",
  "sessionId": "session-id",
  "taskId": "task-id",
  "payload": {
    "tool": "linux.service_status",
    "deviceId": "linux-ubuntu",
    "command": "systemctl status frigate --no-pager",
    "status": "ok",
    "output": "..."
  }
}
```

## Tool policy

Every executable tool event should include a policy class:

```ts
type ToolPolicy = "READ_ONLY" | "GUARDED" | "APPROVAL_REQUIRED" | "BLOCKED"
```

Use `READ_ONLY` for inspection commands, `APPROVAL_REQUIRED` for changes, and `BLOCKED` for destructive or credential-exfiltration requests.

## Topology draft event

Use this event when the agent generates a GNS3 topology from available templates.

```json
{
  "type": "topology_draft",
  "sessionId": "session-id",
  "payload": {
    "engine": "gns3",
    "projectName": "bgp-lab",
    "evidence": "gns3_templates",
    "templates": [
      {
        "templateId": "template-cisco-iosv",
        "templateName": "Cisco IOSv",
        "vendor": "cisco"
      },
      {
        "templateId": "template-mikrotik-chr",
        "templateName": "MikroTik CHR",
        "vendor": "mikrotik"
      }
    ],
    "nodes": [
      {
        "id": "r1",
        "name": "R1",
        "vendor": "cisco",
        "role": "router",
        "templateId": "template-cisco-iosv",
        "x": 120,
        "y": 120
      }
    ],
    "links": [
      {
        "source": "r1",
        "target": "r2",
        "purpose": "BGP peering"
      }
    ]
  }
}
```

Topology creation approval should include:

```json
{
  "type": "approval",
  "sessionId": "session-id",
  "state": "waiting_approval",
  "payload": {
    "risk": "medium",
    "title": "Create GNS3 topology",
    "tool": "topology.generate_from_intent",
    "policy": "APPROVAL_REQUIRED",
    "projectName": "bgp-lab",
    "actions": [
      "create project",
      "create nodes from selected templates",
      "create links",
      "save topology snapshot",
      "create GNS3 snapshot",
      "verify nodes and links"
    ]
  }
}
```

## Evidence labels

User-facing answers should distinguish:

- `backend_snapshot`: inventory, facts, interfaces, routes, cached state, or collected state.
- `live_command_output`: actual command/tool execution result.
- `generated_plan`: proposed actions not yet executed.
- `dry_run`: generated command preview and risk analysis.

## UI rendering rule

The frontend should map `state` to visible UI chips/timeline steps and map `type` to the proper card or message renderer.

The frontend should never execute SSH, shell commands, provider calls, or workspace edits directly. It only sends requests, approvals, and cancellations to FastAPI.
