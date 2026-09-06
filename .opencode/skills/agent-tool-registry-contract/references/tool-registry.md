# Tool Registry Contract

## Tool descriptor

```ts
interface AgentToolDescriptor {
  name: string
  namespace: "workspace" | "devices" | "linux" | "cisco" | "mikrotik" | "aruba" | "gns3" | "containerlab" | "topology" | "lab"
  description: string
  inputSchema: Record<string, unknown>
  outputSchema: Record<string, unknown>
  policy: "READ_ONLY" | "GUARDED" | "APPROVAL_REQUIRED" | "BLOCKED"
  vendorScope?: Array<"cisco" | "mikrotik" | "aruba" | "linux" | "other">
  executionScope: "workspace" | "device" | "lab" | "inventory" | "provider"
  requiresApproval: boolean
  evidenceType: "backend_snapshot" | "live_command_output" | "generated_plan" | "dry_run" | "audit_record"
  timeoutSeconds: number
  rollbackSupported: boolean
  auditFields: string[]
}
```

## Required tool families

```text
workspace.*
devices.*
linux.*
cisco.*
mikrotik.*
aruba.*
gns3.*
containerlab.*
topology.*
lab.*
```

## Minimum tools

```text
workspace.search_code
workspace.read_file
workspace.write_patch
workspace.run_command
workspace.run_tests
workspace.run_lint
workspace.run_build

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

linux.exec_readonly
linux.service_status
linux.process_list
linux.port_check
linux.docker_status
linux.journalctl
linux.restart_service

cisco.exec_readonly
cisco.get_interfaces
cisco.get_routes
cisco.get_running_config
cisco.backup_config
cisco.generate_config
cisco.deploy_config
cisco.verify_change
cisco.rollback

mikrotik.exec_readonly
mikrotik.get_interfaces
mikrotik.get_routes
mikrotik.get_addresses
mikrotik.backup_config
mikrotik.generate_config
mikrotik.deploy_config
mikrotik.verify_change
mikrotik.rollback

gns3.templates.list
gns3.project.create
gns3.node.create_from_template
gns3.link.create
gns3.snapshot.create

topology.generate_from_intent
topology.save_snapshot
topology.verify_against_gns3
```

## Output rules

Every tool output should include:

```json
{
  "status": "ok",
  "tool": "linux.service_status",
  "policy": "READ_ONLY",
  "evidence": "live_command_output",
  "target": {
    "device_id": "linux-ubuntu"
  },
  "summary": "...",
  "data": {},
  "raw": "...",
  "error": null
}
```

Do not return secrets in `summary`, `data`, `raw`, events, or logs.

