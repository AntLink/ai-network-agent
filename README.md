# AI Network Agent — AI-Powered Network Operations Center

AI-driven network management platform for Cisco, MikroTik, Aruba, Ruijie, FortiGate, Juniper (vJunos), GNS3, Containerlab, and vrnetlab environments.

## Features

### Frontend (React + Vite + TypeScript + Tailwind CSS)

| Page | Description |
|------|-------------|
| Dashboard | Network health, device status, AI operations |
| Devices | Device list (paginasi + filter jumlah/halaman), detail, interfaces, routes, config |
| Terminal | Interactive SSH sessions with autocomplete |
| Configurations | Config plan, dry-run, apply, rollback |
| GNS3 | Project lifecycle, nodes, links, snapshots |
| Containerlab | Lab deployment, topology management |
| Tasks | Task execution tracking |
| Alerts | Alert management |
| Backups | Backup inventory |
| Agent | AI Network Copilot with chat, plan, validate |
| Credentials | Credential management (secrets never exposed) |
| Settings | General, AI, SSH, security settings |
| Discovery | Network discovery and device onboarding |
| Audit | Audit trail and event history |
| Topology | Network topology visualization |

### Backend (FastAPI + Python)

**23 endpoint modules:**

```
/devices    /config     /monitoring   /topology   /audit
/mikrotik   /cisco      /aruba        /asa        /ruijie
/fortigate  /gns3       /policy       /terminal    /tasks
/alerts     /backups    /agent        /credentials /settings
/discovery  /containerlab /ninerouter
```

### Vendor Drivers

Driver perangkat (SSH dan/atau telnet-console GNS3), semua baca rutin mengembalikan `{ data: parsed, raw }`:

| Vendor | Driver | Transport | Status |
|--------|--------|-----------|--------|
| Cisco IOS/IOS-XE | `cisco/` | SSH + console | ✅ |
| Cisco ASA (ASAv) | `cisco/asa.py` | console | ✅ |
| MikroTik RouterOS | `mikrotik/` | SSH + console | ✅ |
| Aruba AOS-CX | `aruba/` | SSH + console | ✅ |
| Ruijie RGOS | `ruijie/` | console | ✅ |
| Fortinet FortiOS | `fortinet/` | console | ✅ |
| Linux (Debian/RHEL/Embedded) | `linux/` | SSH | ✅ |

### AI Providers

| Provider | Chat | Stream | Web Search | Free Models |
|----------|------|--------|------------|-------------|
| OpenAI | ✅ | ✅ | - | - |
| Anthropic | ✅ | ✅ | - | - |
| Ollama | ✅ | ✅ | - | ✅ Local |
| 9Router | ✅ | ✅ | ✅ | ✅ Go/Zen |

### Agent Tools

- `get_device` — Device facts and status
- `get_interfaces` — Interface status
- `get_routes` — Routing table
- `get_running_config` — Running configuration
- `ping` — Ping from device
- `traceroute` — Traceroute from device
- `validate_config` — Validate without applying
- `backup_config` — Backup configuration

### Real-time Streaming

- Terminal: WebSocket `WS /api/v1/terminal/sessions/{id}/stream`
- Agent: SSE `GET /api/v1/agent/events/stream`
- Tasks: SSE `GET /api/v1/tasks/stream`

## Quick Start

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv env
.\env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run backend
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Configure environment
# Create .env file:
# VITE_API_BASE_URL=http://localhost:8000
# VITE_USE_MOCKS=false

# Run frontend
npm run dev
```

### 3. Environment Variables

```bash
# Backend
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false

# AI Provider (choose one)
AI_PROVIDER=9router     # or openai, anthropic, ollama

# 9Router (free models available)
NINEROUTER_URL=http://127.0.0.1:20128
NINEROUTER_KEY=your-secret-key
NINEROUTER_MODEL=opencode-go  # free: opencode-go, opencode-zen

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## API Documentation

Start the backend and visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
ai-network-agent/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI provider abstraction, tools
│   │   ├── api/v1/         # FastAPI endpoints
│   │   ├── drivers/        # Cisco, MikroTik, GNS3, Aruba, ASA, Ruijie, FortiGate, Linux
│   │   ├── core/           # Audit, policy
│   │   ├── models/         # Data models
│   │   ├── parsers/        # CLI output parsers
│   │   ├── services/       # Terminal service
│   │   └── transports/     # SSH + telnet-console transport
│   └── tests/
├── src/
│   ├── api/network/        # API client, hooks, backend adapter
│   ├── components/         # Reusable UI components
│   ├── views/              # Page components
│   ├── types/              # TypeScript types
│   └── hooks/              # Custom hooks
├── inventory/              # Device inventory
├── backups/                # Configuration backups
├── logs/                   # Session logs
└── docs/                   # Documentation
```

## Safety Principles

1. **No SSH in browser** — All SSH runs through backend
2. **No credentials in frontend** — Secrets stay backend-side
3. **Plan → Validate → Execute → Verify** — All changes go through workflow
4. **Approval required** — Destructive changes need confirmation
5. **Backup before deploy** — Automatic backup before changes
6. **Rollback available** — Can undo changes if needed

## Documentation

- `docs/FRONTEND_BACKEND_INTEGRATION.md` — Endpoint sync guide
- `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md` — AI agent architecture
- `CHANGES_SUMMARY.md` — Catatan perubahan per sesi
- `ARCHITECTURE.md` — System architecture
- `logs/` — Session logs and history

## License

MIT
