# Frontend Backend Integration Plan

Tanggal: 2026-08-24

Dokumen ini menyinkronkan frontend AI Network Agent dengan endpoint FastAPI yang ada saat ini. Sumber utama:

- `openapi.json`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/endpoints/*.py`
- `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md`

Catatan penting: `openapi.json` sudah diregenerasi dari aplikasi FastAPI pada sesi ini agar sinkron dengan route backend terbaru, termasuk `GET /api/v1/config/plans` dan `GET /api/v1/config/plans/{plan_id}`.

## Status Frontend Saat Ini

Frontend sudah selesai sampai Phase 5 dengan base UI `shadcndashboard`.

Route utama:

- `/dashboard`
- `/agent`
- `/tasks`
- `/terminal`
- `/devices`
- `/devices/:id`
- `/topology`
- `/topology-builder`
- `/labs`
- `/labs/:id`
- `/gns3`
- `/containerlab`
- `/configurations`
- `/backups`
- `/alerts`
- `/audit`
- `/discovery`
- `/settings`
- `/settings/credentials`

Data sebagian masih memakai MSW mock di `src/api/network/network-data.ts`. Read-only core sudah mulai dihubungkan ke FastAPI melalui adapter di `src/api/network/backend-client.ts`. Integrasi backend tetap dilakukan lewat service layer, bukan langsung dari komponen page.

Konfigurasi frontend:

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_USE_MOCKS=false`

Jika `VITE_USE_MOCKS=true`, frontend memakai MSW mock. Jika `VITE_USE_MOCKS=false`, hook read-only mencoba FastAPI dan pada mode dev akan fallback ke MSW jika backend tidak tersedia.

## Endpoint Backend Yang Sudah Ada

Base API:

- `GET /health`
- prefix API utama: `/api/v1`

Devices:

- `GET /api/v1/devices`
- `GET /api/v1/devices/{device_id}`
- `GET /api/v1/devices/{device_id}/health`
- `POST /api/v1/devices/{device_id}/console/exec`
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

Config governance:

- `POST /api/v1/config/plan`
- `GET /api/v1/config/plans`
- `GET /api/v1/config/plans/{plan_id}`
- `POST /api/v1/config/apply`
- `POST /api/v1/config/rollback`

Monitoring, topology, audit:

- `GET /api/v1/monitoring/{device_id}`
- `POST /api/v1/monitoring/{device_id}`
- `GET /api/v1/topology`
- `GET /api/v1/audit`

Cisco:

- read resources: version, interfaces, interfaces-detail, routes, arp, cpu-memory, acls, cdp-neighbors, nat-translations, logs
- command execution: `POST /api/v1/cisco/{device_id}/commands/run`
- netmiko execution: `POST /api/v1/cisco/{device_id}/exec`
- config transaction: `POST /api/v1/cisco/{device_id}/config/transaction`
- config backup: `POST /api/v1/cisco/{device_id}/config/backup`
- config push: `POST /api/v1/cisco/{device_id}/config/push`
- config save: `POST /api/v1/cisco/{device_id}/config/save`
- write endpoints for hostname, DNS, NTP, banner, users, interface, routes, ACL, VLAN, access/trunk/subinterface/SVI

MikroTik:

- read resources: ip-addresses, pools, dhcp, bridges, bridge ports, firewall, OSPF, BGP, static routes, PPP, wireless, SNMP, users, logs, hotspot, tunnels
- command execution: `POST /api/v1/mikrotik/{device_id}/commands/run`
- monitoring: `POST /api/v1/mikrotik/{device_id}/monitoring`
- health: `GET /api/v1/mikrotik/{device_id}/health`
- config transaction: `POST /api/v1/mikrotik/{device_id}/config/transaction`
- config save: `POST /api/v1/mikrotik/{device_id}/config/save`
- write endpoints for IP address, VLAN, bridge, static route, firewall, pools, DHCP, interface state, identity, users, NTP, DNS, wireless security, hotspot, PPP, tunnel, OSPF

GNS3:

- `GET /api/v1/gns3/local-config`
- `POST /api/v1/gns3/test-connection`
- `POST /api/v1/gns3/projects`
- `POST /api/v1/gns3/projects/create`
- `POST /api/v1/gns3/projects/{project_id}`
- `POST /api/v1/gns3/projects/{project_id}/open`
- `POST /api/v1/gns3/projects/{project_id}/close`
- `DELETE /api/v1/gns3/projects/{project_id}`
- `POST /api/v1/gns3/projects/{project_id}/nodes`
- `POST /api/v1/gns3/projects/{project_id}/nodes/create`
- node lifecycle: start, stop, restart, properties, disk-interface, rebuild, console, delete
- links: list, create, delete
- templates: list, update
- snapshots: list, create, restore

Policy:

- `POST /api/v1/policy/check`

## Frontend Mock Endpoint Mapping

Saat ini frontend memakai endpoint mock:

- `/api/network/dashboard`
- `/api/network/health`
- `/api/network/devices`
- `/api/network/devices/:id`
- `/api/network/labs`
- `/api/network/labs/:id`
- `/api/network/topology`
- `/api/network/gns3`
- `/api/network/containerlab`
- `/api/network/agent/messages`
- `/api/network/agent/plan`
- `/api/network/tasks`
- `/api/network/tasks/:id`
- `/api/network/terminal/session`
- `/api/network/configurations`
- `/api/network/backups`
- `/api/network/alerts`
- `/api/network/audit`
- `/api/network/discovery`
- `/api/network/credentials`
- `/api/network/settings`

Endpoint di atas adalah kontrak UI sementara, bukan backend asli.

## Mapping Integrasi Prioritas

Dashboard:

- devices summary: `GET /api/v1/devices`
- per-device health: `GET /api/v1/devices/{device_id}/health`
- monitoring trend: belum ada endpoint agregat; tahap awal ambil `GET /api/v1/monitoring/{device_id}` per device
- topology summary: `GET /api/v1/topology`
- audit recent: `GET /api/v1/audit`

Devices:

- list: `GET /api/v1/devices`
- detail identity: `GET /api/v1/devices/{device_id}` dan `GET /api/v1/devices/{device_id}/facts`
- health: `GET /api/v1/devices/{device_id}/health`
- interfaces: `GET /api/v1/devices/{device_id}/interfaces`
- routing: `GET /api/v1/devices/{device_id}/routes`
- config: `GET /api/v1/devices/{device_id}/config`
- VLAN: `GET /api/v1/devices/{device_id}/vlans`
- metrics: `GET /api/v1/monitoring/{device_id}`

Terminal:

- Cisco: `POST /api/v1/cisco/{device_id}/commands/run` atau `POST /api/v1/cisco/{device_id}/exec`
- MikroTik: `POST /api/v1/mikrotik/{device_id}/commands/run`
- fallback console: `POST /api/v1/devices/{device_id}/console/exec`
- streaming belum ada; UI harus mulai dengan request/response command history, lalu upgrade ke SSE/WebSocket jika backend ditambah

Configurations:

- plan: `POST /api/v1/config/plan`
- list plans: `GET /api/v1/config/plans`
- plan detail: `GET /api/v1/config/plans/{plan_id}`
- apply: `POST /api/v1/config/apply`
- rollback: `POST /api/v1/config/rollback`
- direct vendor config transaction harus tetap melalui confirmation dan policy: Cisco/MikroTik `config/transaction`

Backups:

- Cisco backup: `POST /api/v1/cisco/{device_id}/config/backup`
- restore/rollback: `POST /api/v1/config/rollback`
- list backup inventory belum ada endpoint khusus; sementara bisa derive dari config plan reports atau perlu backend endpoint baru

Audit:

- list events: `GET /api/v1/audit`

Topology:

- topology read: `GET /api/v1/topology`
- GNS3 topology/lab detail: GNS3 project, nodes, links endpoints

GNS3:

- local config/status basis: `GET /api/v1/gns3/local-config`
- connection test: `POST /api/v1/gns3/test-connection`
- projects/nodes/links/templates/snapshots sesuai endpoint GNS3 yang sudah ada

Containerlab:

- belum ada endpoint backend di FastAPI saat ini
- frontend tetap mock sampai backend menambahkan endpoint `containerlab`

Discovery:

- ✅ Endpoint backend `/api/v1/discovery` sudah dibuat
- Discovery results, scan, dan add device sudah terhubung ke backend

Credentials:

- ✅ Endpoint backend `/api/v1/credentials` sudah dibuat
- Credential list, create, dan delete sudah terhubung ke backend
- Secret tidak dikirim ke frontend setelah tersimpan

Settings:

- ✅ Endpoint backend `/api/v1/settings` sudah dibuat
- Settings get dan update sudah terhubung ke backend

Alerts:

- ✅ Endpoint backend `/api/v1/alerts` sudah dibuat
- Alert list, create, update, dan delete sudah terhubung ke backend

AI Agent:

- ✅ Endpoint backend `/api/v1/agent/*` sudah dibuat (chat, plan, validate, execute, events)
- Agent harus mengikuti aritektur Network Copilot: Plan -> Validate -> Execute -> Verify
- LLM hanya menghasilkan structured intent, bukan menjalankan SSH atau raw CLI langsung
- Provider AI harus lewat abstraction backend, bukan hardcode satu provider
- Tahap awal AI plan UI bisa memanggil `POST /api/v1/agent/plan`
- destructive action tetap memerlukan approval via `POST /api/v1/config/apply`
- Riwayat chat agent dipersist per session: backend session messages di-upsert by ID, lalu frontend mereplay transcript tersimpan saat reload agar bubble lama tidak hilang
- SSE agent stream sekarang mengirim event operasional yang lebih kaya:
  - `start`
  - `plan`
  - `device_state`
  - `approval`
  - `task_progress`
  - `command_output`
  - `verification`
  - `text`
  - `done`
  - `error`
- Stream membawa `session_id`, `device_ids`, `lab_id`, `project_id`, dan `environment` agar konteks sesi tetap sinkron di backend
- detail kontrak agent ada di `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md`

Tasks:

- ✅ Endpoint backend `/api/v1/tasks` dan `/api/v1/tasks/{id}` sudah dibuat
- Task list dan detail sudah terhubung ke backend dengan fallback MSW
- Stream update untuk task progress masih perlu WebSocket/SSE

## Tahapan Integrasi Backend

Tahap 1: Read-only core

- Status: dimulai.
- Hook `useDevices`, `useDeviceDetail`, `useDashboardSummary`, `useNetworkHealth`, `useTopology`, dan `useAuditLogs` sudah memakai adapter backend dengan fallback MSW saat dev.
- Adapter response dibuat di `src/api/network/backend-client.ts` supaya response backend yang bervariasi tetap masuk ke type frontend.
- `VITE_API_BASE_URL` sudah didukung, default `http://localhost:8000`.
- `VITE_USE_MOCKS=true` dapat dipakai untuk memaksa mode mock.
- Catatan: dashboard health series sementara dibuat dari snapshot device karena endpoint monitoring agregat belum ada.
- Catatan: topology backend saat ini masih mengembalikan `{nodes: [], links: []}`.

Tahap 2: Terminal live session

- Status: sudah dimulai dan sudah memiliki backend terminal session manager.
- Terminal UI dapat membuat interactive SSH session melalui `POST /api/v1/terminal/sessions`.
- Session aktif dapat dilihat lewat `GET /api/v1/terminal/sessions` dan ditutup lewat `DELETE /api/v1/terminal/sessions/{session_id}`.
- Command execution pada session aktif memakai `POST /api/v1/terminal/sessions/{session_id}/execute`.
- Raw interactive input disiapkan lewat `POST /api/v1/terminal/sessions/{session_id}/input`.
- Streaming output disiapkan lewat `WS /api/v1/terminal/sessions/{session_id}/stream`.
- Autocomplete live memakai `POST /api/v1/terminal/sessions/{session_id}/suggest`.
- Cisco autocomplete mengikuti pola perangkat: user mengetik `?`, `show ?`, `show ip ?`, atau `show ?a`; backend mengirim helper `?` ke session SSH dan frontend memfilter suffix setelah `?`.
- MikroTik autocomplete mengikuti pola perangkat dari input seperti `ip ?`; backend menormalisasi request menjadi konteks RouterOS yang benar lalu mengambil pilihan dari perangkat.
- Parser suggestion sudah menangani Cisco pagination `--More--`, output panjang seperti `show ?` sampai `xsd-format`, banner RouterOS, prompt line, dan retry awal jika output masih berisi banner.
- Terminal menampilkan transcript, running state, error banner, command history, risk badge, connection status, dan keyboard navigation untuk autocomplete.
- Frontend risk classifier tetap ada: read-only langsung jalan, low/medium/high minta confirmation, critical diblokir.
- Jangan simpan credential di frontend.
- Catatan: endpoint vendor one-shot lama masih ada sebagai fallback/legacy, tetapi mode yang diprioritaskan untuk UI terminal adalah session manager.

Tahap 3: Configuration workflow

- Status: dimulai.
- Halaman `/configurations` sudah membuat dry-run plan lewat `POST /api/v1/config/plan`.
- Plan real ditampilkan di panel Dry Run: plan id, status, risk, target, generated commands, dan approval identity.
- Apply hanya bisa dilakukan setelah plan dibuat dan approval identity tersedia.
- Deploy memakai confirmation modal lalu memanggil `POST /api/v1/config/apply`.
- Rollback UI placeholder masih ada; wiring `POST /api/v1/config/rollback` belum dilakukan karena perlu backup id/report yang valid dari apply result.
- Sanity check `POST /api/v1/config/plan` sukses membuat plan `1059a24c` tanpa apply ke device.

Tahap 4: GNS3 lifecycle

- Status: selesai.
- Halaman `/gns3` sudah terhubung ke backend production endpoints.
- Load local config dari `GET /api/v1/gns3/local-config`.
- Test connection ke `POST /api/v1/gns3/test-connection`.
- List projects dari `POST /api/v1/gns3/projects`.
- Create project lewat `POST /api/v1/gns3/projects/create`.
- Open/close/delete project lewat endpoints yang sesuai.
- View nodes per project dari `POST /api/v1/gns3/projects/{project_id}/nodes`.
- Start/stop/delete node lewat endpoints yang sesuai.
- UI mendukung loading states, error handling, toast notifications, dan confirmation dialogs.

Tahap 5: Backend gaps

- Status: selesai (basic endpoints).
- Backend endpoints sudah dibuat untuk:
  - Tasks: `GET/POST /api/v1/tasks`, `GET/PATCH /api/v1/tasks/{id}`
  - Alerts: `GET/POST /api/v1/alerts`, `PATCH/DELETE /api/v1/alerts/{id}`
  - Backups: `GET/POST /api/v1/backups`, `DELETE /api/v1/backups/{id}`
  - Agent: `POST /api/v1/agent/chat`, `/plan`, `/validate`, `/execute`, `GET /api/v1/agent/events`
  - Credentials: `GET/POST /api/v1/credentials`, `DELETE /api/v1/credentials/{id}`
  - Settings: `GET/PATCH /api/v1/settings`
  - Discovery: `GET /api/v1/discovery`, `POST /api/v1/discovery/scan`, `/add`
- Frontend hooks sudah terhubung ke backend dengan fallback MSW.
- Containerlab backend endpoints masih perlu ditambahkan.
- WebSocket/SSE streaming untuk task updates dan agent messages masih perlu diimplementasi.
- Semua delete/rebuild/restore harus pakai confirmation.

Tahap 5: Backend gaps

- Tambah backend endpoint untuk tasks, alerts, backups list, credentials, settings, discovery, agent, Containerlab.
- Terminal WebSocket sudah disiapkan di backend. Berikutnya tambahkan SSE/WebSocket untuk task update, agent message, alert created, dan topology change.

Tahap 6: Network Copilot backend

- Tambah provider abstraction di `backend/app/agent/providers/` untuk OpenAI, Anthropic, DeepSeek, OpenRouter, Ollama, dan NVIDIA NIM.
- Tambah schema structured intent, execution plan, agent events, approval request, dan verification result.
- Tambah internal tool registry: device facts, interfaces, routes, config, ping, traceroute, backup, validate, deploy, rollback, verify, GNS3 topology, dan Containerlab management.
- Tambah endpoint agent minimal: `POST /api/v1/agent/chat`, `POST /api/v1/agent/plan`, `POST /api/v1/agent/validate`, `POST /api/v1/agent/execute`, dan stream event.
- Pastikan LLM tidak pernah menerima credential plaintext dan tidak memiliki primitive SSH langsung.

## Kontrak Safety

- Frontend tidak boleh menjalankan SSH langsung.
- Frontend tidak boleh menyimpan password/token/plaintext secret.
- AI provider tidak boleh diakses langsung dari frontend.
- LLM tidak boleh menjalankan SSH langsung; LLM hanya menghasilkan intent/rencana yang divalidasi backend.
- Semua write/delete/reload/destroy/restore harus punya confirmation.
- Config apply harus punya plan id dan approval identity.
- Direct vendor write endpoint sebaiknya tetap berada di balik policy check.
- Untuk semua response error `502`, tampilkan error operasional yang jelas, bukan hanya generic bad gateway.

## Kontrak Agent Event UI

Frontend `/agent`, `/tasks`, dan `/terminal` harus siap menerima typed events dari backend. Jenis card/event minimal:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

Contoh event:

```json
{
  "type": "task_progress",
  "task_id": "task-182",
  "step": "backup",
  "status": "success",
  "message": "Running configuration backed up"
}
```

UI harus merender event sebagai state operasional, bukan hanya Markdown mentah.

## File Frontend Yang Akan Diubah Saat Integrasi

- `src/api/network/index.ts`
- `src/api/network/network-data.ts`
- `src/types/network.ts`
- pages di `src/views/*`
- komponen status/error/loading di `src/components/network/*`

Target akhir: MSW hanya dipakai untuk dev/demo, sedangkan mode normal memakai FastAPI `/api/v1`.

## Status Integrasi Final (2026-08-25)

### Frontend Pages Terhubung ke Backend

| Page | Backend Endpoint | Status |
|------|------------------|--------|
| Dashboard | /api/v1/devices, /api/v1/monitoring | ✅ Complete |
| Devices | /api/v1/devices/* | ✅ Complete |
| Device Detail | /api/v1/devices/*, /api/v1/interfaces | ✅ Complete |
| Terminal | /api/v1/terminal/* + WebSocket | ✅ Complete |
| Configurations | /api/v1/config/* | ✅ Complete |
| GNS3 | /api/v1/gns3/* | ✅ Complete |
| Tasks | /api/v1/tasks | ✅ Complete |
| Alerts | /api/v1/alerts | ✅ Complete |
| Backups | /api/v1/backups | ✅ Complete |
| Credentials | /api/v1/credentials | ✅ Complete |
| Settings | /api/v1/settings | ✅ Complete |
| Discovery | /api/v1/discovery | ✅ Complete |
| Agent | /api/v1/agent/* + SSE | ✅ Complete |
| Containerlab | /api/v1/containerlab/* | ✅ Complete |
| Audit | /api/v1/audit | ✅ Complete |
| Topology | /api/v1/topology | ✅ Complete |

### Backend Modules (19 total)

| Module | Status |
|--------|--------|
| devices | ✅ |
| config | ✅ |
| monitoring | ✅ |
| topology | ✅ |
| audit | ✅ |
| mikrotik | ✅ |
| cisco | ✅ |
| gns3 | ✅ |
| policy | ✅ |
| terminal | ✅ |
| tasks | ✅ |
| alerts | ✅ |
| backups | ✅ |
| agent | ✅ |
| credentials | ✅ |
| settings | ✅ |
| discovery | ✅ |
| containerlab | ✅ |
| ninerouter | ✅ |

### AI Integration

| Feature | Status |
|---------|--------|
| OpenAI Provider | ✅ |
| Anthropic Provider | ✅ |
| Ollama Provider | ✅ |
| 9Router Provider | ✅ |
| Web Search (9Router) | ✅ |
| Web Fetch (9Router) | ✅ |
| Free Models (Go/Zen) | ✅ |
| Agent Tools (8 tools) | ✅ |

### Real-time Features

| Feature | Protocol | Status |
|---------|----------|--------|
| Terminal Streaming | WebSocket | ✅ |
| Agent Events | SSE | ✅ |
| Task Updates | SSE | ✅
