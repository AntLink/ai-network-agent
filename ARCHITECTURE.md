# AI Network Agent — Architecture

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  Dashboard │ Devices │ Terminal │ Agent │ GNS3 │ Configurations │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket/SSE
┌─────────────────────────────▼───────────────────────────────────┐
│                     FastAPI Backend (Python)                     │
├─────────────────────────────────────────────────────────────────┤
│  API Layer (19 modules)                                         │
│  /devices /config /monitoring /topology /audit                  │
│  /mikrotik /cisco /gns3 /policy /terminal                      │
│  /tasks /alerts /backups /agent /credentials                   │
│  /settings /discovery /containerlab /ninerouter                │
├─────────────────────────────────────────────────────────────────┤
│  Agent Layer                                                    │
│  ├── AI Providers (OpenAI, Anthropic, Ollama, 9Router)         │
│  ├── Internal Tools (get_device, ping, validate_config, etc.)  │
│  └── Web Search/Fetch (9Router)                                │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer                                                  │
│  ├── Terminal Session Manager (SSH via backend)                │
│  ├── Config Governance (plan → validate → apply → verify)      │
│  ├── Policy Engine (risk, approval, safety)                    │
│  └── Audit Trail                                               │
├─────────────────────────────────────────────────────────────────┤
│  Driver Layer                                                   │
│  ├── Cisco IOS/IOS-XE                                          │
│  ├── MikroTik RouterOS                                         │
│  ├── Aruba AOS-CX                                              │
│  ├── GNS3 Controller                                           │
│  └── Containerlab                                              │
├─────────────────────────────────────────────────────────────────┤
│  Transport Layer                                                │
│  ├── SSH (asyncssh)                                            │
│  ├── REST API                                                  │
│  └── WebSocket                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Network Devices                             │
│  Cisco IOSv │ MikroTik CHR │ Aruba AOS-CX │ Linux │ GNS3 VM   │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Endpoints (19 modules)

| Module | Prefix | Description |
|--------|--------|-------------|
| devices | /api/v1/devices | Device inventory, facts, interfaces, routes |
| config | /api/v1/config | Configuration plan, apply, rollback |
| monitoring | /api/v1/monitoring | Real-time metrics (CPU, memory, interfaces) |
| topology | /api/v1/topology | LLDP/CDP neighbor mapping |
| audit | /api/v1/audit | Audit trail and event history |
| mikrotik | /api/v1/mikrotik | MikroTik vendor-specific (88+ endpoints) |
| cisco | /api/v1/cisco | Cisco IOS/IOS-XE vendor-specific |
| gns3 | /api/v1/gns3 | GNS3 controller/compute API |
| policy | /api/v1/policy | Risk and approval checks |
| terminal | /api/v1/terminal | Interactive SSH session manager |
| tasks | /api/v1/tasks | Task execution tracking |
| alerts | /api/v1/alerts | Alert management |
| backups | /api/v1/backups | Backup inventory |
| agent | /api/v1/agent | AI Network Copilot (chat, plan, tools) |
| credentials | /api/v1/credentials | Credential management |
| settings | /api/v1/settings | System settings |
| discovery | /api/v1/discovery | Network discovery |
| containerlab | /api/v1/containerlab | Containerlab management |
| ninerouter | /api/v1/ninerouter | 9Router web search/fetch |

## AI Provider Abstraction

```python
# backend/app/agent/providers.py
AIProvider (base)
├── OpenAIProvider     # OpenAI API
├── AnthropicProvider  # Anthropic Claude API
├── OllamaProvider     # Ollama local LLM
└── NineRouterProvider # 9Router gateway (chat + web search/fetch)
```

### Free Model Combos (via 9Router)

| Model | Tier | Description |
|-------|------|-------------|
| opencode-go | Free | Fast, quick tasks |
| opencode-zen | Free | Balanced, general work |
| opencode-cheap | Free | Cheapest available |
| opencode-coder | Paid | Coding model |
| opencode-reasoning | Paid | Reasoning model |

## Agent Internal Tools

```python
# backend/app/agent/tools.py
AGENT_TOOLS = {
    "get_device":       "Get device facts and status",
    "get_interfaces":   "Get device interface status",
    "get_routes":       "Get device routing table",
    "get_running_config": "Get device running config",
    "ping":             "Ping from device to target",
    "traceroute":       "Traceroute from device to target",
    "validate_config":  "Validate config commands",
    "backup_config":    "Backup device configuration",
}
```

## Real-time Streaming

| Feature | Protocol | Endpoint |
|---------|----------|----------|
| Terminal Output | WebSocket | WS /api/v1/terminal/sessions/{id}/stream |
| Agent Events | SSE | GET /api/v1/agent/events/stream |
| Task Updates | SSE | GET /api/v1/tasks/stream |

## Network Copilot Workflow

```text
User Request
    ↓
Agent Plan (structured intent)
    ↓
Collect Current State (get_device, get_interfaces, get_routes)
    ↓
Generate Candidate Configuration
    ↓
Validate (validate_config, policy check)
    ↓
Dry Run / Diff
    ↓
User Approval (when required)
    ↓
Backup (backup_config)
    ↓
Deploy (config apply)
    ↓
Post-check (get_interfaces, ping)
    ↓
Success OR Rollback
```

## Safety Principles

1. **No SSH in browser** — All SSH runs through backend
2. **No credentials in frontend** — Secrets stay backend-side
3. **Plan → Validate → Execute → Verify** — All changes go through workflow
4. **Approval required** — Destructive changes need confirmation
5. **Backup before deploy** — Automatic backup before changes
6. **Rollback available** — Can undo changes if needed

## Frontend Architecture

```text
src/
├── api/network/
│   ├── index.ts          # SWR hooks and API functions
│   ├── backend-client.ts # Backend adapter functions
│   ├── network-data.ts   # MSW mock data
│   └── sse-client.ts     # SSE client utility
├── views/                # Page components
├── components/           # Reusable UI components
├── types/                # TypeScript types
└── hooks/                # Custom hooks
```

## Data Flow

```text
View Component
    ↓
SWR Hook (useDevices, useTasks, etc.)
    ↓
backendOrMock() — tries backend, falls back to MSW
    ↓
Backend Adapter (loadBackendDevices, etc.)
    ↓
HTTP Request → FastAPI Backend
    ↓
Driver Layer (Cisco, MikroTik, GNS3)
    ↓
Network Device
```
