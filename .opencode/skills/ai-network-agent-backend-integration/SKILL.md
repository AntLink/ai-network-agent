---
name: ai-network-agent-backend-integration
description: Integrate the AI Network Agent shadcndashboard frontend with the existing FastAPI backend endpoints. Use for replacing MSW mock data with real API calls, syncing endpoint contracts, wiring device details, terminal commands, config plan/apply/rollback, GNS3 lifecycle, audit, topology, monitoring, and identifying backend gaps for tasks, alerts, backups, credentials, settings, discovery, agent, Containerlab, and real-time streams.
compatibility: AI Network Agent; FastAPI; React; Vite; TypeScript; SWR; MSW; shadcndashboard
metadata:
  opencode/autoinvoke: "true"
---

# AI Network Agent Backend Integration Skill

Use this skill when connecting the frontend to the FastAPI backend.

The frontend is an AI-powered Network Operations Center built from `shadcndashboard`. The current UI uses MSW mock endpoints under `/api/network/*`. The backend exposes real endpoints mostly under `/api/v1/*`.

## Mandatory discovery

Before changing code:

1. Read `docs/FRONTEND_BACKEND_INTEGRATION.md`.
2. Read `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md` when touching agent, task, config workflow, provider, or streaming behavior.
3. Read `openapi.json`.
4. Read `backend/app/api/v1/router.py`.
5. Read the target backend endpoint file under `backend/app/api/v1/endpoints/`.
6. Read the target frontend API hook file, currently `src/api/network/index.ts`.
7. Read the target view/component under `src/views/` and `src/components/`.
8. Confirm whether the endpoint exists in code, not only in `openapi.json`.

Do not start by guessing endpoint names from the UI route.

## Small issue resolution pattern

Use this pattern for the small-but-important integration problems that appear during live frontend/backend/device testing.

1. Reproduce the exact symptom.
   - Capture the route, endpoint, device id, command, request method, status code, and UI state.
   - Example: `GET /api/v1/mikrotik/mikrotik-chr-mk-1/interface` returns `404`, or Cisco `show ?` stops before `xsd-format`.

2. Classify where the fault is.
   - Frontend route/API mapping problem.
   - Backend route missing or wrong prefix.
   - Backend adapter/parser problem.
   - Device/vendor behavior problem.
   - Lab/inventory/GNS3 topology problem.
   - Pure UI layout/state problem.

3. Verify from the lowest reliable layer first.
   - For UI bugs, inspect the component, state, and CSS class/layout.
   - For endpoint bugs, call the backend endpoint directly.
   - For device behavior, test through backend/session driver, not by inventing local mock data.
   - For GNS3 issues, verify inventory, node link state, management IP, and console/SSH availability.

4. Prefer a narrow patch.
   - Fix the adapter, route, parser, CSS layout, or service method that owns the problem.
   - Do not rewrite unrelated pages or move architecture boundaries to solve one symptom.
   - Do not add frontend SSH, local credential storage, or static command lists as a shortcut.

5. Keep behavior vendor-aware.
   - Cisco IOS and MikroTik RouterOS do not expose help/autocomplete the same way.
   - Match actual device behavior when possible: Cisco `?`, MikroTik contextual help from RouterOS.
   - Normalize in backend only enough to make the UI consistent; do not hide vendor facts that matter.

6. Validate the real user flow.
   - Re-run the exact interaction that failed.
   - Check success and failure states.
   - For autocomplete, verify keyboard selection, scroll behavior, filtering, and no unwanted popup when `?` is absent.
   - For terminal output, verify prompt cleanup and transcript readability.

7. Add a regression test when the bug is parser/service logic.
   - Cisco/MikroTik terminal suggestion parsing should have unit tests.
   - Parser fixes should include representative raw output fixtures when practical.

8. Update documentation/logs for behavior changes.
   - Record what changed, the endpoint involved, the reason, and the validation result.

Practical examples from this project:

- Bad vendor endpoint: stop calling MikroTik endpoints for Cisco devices; route by `device.vendor`.
- `502 Bad Gateway`: show a clear operational error in UI and verify backend/device connectivity separately.
- Unknown device detail: normalize backend response into typed device facts before rendering cards.
- Raw config in UI: parse structured fields first and keep raw config as secondary/debug view.
- Tab layout broken: fix tab container/content layout instead of rebuilding the page.
- Base UI button warning: render a native `<button>` or set `nativeButton={false}` when intentionally rendering another element.
- Cisco incomplete `show ?`: handle device pagination and increase parser/suggestion limits.
- MikroTik `ip ?` only showing root commands: preserve user intent, normalize context in backend, retry after RouterOS banner, and parse the returned device help.

## Core architecture rule

The browser must not run network automation directly.

Forbidden in frontend:

- SSH client logic
- Telnet client logic
- Netmiko/Scrapli/NAPALM execution
- direct GNS3 host shell execution
- Containerlab host commands
- storing plaintext credentials
- storing secrets in localStorage/sessionStorage
- embedding real passwords, API tokens, or SSH keys in mocks

Allowed frontend flow:

```text
View
  -> typed hook/service function
  -> HTTP API client
  -> FastAPI backend
  -> drivers/lab engines
```

## Terminal integration rule

Prefer the backend terminal session manager for interactive terminal work.

Current live terminal endpoints:

- `GET /api/v1/terminal/sessions`
- `POST /api/v1/terminal/sessions`
- `DELETE /api/v1/terminal/sessions/{session_id}`
- `POST /api/v1/terminal/sessions/{session_id}/execute`
- `POST /api/v1/terminal/sessions/{session_id}/suggest`
- `POST /api/v1/terminal/sessions/{session_id}/input`
- `WS /api/v1/terminal/sessions/{session_id}/stream`

Autocomplete must come from the device through the backend session, not from a local static command list.

Expected behavior:

- Cisco: trigger suggestion only when the command contains `?`, for example `?`, `show ?`, `show ip ?`, or `show ?a`.
- MikroTik: trigger suggestion only when the command contains `?`, for example `?`, `ip ?`, or `ip ?f`.
- Frontend may filter the returned device suggestions by the text typed after `?`.
- Frontend must not show suggestions continuously when the user is not asking for help.
- Frontend must not store SSH credentials.
- Risky commands still require warning/confirmation, and destructive/config changes should move toward the config plan/apply workflow.

## Network Copilot rule

The AI agent must be designed as a Network Copilot, not as a chatbot with a direct command button.

Required workflow for changes:

```text
Plan -> Validate -> Execute -> Verify
```

The LLM must not receive SSH credentials, open SSH sessions, or execute vendor CLI directly. It should produce structured intent and execution plans. Backend drivers translate those intents into Cisco IOS, MikroTik RouterOS, Aruba AOS-CX, GNS3, or Containerlab operations.

Example intent:

```json
{
  "action": "configure_interface",
  "device_id": "r1",
  "parameters": {
    "interface": "GigabitEthernet0/1",
    "address": "192.168.10.1/24",
    "enabled": true
  }
}
```

The backend should validate this intent, generate vendor-specific candidate configuration, run policy checks, require approval for risky changes, back up device state, deploy through drivers, verify post-change state, and record audit/task events.

## AI provider abstraction

Do not hardcode one AI provider. Prefer a backend provider abstraction similar to:

```text
backend/app/agent/providers/
|-- base.py
|-- openai.py
|-- anthropic.py
|-- deepseek.py
|-- openrouter.py
|-- ollama.py
`-- nvidia_nim.py
```

Settings should select provider/model, but frontend must never receive provider API keys in plaintext. Provider credentials stay backend-side.

## Internal agent tools

Expose agent capabilities as controlled backend tools, not arbitrary shell/SSH primitives:

- `get_device()`
- `get_interfaces()`
- `get_running_config()`
- `get_routes()`
- `ping()`
- `traceroute()`
- `backup_config()`
- `generate_config()`
- `validate_config()`
- `deploy_config()`
- `rollback()`
- `verify_change()`
- `gns3_get_topology()`
- `containerlab_manage()`

Troubleshooting requests should use read-only tools first and propose a fix with risk/approval. Complex changes such as IPsec should return an execution plan before producing deployable configuration.

## Current backend endpoint map

Base:

- `GET /health`
- API prefix: `/api/v1`

Read-only core:

- `GET /api/v1/devices`
- `GET /api/v1/devices/{device_id}`
- `GET /api/v1/devices/{device_id}/health`
- `GET /api/v1/devices/{device_id}/identify`
- `GET /api/v1/devices/{device_id}/facts`
- `GET /api/v1/devices/{device_id}/interfaces`
- `GET /api/v1/devices/{device_id}/routes`
- `GET /api/v1/devices/{device_id}/config`
- `GET /api/v1/devices/{device_id}/vlans`
- `GET /api/v1/devices/{device_id}/services`
- `GET /api/v1/devices/{device_id}/disk`
- `GET /api/v1/devices/{device_id}/memory`
- `GET /api/v1/devices/{device_id}/ntp`
- `GET /api/v1/monitoring/{device_id}`
- `POST /api/v1/monitoring/{device_id}`
- `GET /api/v1/topology`
- `GET /api/v1/audit`

Terminal and command execution:

- `POST /api/v1/devices/{device_id}/console/exec`
- `POST /api/v1/cisco/{device_id}/commands/run`
- `POST /api/v1/cisco/{device_id}/exec`
- `POST /api/v1/mikrotik/{device_id}/commands/run`

Configuration governance:

- `POST /api/v1/config/plan`
- `GET /api/v1/config/plans`
- `GET /api/v1/config/plans/{plan_id}`
- `POST /api/v1/config/apply`
- `POST /api/v1/config/rollback`

Vendor-specific read resources:

- Cisco: `/api/v1/cisco/{device_id}/resources/*`
- MikroTik: `/api/v1/mikrotik/{device_id}/resources/*`

Vendor-specific writes:

- Cisco: system, users, interface, static route, ACL, L2, config save/backup/push/transaction.
- MikroTik: IP, VLAN, bridge, static route, firewall, pool, DHCP, interface, system, wireless, hotspot, PPP, tunnel, OSPF, config save/transaction.

GNS3:

- `GET /api/v1/gns3/local-config`
- `POST /api/v1/gns3/test-connection`
- `POST /api/v1/gns3/projects`
- `POST /api/v1/gns3/projects/create`
- `POST /api/v1/gns3/projects/{project_id}`
- `POST /api/v1/gns3/projects/{project_id}/open`
- `POST /api/v1/gns3/projects/{project_id}/close`
- `DELETE /api/v1/gns3/projects/{project_id}`
- node lifecycle, links, templates, snapshots under `/api/v1/gns3/projects/{project_id}/...`

Policy:

- `POST /api/v1/policy/check`

## Backend gaps to preserve as explicit TODOs

Do not pretend these exist unless added to backend:

- `/api/v1/tasks`
- `/api/v1/tasks/{id}`
- `/api/v1/alerts`
- `/api/v1/backups`
- `/api/v1/discovery`
- `/api/v1/settings`
- `/api/v1/credentials`
- `/api/v1/agent`
- `/api/v1/containerlab`
- SSE/WebSocket stream endpoints for task updates, agent messages, alerts, and topology changes

When wiring a page that needs one of these, either:

- keep MSW fallback, or
- derive a limited view from existing endpoints, and document the limitation.

## Integration phases

### Integration Phase A: API client foundation

- Add `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.
- Create a single fetch wrapper with timeout and typed error normalization.
- Keep MSW only for demo/dev fallback.
- Do not hardcode backend URL in components.

### Integration Phase B: Read-only frontend

Wire:

- dashboard summaries from devices, monitoring, topology, audit
- devices list/detail
- interfaces, routes, config, VLANs, services, disk, memory, NTP
- topology
- audit

Use adapters to normalize backend responses into frontend types.

### Integration Phase C: Terminal

Wire interactive terminal session manager:

- Create session with `POST /api/v1/terminal/sessions`.
- Execute command with `POST /api/v1/terminal/sessions/{session_id}/execute`.
- Request live device suggestions with `POST /api/v1/terminal/sessions/{session_id}/suggest`.
- Stream output with `WS /api/v1/terminal/sessions/{session_id}/stream`.
- Close session with `DELETE /api/v1/terminal/sessions/{session_id}`.

No browser-side SSH.

Legacy vendor command endpoints may remain available for fallback, but the preferred UI terminal path is the backend session manager.

### Integration Phase D: Config workflow

Use only governance endpoints for general apply flow:

1. `POST /api/v1/config/plan`
2. `GET /api/v1/config/plans/{plan_id}`
3. UI approval
4. `POST /api/v1/config/apply`
5. post-check using monitoring/read endpoints
6. rollback with `POST /api/v1/config/rollback` if needed

Direct vendor write endpoints must still pass policy/safety UI and confirmation.

### Integration Phase E: GNS3

Wire:

- local config
- test connection
- list/open/close/create/delete projects
- nodes list/create/start/stop/restart/delete
- links list/create/delete
- snapshots list/create/restore

Delete, rebuild, restore, and stop all actions require confirmation.

### Integration Phase F: Missing backend features

Design or add backend endpoints for:

- tasks
- alerts
- backup inventory
- discovery
- credentials
- settings
- agent
- Containerlab
- real-time streams

Update OpenAPI after adding endpoints.

For the agent feature, prefer adding:

- `POST /api/v1/agent/chat`
- `POST /api/v1/agent/plan`
- `POST /api/v1/agent/validate`
- `POST /api/v1/agent/execute`
- `GET /api/v1/agent/tasks/{task_id}`
- `GET /api/v1/agent/tasks/{task_id}/events`
- `GET /api/v1/agent/events`

SSE is acceptable as the first streaming implementation for task progress, command output, agent messages, alerts, and topology changes.

## Response normalization

Backend responses are not fully uniform. Some endpoints return:

- direct arrays/objects
- `{data: ..., raw: ...}`
- `{events: [...]}`
- `{plans: [...]}`
- device-specific parser output
- error objects

Frontend adapters must normalize these into `src/types/network.ts` types before passing data to pages.

Do not make pages parse raw CLI strings unless there is no structured data available. If raw is needed, show it as transcript/debug secondary data.

## Agent event normalization

Agent and task streams should normalize to typed UI events/cards:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

Do not stream opaque Markdown when the UI needs structured progress, approval, diff, or verification cards.

## Safety requirements

Any operation with these verbs or meanings is risky:

- apply
- push
- delete
- remove
- rollback
- restore
- rebuild
- destroy
- reload
- shutdown
- disable
- factory reset
- password/user/secret changes
- ACL/firewall/routing/default route changes

Frontend must display:

- target device/lab
- exact operation
- generated commands/config
- risk level
- backup status
- validation plan
- approval identity requirement

Never call these endpoints directly from a simple button without confirmation.

## Validation gate

After each integration slice:

```bash
npm run lint
npm run build
```

If backend code changes are made:

```bash
cd backend
python -m pytest
```

If OpenAPI/client generation is changed, regenerate and verify the generated client does not break TypeScript.

## Documentation update rule

When endpoint wiring changes, update:

- `docs/FRONTEND_BACKEND_INTEGRATION.md`
- relevant session log in `logs/`
- `README.md` if the workflow or setup command changes

## Definition of done

An integration slice is done only when:

- UI data comes from the correct backend endpoint or documented fallback.
- loading/error/empty states still work.
- destructive actions still require confirmation.
- no secrets are exposed in frontend.
- lint and build pass.
- any backend gap is explicitly documented.
