"""Structured tool registry contract for the AI Network Agent."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.agent.risk import AgentPolicy


class ToolNamespace(StrEnum):
    WORKSPACE = "workspace"
    DEVICES = "devices"
    LINUX = "linux"
    CISCO = "cisco"
    MIKROTIK = "mikrotik"
    ARUBA = "aruba"
    GNS3 = "gns3"
    CONTAINERLAB = "containerlab"
    TOPOLOGY = "topology"
    LAB = "lab"


class ExecutionScope(StrEnum):
    WORKSPACE = "workspace"
    DEVICE = "device"
    LAB = "lab"
    INVENTORY = "inventory"
    PROVIDER = "provider"


class EvidenceType(StrEnum):
    BACKEND_SNAPSHOT = "backend_snapshot"
    LIVE_COMMAND_OUTPUT = "live_command_output"
    GENERATED_PLAN = "generated_plan"
    DRY_RUN = "dry_run"
    AUDIT_RECORD = "audit_record"


@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    namespace: ToolNamespace
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    policy: AgentPolicy
    execution_scope: ExecutionScope
    evidence_type: EvidenceType
    requires_approval: bool = False
    vendor_scope: tuple[str, ...] = ()
    timeout_seconds: int = 30
    rollback_supported: bool = False
    audit_fields: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "namespace": self.namespace.value,
            "description": self.description,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
            "policy": self.policy.value,
            "vendorScope": list(self.vendor_scope),
            "executionScope": self.execution_scope.value,
            "requiresApproval": self.requires_approval,
            "evidenceType": self.evidence_type.value,
            "timeoutSeconds": self.timeout_seconds,
            "rollbackSupported": self.rollback_supported,
            "auditFields": list(self.audit_fields),
        }


_GENERIC_OUTPUT = {
    "status": "string",
    "tool": "string",
    "policy": "string",
    "evidence": "string",
    "target": "object",
    "summary": "string",
    "data": "object",
    "raw": "string",
    "error": "string|null",
}


def default_tool_registry() -> dict[str, ToolDescriptor]:
    tools = [
        _tool("devices.list", ToolNamespace.DEVICES, "List all inventory devices", {}, AgentPolicy.READ_ONLY, ExecutionScope.INVENTORY),
        _tool("devices.get", ToolNamespace.DEVICES, "Get one inventory device", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.health", ToolNamespace.DEVICES, "Check device reachability and status", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.facts", ToolNamespace.DEVICES, "Collect device facts", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.interfaces", ToolNamespace.DEVICES, "Collect interface table", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.routes", ToolNamespace.DEVICES, "Collect routing table", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.config", ToolNamespace.DEVICES, "Collect running configuration", {"device_id": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE),
        _tool("devices.create", ToolNamespace.DEVICES, "Create inventory device", {"device": "object"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.INVENTORY, approval=True),
        _tool("devices.update", ToolNamespace.DEVICES, "Update inventory device", {"device_id": "string", "device": "object"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.INVENTORY, approval=True),
        _tool("devices.delete", ToolNamespace.DEVICES, "Delete inventory device", {"device_id": "string"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.INVENTORY, approval=True),
        _tool("linux.exec_readonly", ToolNamespace.LINUX, "Run safe Linux read-only command", {"device_id": "string", "command": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, vendors=("linux",)),
        _tool("linux.service_status", ToolNamespace.LINUX, "Check Linux service status", {"device_id": "string", "service": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, vendors=("linux",)),
        _tool("linux.restart_service", ToolNamespace.LINUX, "Restart Linux service", {"device_id": "string", "service": "string"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.DEVICE, approval=True, vendors=("linux",)),
        _tool("cisco.exec_readonly", ToolNamespace.CISCO, "Run Cisco IOS read-only command", {"device_id": "string", "command": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, vendors=("cisco",)),
        _tool("cisco.deploy_config", ToolNamespace.CISCO, "Deploy Cisco IOS configuration", {"device_id": "string", "commands": "array"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.DEVICE, approval=True, vendors=("cisco",), rollback=True),
        _tool("mikrotik.exec_readonly", ToolNamespace.MIKROTIK, "Run MikroTik RouterOS read-only command", {"device_id": "string", "command": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, vendors=("mikrotik",)),
        _tool("mikrotik.deploy_config", ToolNamespace.MIKROTIK, "Deploy MikroTik RouterOS configuration", {"device_id": "string", "commands": "array"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.DEVICE, approval=True, vendors=("mikrotik",), rollback=True),
        _tool("aruba.exec_readonly", ToolNamespace.ARUBA, "Run Aruba AOS-CX read-only command", {"device_id": "string", "command": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.DEVICE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, vendors=("aruba",)),
        _tool("aruba.deploy_config", ToolNamespace.ARUBA, "Deploy Aruba AOS-CX configuration", {"device_id": "string", "commands": "array"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.DEVICE, approval=True, vendors=("aruba",), rollback=True),
        _tool("gns3.templates.list", ToolNamespace.GNS3, "List GNS3 templates", {}, AgentPolicy.READ_ONLY, ExecutionScope.LAB),
        _tool("gns3.project.create", ToolNamespace.GNS3, "Create GNS3 project", {"name": "string"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.LAB, approval=True),
        _tool("gns3.node.create_from_template", ToolNamespace.GNS3, "Create GNS3 node from template", {"project_id": "string", "template_id": "string"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.LAB, approval=True),
        _tool("topology.generate_from_intent", ToolNamespace.TOPOLOGY, "Generate topology draft from user intent", {"prompt": "string"}, AgentPolicy.GUARDED, ExecutionScope.LAB, evidence=EvidenceType.GENERATED_PLAN),
        _tool("topology.save_snapshot", ToolNamespace.TOPOLOGY, "Save topology snapshot", {"project_id": "string", "topology": "object"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.LAB, approval=True),
        _tool("containerlab.inspect", ToolNamespace.CONTAINERLAB, "Inspect Containerlab labs", {}, AgentPolicy.READ_ONLY, ExecutionScope.LAB),
        _tool("containerlab.deploy", ToolNamespace.CONTAINERLAB, "Deploy Containerlab topology", {"topology": "string"}, AgentPolicy.APPROVAL_REQUIRED, ExecutionScope.LAB, approval=True),
        _tool("workspace.list_files", ToolNamespace.WORKSPACE, "List workspace files and directories", {"path": "string", "depth": "integer"}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.BACKEND_SNAPSHOT),
        _tool("workspace.search_code", ToolNamespace.WORKSPACE, "Search workspace files for a pattern", {"pattern": "string", "path": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.BACKEND_SNAPSHOT),
        _tool("workspace.read_file", ToolNamespace.WORKSPACE, "Read a workspace file", {"path": "string", "start": "integer", "limit": "integer"}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.BACKEND_SNAPSHOT),
        _tool("workspace.write_file", ToolNamespace.WORKSPACE, "Create or overwrite a workspace file", {"path": "string", "content": "string"}, AgentPolicy.GUARDED, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT),
        _tool("workspace.edit_file", ToolNamespace.WORKSPACE, "Replace an exact string in a workspace file", {"path": "string", "old": "string", "new": "string"}, AgentPolicy.GUARDED, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT),
        _tool("workspace.run_command", ToolNamespace.WORKSPACE, "Run a shell command in the workspace", {"command": "string", "timeout": "integer"}, AgentPolicy.GUARDED, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT, timeout_seconds=120),
        _tool("workspace.run_tests", ToolNamespace.WORKSPACE, "Run the project test suite", {}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT),
        _tool("workspace.run_lint", ToolNamespace.WORKSPACE, "Run the project linter", {}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT),
        _tool("workspace.run_build", ToolNamespace.WORKSPACE, "Run the project build/typecheck", {}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.LIVE_COMMAND_OUTPUT),
        _tool("workspace.task_tracker", ToolNamespace.WORKSPACE, "Maintain the current task checklist", {"task_id": "string", "items": "array"}, AgentPolicy.GUARDED, ExecutionScope.WORKSPACE, evidence=EvidenceType.AUDIT_RECORD),
        _tool("workspace.think", ToolNamespace.WORKSPACE, "Reason about the next step (no side effects)", {"reasoning": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.AUDIT_RECORD),
        _tool("workspace.finish", ToolNamespace.WORKSPACE, "Signal task completion with a summary", {"summary": "string"}, AgentPolicy.READ_ONLY, ExecutionScope.WORKSPACE, evidence=EvidenceType.AUDIT_RECORD),
    ]
    return {tool.name: tool for tool in tools}


def list_tool_descriptors(namespace: str | None = None) -> list[dict[str, Any]]:
    registry = default_tool_registry()
    if namespace:
        namespace = namespace.lower()
        return [tool.to_dict() for tool in registry.values() if tool.namespace.value == namespace]
    return [tool.to_dict() for tool in registry.values()]


def get_tool_descriptor(name: str) -> dict[str, Any] | None:
    tool = default_tool_registry().get(name)
    return tool.to_dict() if tool else None


def _tool(
    name: str,
    namespace: ToolNamespace,
    description: str,
    input_schema: dict[str, Any],
    policy: AgentPolicy,
    execution_scope: ExecutionScope,
    *,
    evidence: EvidenceType = EvidenceType.BACKEND_SNAPSHOT,
    approval: bool = False,
    vendors: tuple[str, ...] = (),
    rollback: bool = False,
    timeout_seconds: int = 30,
) -> ToolDescriptor:
    return ToolDescriptor(
        name=name,
        namespace=namespace,
        description=description,
        input_schema=input_schema,
        output_schema=_GENERIC_OUTPUT,
        policy=policy,
        execution_scope=execution_scope,
        evidence_type=evidence,
        requires_approval=approval,
        vendor_scope=vendors,
        rollback_supported=rollback,
        timeout_seconds=timeout_seconds,
        audit_fields=("session_id", "task_id", "target", "policy", "risk", "result"),
    )
