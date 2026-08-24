# AI Network Agent V3 Architecture

```text
User
  |
  v
OpenCode Agents  (+ Swagger UI /docs)
  |
  v
.opencode/tools/*.ts
  |
  | HTTP
  v
FastAPI Backend (uvicorn app.main:app --port 8000)
  |
  +-- API v1 (/api/v1)
  |    +-- /devices        : list, identify, facts, interfaces, routes, config, vlans, services, disk, memory, ntp
  |    +-- /config         : plan / apply / rollback (stub, belum persist)
  |    +-- /monitoring     : real-time metrics
  |    +-- /topology       : LLDP/CDP mapping
  |    +-- /audit          : event trail
  |    +-- /mikrotik       : vendor-specific suite (88 endpoint total saat ini)
  |
  +-- Services        (device_service)
  +-- Repositories    (inventory/devices.json)
  +-- Policy          (risk/approval)
  +-- Drivers
  |    +-- MikroTik   : facts, interfaces, routes, vlan, bridge,
  |    |                ip/firewall (filter, nat, mangle, address-list),
  |    |                routing (static, ospf, bgp), dhcp/pool, dns/ntp,
  |    |                system (identity, users, logging), wireless,
  |    |                hotspot (server/profile/user/user-profile/active/
  |    |                hosts/ip-binding/walled-garden),
  |    |                PPP & VPN tunnel (secret CRUD, active, kick;
  |    |                server+client l2tp/pptp/sstp/ovpn/pppoe; pppoe instance)
  |    +-- Cisco
  |    +-- Linux      (debian / rhel / embedded)
  |    +-- Generic
  |
  +-- Transports
       +-- SSH   (asyncssh; connect 10s / command 20s timeout)
       +-- REST  (planned)
       +-- NETCONF (planned)
  |
  v
Network Devices

Inventory terdaftar:
- mikrotik-rb5009-tci-upt-pontianak  36.88.39.234  RB5009UG+S+   (hub L2TP/IPsec, user: ozan)
- mikrotik-rb951ui-2hnd-home-bagem   192.168.30.1  RB951Ui-2HnD  (client wifi+l2tp, user: admin)
- linux-embedded                     192.168.162.20 CSMS-SINGKAWANG
- linux-debian                       172.23.193.80 fauzan
- linux-ubuntu                       192.168.210.51 ubuntu
- cisco-iosv-r1                      172.22.45.249 IOSv 15.6(2)T    (lab GNS3)
- mikrotik-chr-mk-1                  172.22.37.168 CHR 7.22.1       (lab GNS3)

Lab GNS3 multi-vendor (R1/R2/SW1/SW2/MK1 + 5 VPCS): lihat
`logs/LAB-GNS3-REFERENCE.md` (topologi, port konsol, aturan IDE,
API controller) dan `logs/SESSION-2026-08-23-gns3-lab-recovery.md`.
Suite pengujian: `backend/grand_finale_ping.py` (8/8 lulus).

Cisco driver refactoring (2026-08-24): lihat `logs/SESSION-2026-08-24-cisco-driver-refactor.md`
untuk detail perbaikan duplikasi kode dan analisis SSH timeout.

## API Response Format Standardization (2026-08-24)

Semua driver backend sekarang mengimplementasikan format response JSON terstruktur:

```json
{
  "data": <parsed_structured_json>,
  "raw": "<original_cli_output>"
}
```

### WRITE endpoints (POST/DELETE/PATCH) — 2026-08-24

Semua write endpoint dinormalisasi via `write_response()` helper
(`backend/app/api/v1/endpoints/helpers.py`):

```json
{
  "status": "applied",
  "operation": "create_vlan",
  "success": true,
  "output": ""
}
```

- `status`: applied | deleted | saved | committed | failed
- `operation`: nama method driver
- `success`: boolean
- `output`: raw device output (biasanya kosong / warning device)
- Endpoint TIDAK double-wrap (return driver result langsung)

### Driver Implementation:
- **Cisco IOS**: `backend/app/drivers/cisco/driver.py` + `parser.py`
  - 15+ read methods dengan parser khusus
  - Parse output: version, interfaces, routes, ARP, CPU/memory, ACLs, CDP, NAT
- **MikroTik RouterOS**: `backend/app/drivers/mikrotik/driver.py` + `parser.py`
  - 25+ read methods dengan parser khusus
  - Parse output: identity, resource, interfaces, routes, IP addresses, users, DHCP
- **Generic SSH**: `backend/app/drivers/generic/driver.py`
  - Format standar untuk perangkat tidak dikenal

### Monitoring Endpoint (`/api/v1/monitoring/{device_id}`)
Menggunakan data terstruktur dari driver dengan fallback ke raw text:
- `cpu_memory`: CPU utilization dan memory statistics
- `interfaces`: Status dan statistik interface
- `routes`: Tabel routing
- `facts`: Informasi device (versi, uptime, dll)
- `health`: Health check device
```

`.opencode/skills/` is the AI knowledge and safety layer.
`backend/` is the executable network control-plane.

## Konvensi penting

- **Device ID** mengikuti pola `mikrotik-<board>-<identity>` sesuai `/system identity`
  dan `/system resource board-name` device asli.
- **Kredensial** dibaca dari `backend/.env` dengan prefix `{ID_UPPER_WITH_UNDERSCORE}_USERNAME/_PASSWORD`,
  fallback ke `NETWORK_USERNAME/NETWORK_PASSWORD`.
- **Safety flow** untuk perubahan konfigurasi: backup (`/export terse` -> `backups/*.rsc`)
  -> approval user -> apply -> verify. Semua perintah tercatat via `log_event` (audit).
- **Swagger UI**: http://127.0.0.1:8000/docs (aset dari CDN jsdelivr; klik "Try it out"
  sebelum mengisi parameter).

## Status implementasi MikroTik API

| Area | Endpoint | Status |
|------|----------|--------|
| Resources read-only (ip, route, firewall, dhcp, wireless, hotspot, ppp, tunnel) | GET `/mikrotik/{id}/resources/*` | OK |
| IP/VLAN/Bridge/route/firewall/dhcp/interface/system/wireless write | POST/PATCH/DELETE | OK |
| Hotspot management | POST/PATCH/DELETE + reset/kick | OK |
| PPP secret/profile/active/kick | POST/PATCH/DELETE + GET | OK |
| Tunnel server set (l2tp/pptp/sstp/ovpn) + pppoe instance | PATCH/POST/DELETE | OK |
| Tunnel client CRUD + enable/disable/monitor (5 protokol) | POST/DELETE/GET | OK |
| Raw command runner | POST `/commands/run` | OK |
| Config plan persist/validate/rollback | `/config/*` | STUB (belum persist) |
