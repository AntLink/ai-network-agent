---
name: ai-network-agent-user-guide
description: Answer end-user questions about how to use the AI Network Agent dashboard, chat agent, devices page, terminal, GNS3 topology builder, approvals, and common troubleshooting flows.
metadata:
  opencode/autoinvoke: "true"
---

# AI Network Agent User Guide

Use this skill when the user asks how to use the AI Network Agent application, including:

- dashboard navigation,
- `/agent` chat usage,
- adding, editing, or deleting devices,
- checking Cisco, MikroTik, Aruba, or Linux devices,
- using Terminal SSH,
- generating GNS3 topologies,
- understanding approval and dry-run workflows,
- backup, config, audit, alert, and task pages,
- common UI/backend troubleshooting.

This skill is for user-facing usage guidance. It should not replace implementation skills such as:

- `openhands-software-agent-sdk-9router-hybrid`
- `opencode-codex-9router-agent`
- `ai-network-agent-backend-integration`
- `ai-network-agent-frontend`
- `configuration-safety`

## Response style

Answer like an operator guide:

- concise,
- step-by-step,
- practical,
- tied to the visible UI route or menu,
- in the user's language,
- with examples the user can paste into chat.

Do not expose backend secrets, credentials, or internal implementation details unless the user explicitly asks as a developer.

## Core pages

Use these references:

- `references/user-guide.md`
- `references/agent-chat-guide.md`
- `references/devices-guide.md`
- `references/terminal-guide.md`
- `references/gns3-topology-guide.md`
- `references/safety-workflow-guide.md`
- `references/troubleshooting-guide.md`

## Safety

When explaining risky operations, always mention:

- read-only checks do not require approval,
- configuration changes require approval,
- destructive actions require confirmation,
- frontend never runs SSH or shell directly,
- backend tools execute and audit actions.

