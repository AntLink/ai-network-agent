# AI Network Agent V3 — OpenCode Project Structure

This package restructures the supplied V2 generator output into a project-local OpenCode layout.

## Layout
- `.opencode/skills/` — original supplied skills / vendor knowledge.
- `.opencode/agents/` — planner, operator, auditor, troubleshooter.
- `.opencode/tools/` — original custom OpenCode tools (currently mock/stub implementations from V2).
- `src/drivers/` — vendor-specific runtime logic.
- `src/transports/` — SSH / REST / NETCONF transport layer.
- `src/parsers/` — vendor output parsers.
- `src/policy/` — policy/risk logic.
- `src/storage/` — backup and audit persistence.
- `inventory/` — device inventory; copy `devices.example.json` to `devices.json`.
- `backups/` — configuration backups.
- `logs/` — immutable/audit-style event logs.
- `tests/` — test fixtures and unit tests.

## Important
The supplied OpenCode custom tools are preserved as provided. They are architecture stubs and return mocked data; they do not yet connect to real devices. Implement the runtime transports/drivers and then wire the `.opencode/tools/*.ts` files to them before production use.

## Suggested flow
User -> network-planner -> read-only tools -> plan/validate -> approval -> network-operator -> policy/backup/apply/verify -> rollback on failure.


## FastAPI Backend

Python FastAPI control-plane is included in `backend/` and is intended to be called by OpenCode custom tools.

Run: `cd backend && python -m uvicorn app.main:app --port 8000`
Docs: http://127.0.0.1:8000/docs

### MikroTik API (vendor suite)
`/api/v1/mikrotik/{device_id}/...` — 88 endpoint: read-only resources, config write
(ip/vlan/bridge/firewall/route/dhcp/system/wireless), hotspot management,
PPP (secret/profile/active/kick) dan VPN tunnel server+client untuk
l2tp/pptp/sstp/ovpn/pppoe. Lihat `ARCHITECTURE.md` untuk rincian dan
`logs/SESSION-2026-08-22-mikrotik.md` untuk riwayat implementasi + perubahan live.

Device ID mengikuti `mikrotik-<board>-<identity>`; kredensial per device di `backend/.env`.

## Cisco Driver Refactoring (2026-08-24)

Cisco IOS driver telah direfactor untuk menghilangkan duplikasi kode:
- `backend/app/drivers/cisco/base.py` - Common utilities (credential management, IP parsing)
- Semua driver (driver.py, netmiko_driver.py, connection.py) sekarang menggunakan base.py
- Lihat `logs/SESSION-2026-08-24-cisco-driver-refactor.md` untuk detail lengkap.

## API Response Format Standardization (2026-08-24)

Semua endpoint backend (Cisco, MikroTik, Generic) sekarang mengembalikan format JSON terstruktur:

```json
{
  "data": {"structured": "parsed_json_data"},
  "raw": "original_cli_text_output"
}
```

### Manfaat:
- **Frontend-friendly**: Data terstruktur mudah ditampilkan dalam tabel dan UI
- **Konsistensi**: Semua endpoint menggunakan format yang sama
- **Backward compatible**: Teks CLI asli masih tersedia untuk debugging
- **Tahan error**: Frontend dapat mendeteksi dan menangani kegagalan parsing

### Parser yang Tersedia:
- **Cisco**: `backend/app/drivers/cisco/parser.py` - 10+ parser untuk perintah show *
- **MikroTik**: `backend/app/drivers/mikrotik/parser.py` - 8+ parser untuk perintah /system, /interface, /ip *

Lihat `CHANGES_SUMMARY.md` untuk detail lengkap semua perubahan.
