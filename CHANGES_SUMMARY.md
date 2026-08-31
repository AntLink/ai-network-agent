# Summary of Changes - JSON Response Format for All Backend Endpoints

## Objective
Convert ALL backend endpoints (Cisco, MikroTik, Switch) to return structured JSON instead of raw CLI text for easier frontend data management.

## Follow-up Fix - Agent Chat History Persistence
The AI agent chat UI was stabilized after a follow-up regression where the previous assistant bubble could render empty and older history could disappear after refresh.

### What Was Fixed

- Backend session message storage now upserts by message ID instead of blindly appending duplicates.
- Frontend agent runtime now replays the stored session transcript back into the thread on reload.
- Assistant bubble rendering now falls back to persisted session text when runtime content is temporarily empty.
- Follow-up runs no longer wipe earlier messages when the session is refreshed.

### Validation

- `npm run lint` passed
- `npm run build` passed

## Frontend Follow-up
The device detail UI was updated after the backend normalization to make the frontend more operationally useful:

- Added vendor-aware device detail layouts for Cisco router, Cisco switch, and MikroTik router.
- Added a loading overlay and skeleton state when opening `device -> details`.
- Added toast notifications for success, failure, and timeout states.
- Rendered detail tabs and summary blocks as tables/cards instead of raw preformatted output where possible.

## Changes Made

### 1. Cisco Driver (`backend/app/drivers/cisco/driver.py`)
- **Added import**: `from .parser import IOSParser`
- **Updated all read methods** to use `IOSParser.parse_*` methods and return `{"data": parsed, "raw": raw}` format:
  - `identify()` - uses `IOSParser.parse_version()`
  - `get_facts()` - uses `IOSParser.parse_version()`
  - `get_interfaces()` - uses `IOSParser.parse_interfaces_brief()`
  - `get_interfaces_detail()` - uses `IOSParser.parse_interfaces_detail()`
  - `get_routes()` - uses `IOSParser.parse_routes()`
  - `get_arp()` - uses `IOSParser.parse_arp()`
  - `get_cpu_memory()` - uses `IOSParser.parse_cpu_memory()`
  - `get_acls()` - uses `IOSParser.parse_access_lists()`
  - `get_cdp_neighbors()` - uses `IOSParser.parse_cdp_neighbors()`
  - `get_nat_translations()` - uses `IOSParser.parse_nat_translations()`
  - `get_startup_config()` - returns `{"data": raw, "raw": raw}`
  - `get_logs()` - returns `{"data": raw, "raw": raw}`
  - `get_config()` - returns `{"data": raw, "raw": raw}`
  - `backup()` - returns `{"data": raw, "raw": raw}`
  - `ping_tool()` - returns parsed ping statistics with success_rate and loss_percent
  - `traceroute_tool()` - returns `{"data": raw, "raw": raw}`

### 2. Cisco Parser (`backend/app/drivers/cisco/parser.py`)
- **Already existed** with comprehensive parser methods:
  - `parse_interfaces()` - for TextFSM output
  - `parse_static_routes()` - for plain-text route output
  - `parse_cpu_memory()` - for CPU and memory statistics
  - `parse_interfaces_brief()` - for `show ip interface brief`
  - `parse_interfaces_detail()` - for `show interfaces`
  - `parse_routes()` - for `show ip route`
  - `parse_arp()` - for `show ip arp`
  - `parse_version()` - for `show version`
  - `parse_access_lists()` - for `show access-lists`
  - `parse_cdp_neighbors()` - for `show cdp neighbors detail`
  - `parse_nat_translations()` - for `show ip nat translation`

### 3. MikroTik Parser (`backend/app/drivers/mikrotik/parser.py`)
- **Newly created** with parser methods for MikroTik RouterOS:
  - `parse_identity()` - for `/system identity print`
  - `parse_resource()` - for `/system resource print`
  - `parse_interfaces()` - for `/interface print detail`
  - `parse_routes()` - for `/ip route print detail`
  - `parse_ip_addresses()` - for `/ip address print detail`
  - `parse_config()` - for `/export terse`
  - `parse_system_users()` - for `/user print detail`
  - `parse_dhcp_server()` - for `/ip dhcp-server print detail`

### 4. MikroTik Driver (`backend/app/drivers/mikrotik/driver.py`)
- **Added import**: `from .parser import MikroTikParser`
- **Updated all read methods** to use `MikroTikParser.parse_*` methods where applicable and return `{"data": parsed, "raw": raw}` format:
  - `identify()` - uses `MikroTikParser.parse_identity()` and `MikroTikParser.parse_resource()`
  - `get_facts()` - uses `MikroTikParser.parse_resource()`
  - `get_interfaces()` - uses `MikroTikParser.parse_interfaces()`
  - `get_routes()` - uses `MikroTikParser.parse_routes()`
  - `get_config()` - uses `MikroTikParser.parse_config()`
  - `get_ip_addresses()` - uses `MikroTikParser.parse_ip_addresses()`
  - `get_dhcp_server()` - uses `MikroTikParser.parse_dhcp_server()`
  - `get_system_users()` - uses `MikroTikParser.parse_system_users()`
  - `backup()` - uses `MikroTikParser.parse_config()`
  - **All other methods** - updated to return `{"data": raw, "raw": raw}` for consistency

### 5. Generic Driver (`backend/app/drivers/generic/driver.py`)
- **Updated methods** to return `{"data": raw, "raw": raw}` format:
  - `identify()` - returns `{"vendor": "unknown", "data": raw, "raw": raw}`
  - `get_facts()` - returns `{"vendor": "unknown", "data": raw, "raw": raw}`

### 6. Monitoring Endpoint (`backend/app/api/v1/endpoints/monitoring.py`)
- **Updated** to use parsed data from drivers when available:
  - Now checks for `"data"` key in driver responses and uses it if available
  - Falls back to `"raw"` key if parsed data is not available
  - Returns structured JSON with:
    - `cpu_memory` - parsed CPU and memory statistics
    - `interfaces` - parsed interface data
    - `routes` - parsed route data
    - `facts` - parsed device facts (version, uptime, etc.)
    - `health` - device health check

## Response Format

All endpoint responses now follow this structure:

```json
{
  "data": <parsed_structured_json>,
  "raw": "<original_cli_text>"
}
```

Where:
- `data` - Contains structured JSON parsed from CLI output (when parser is available)
- `raw` - Contains the original CLI text output (for debugging and fallback)

For methods without specific parsers (e.g., config backups, logs), both `data` and `raw` contain the same text value.

## Benefits

1. **Frontend-Friendly**: Structured JSON is easier to display in tables and UI components
2. **Consistent API**: All endpoints return the same response format
3. **Backward Compatible**: Raw CLI text is still available for debugging
4. **Extensible**: New parsers can be added without breaking existing clients
5. **Better Error Handling**: Frontend can detect and handle parsing failures gracefully

## Testing

All modules have been verified to import correctly:
- ✅ Cisco driver
- ✅ Cisco parser
- ✅ MikroTik driver
- ✅ MikroTik parser
- ✅ Generic driver
- ✅ Monitoring endpoint

## Next Steps

1. Test each endpoint with real devices to verify parsing accuracy
2. Add more specific parsers for additional commands as needed
3. Update frontend to use the structured `data` field instead of `raw`
4. Add validation for parsed data structures

## 2026-08-30 — Console & SSH Stabilization + Approval Flow

### Konsol telnet GNS3
- Lock per (host, port) agar dua sesi tidak menabrakkan karakter di console yang sama.
- Pager dimatikan otomatis sebelum command (`terminal length 0` utk IOSv, `terminal pager 0` utk ASAv, terdeteksi dari metadata node GNS3); cleanup marker `--More--`/`<--- More --->`/`---- More ----` di mana pun.
- Login robust: fallback kredensial (`admin123`/empty), anti-loop, tahan redraw prompt RouterOS, `enable` sekali, keluar dari config-mode terwarisi (Ctrl-Z).
- `run_scripted()` + tool MCP `net_console_interactive` untuk prompt interaktif (keygen crypto, copy, dsb).

### Alur approval eksplisit
- Backend: `list_pending_approvals()` & `approve_command(approval_id, approved_by)`; endpoint `GET /tools/pending-approvals`, `POST /tools/approve`.
- MCP: `net_list_pending_approvals`, `net_approve_command`.

### SSH transport
- `apply()` Cisco kini memakai `configure terminal` (sebelumnya EXEC batch → command config gagal di SSH).
- `AsaDriver.exec_logged()` agar `show` read via exec.
- `load_dotenv(.env)` → kredensial per-device terbaca driver.

### Lab & inventory
- SSH + key RSA aktif di router/switch/ASAv; DHCP/statik IP di subnet cloud; eksplorasi via SSH transport terverifikasi (facts/interfaces/routes/config).
- Perbaiki collision port console: `pc-vm-1`/`pc-attacker` (5007→switch) & `fw-asav` (5001→router) tidak lagi menunjuk console perangkat lain.

## 2026-08-30/31 — Vendor drivers (Aruba/ASA/Ruijie/FortiGate), endpoint parity, lab lintas-vendor, pagination Devices

### Driver & endpoint vendor baru
- **Aruba AOS-CX** `backend/app/drivers/aruba/` (SSH + console GNS3, parser version/system/interfaces/vlan/route/arp/config) + endpoint `/aruba` (resources, interface, l2 vlan/access/trunk, static-route, tools, config/save).
- **ASA (ASAv)** — endpoint `/asa` (resources, interface/address, acl, nat, static-route, config/save) untuk `AsaDriver` yang sudah ada.
- **Ruijie RGOS** `backend/app/drivers/ruijie/` (console, RG-NSE Router/switch V1.06) + endpoint `/ruijie` + integrasi agent (normalize/label/noc-profile/topic-command).
- **Fortinet FortiOS** `backend/app/drivers/fortinet/` (console; login admin, parser structured interface/route/static-route; retry anti-flaky; config satu-sesi tanpa `configure terminal`) + endpoint `/fortigate` (resources, commands/run, interface/address ±DELETE, hostname, static-route POST/GET/DELETE).
- Factory: registrasi vendor `aruba`, `ruijie`, `fortinet`.
- `main.py`: exception handler console transport (502/504/503) + `ArubaCLIError` → 422 untuk error device yang utuh.

### Perbaikan shared (transport console)
- `PROMPT_RE` kini mengakui hostname ber-hiphen dan spasi sebelum `#` (kasus `FortiFirewall-VM64-KVM # `) agar login console tak timeout.
- Prompt konfirmasi `(y/n)` dijawab `n` (tidak macet di dialog AOS-CX/ASAv).
- RouterOS: `print ... where ...` tanpa suffix `without-paging` (output jadi kosong kalau kepaksa).
- `mcp-bridge`: hapus truncation `detail[:400]` pada error backend.

### GNS3 / lab lintas-vendor
- Template vJunos-Router & Switch 26.2R1.7 (digambar upload); FortiGate (FortiOS 7.6.7 resmi, admin/FortiLab123! first-login policy); HPE VSR1001 dicek setara resmi.
- Instal `ovmf` di VM GNS3 untuk UEFI; diagnosis vJunos-Evolved (tidak stabil di nested KVM → template dihapus).
- Wiring & ping: Aruba↔CHR↔ASAv 0% loss; **Ruijie→MikroTik 5/5** (SVI vlan1); **Aruba↔FortiGate 5/5** dua arah via SW1 1/1/7↔FG port1.
- Console FG output utuh (pager `--More--` otomatis dijawab transport; `show full-configuration` ±365 KB).

### Frontend
- Halaman Devices: **pagination server-side** (`/devices?page=&limit=`), Select ukuran halaman, Prev/Next — sejajar pola Audit; paging di dalam `CardContent`.
- `useDevicesPage`/`loadBackendDevicesPage` (join batch-status) + `DeviceStatusTable.footer` untuk kontrol paging.

### Testing & status
- Unit test parser Aruba (`tests/test_aruba_parser.py`) lulus; endpoint read/write/delete vendor terverifikasi live.

## 2026-08-31 — Web Search Tavily via 9Router (true provider + multi-key failover)

Detail: `logs/SESSION-2026-08-31-web-search-tavily.md`

### Konteks
- Sebelumnya `/v1/search` selalu gagal (`/v1/models/web` kosong, "Unknown provider")
  karena tidak ada provider web-search terhubung; agent jatuh ke fallback model
  `cx/gpt-5.6-sol` (search:true).
- `oc/big-pickle` dicek: terdaftar tapi **tidak** search-capable (halusinasi —
  tanggal salah & URL 404). Bukan kandidat pengganti.

### Perbaikan
- **9Router dashboard:** tambah provider **Tavily** + koneksi kedua (failover),
  total 2 akun aktif (`Free-azlan`, `Free-moh.fauzan.azim@gmail.com`).
- **`backend/app/agent/providers.py`**: default `web_search()`/`web_fetch()`
  `search-combo`/`fetch-combo` → **`tavily`** (baris 238, 256).
- **Root `.env`**: `NINEROUTER_SEARCH_MODEL=tavily`, `NINEROUTER_FETCH_MODEL=tavily`.

### Multi-key failover
- Dari source 9Router `/v1/search` (0.5.55): loop pemilih akun (`c1(provider, triedSet)`)
  otomatis pindah ke key lain saat satu key rate-limited/kuota habis (429).
- Failover real-time antar key terjadi di sisi 9Router tanpa ubah `.env`/kode backend.

### Validasi
- `/api/v1/ninerouter/status` → `connected`.
- `/api/v1/ninerouter/search` → provider **tavily**, hasil live Aug 2026.
- `/api/v1/agent/chat` ("cari di web: berita terbaru Nvidia") → jawaban live
  (Q2 FY27 $96,2 M, Jetson Orin Nano 2, Groq 3 LPX) + sumber URL.
- `oc/big-pickle` vs `cx/gpt-5.6-sol`/Tavily: yang pertama halusinasi, sisanya live.

## 2026-08-31 — Self-host SearXNG (free tier unlimited) sebagai search provider

Detail: `logs/SESSION-2026-08-31-web-search-tavily.md`

### Konteks
- 9Router punya provider `searxng` (freeTier, noAuth, cost 0, quota 999.999/bln),
  tetapi butuh instance SearXNG yang berjalan (`SEARXNG_URL || localhost:8888/search`).

### Perubahan
- **Install Docker Desktop** (silent, WSL2 backend) karena sebelumnya tidak ada.
- **`searxng/docker-compose.yml`** — image `searxng/searxng`, port `8888:8080`.
- **`searxng/config/settings.yml`** — enable `search.formats:[html,json]` (wajib utk 9Router).
- **`searxng/.env`** — `SEARXNG_SECRET`.
- Dashboard 9Router: aktifkan provider SearXNG.
- **`.env`**: `NINEROUTER_SEARCH_MODEL=searxng`, `NINEROUTER_FETCH_MODEL=tavily`.
- **`providers.py:238`**: default web_search → `searxng` (fetch tetap `tavily`,
  karena SearXNG tanpa webFetch).

### Validasi
- `POST /api/v1/ninerouter/search` → provider **searxng**, cost **$0**, hasil live.
- `POST /api/v1/agent/chat` ("cari di web AI") → jawaban live + URL (detik/CNN/SINDO).
- `POST /api/v1/ninerouter/fetch` → provider **tavily** (extract).
- Kombinasi: search gratis unlimited (SearXNG) + extract by Tavily.
