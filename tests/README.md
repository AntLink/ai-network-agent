# Tests

Add mocked vendor outputs and unit tests here before production use.

---

## API Response Format (standardisasi 2026-08-24)

**Semua endpoint FastAPI return JSON terstruktur** (bukan raw CLI):

| Tipe | Format |
|------|--------|
| **READ (GET)** | `{"data": <structured list/dict>, "raw": "<cli text>"}` |
| **WRITE (POST/DELETE/PATCH)** | `{"status": "applied", "operation": "<method>", "success": true, "output": ""}` |

- Write normalized via `write_response()` di `backend/app/api/v1/endpoints/helpers.py`
- `data` berisi hasil parsing (parser di `drivers/<vendor>/parser.py`)
- `raw` selalu dipertahankan untuk debugging

## Skrip Pengujian & Diagnostik Lab GNS3

Skrip operasional berada di `backend/` (dijalankan dari folder `backend/`,
butuh `python -u -X utf8` agar output real-time di Windows). Referensi
lengkap lab: `logs/LAB-GNS3-REFERENCE.md`, log sesi:
`logs/SESSION-2026-08-23-gns3-lab-recovery.md`.

### Suite pengujian akhir (jalankan untuk verifikasi lab)

| Skrip | Fungsi | Hasil 2026-08-23 |
|-------|--------|------------------|
| `backend/grand_finale_ping.py` | 8 tes ping end-to-end antar PC (GW, lintas situs, VLAN, LAN-M) | **8/8 SUKSES** |
| `backend/verify_routers_ide.py` | Identitas + interface + OSPF neighbor + startup-config R1/R2 via konsol | semua lengkap |
| `backend/verify_switches_now.py` | Flash/VLAN/trunk/SVI/startup SW1-SW2 + ping ringkas | OK setelah fix access-port |

### Unit tests & smoke (Phase A+B hardening)

| Skrip | Fungsi |
|-------|--------|
| `tests/test_phase_ab.py` | 11 unit test mocked: dialog konsol, guard ENTER-kosong-di-password, verifikasi persistensi save_config, deteksi flash rusak, fallback SSH legacy, wiring inventory. Jalur: `python -m pytest tests -q` |
| `backend/smoke_phase_ab.py` | Smoke test LIVE ke lab: console_exec R1, health flash, save_config verified |
| `backend/trace_paths.py` | Traceroute aktual antar PC untuk dokumentasi jalur OSPF |

### Phase E (L2 API) & D (config transaction)

- L2 endpoints ditambah di `cisco.py`: `POST /l2/vlan`, `DELETE /l2/vlan/{id}`, `POST /l2/access`, `POST /l2/trunk`, `POST /l2/subinterface`, `POST /l2/svi`.
- Config transaction generic endpoints di `config.py`: `POST /config/plan`, `POST /config/apply`, `POST /config/rollback` (menggunakan `driver.config_transaction`).
- Skema request baru di `schemas/cisco.py` (VlanCreate, AccessPortSet, TrunkPortSet, SubinterfaceCreate, SviSet) dan `schemas/config.py` (ConfigPlanRequest dengan verify & save_on_success).

### Integration tests (Phase E - live lab)

| File | Cakupan |
|---|---|
| `tests/test_phase_e_l2_integration.py` | 8 tes live: VLAN create/access/trunk di SW1/SW2, SVI, subinterface R1/R2, config transaction (atomic commit + rollback via `configure replace` dengan fallback konsol). Jalankan: `python -m pytest tests/test_phase_e_l2_integration.py -v` (butuh lab GNS3 hidup). |

### Konfigurasi (dipakai membangun lab; reusable)

| Skrip | Fungsi |
|-------|--------|
| `phase1_console.py` / `phase1_recovery.py` | Base config router via konsol (tangani dialog awal IOS) |
| `ospf_console.py` | Push OSPF R1/R2 via konsol slow-send |
| `full_config_switches.py` | Konfigurasi penuh switch (hostname/SSH/vlan/access/trunk/SVI) |
| `repair_sw_l2_v2.py` | Contoh otomasi switch prompt-synced (anti telan-input) |
| `finalize_sw2_v3.py` | State machine konsol: aman terhadap prompt `Password:`/[confirm] |
| `fix_access_final.py` | Perbaiki access-port + bukti startup-config lengkap |
| `rebuild_routers_full.py` | Rebuild total router dari factory (base+OSPF+persistensi) |
| `pc_rebuild_and_verify.py` | Set ulang IP semua VPCS + verifikasi OSPF + ping |

### Perbaikan infrastruktur GNS3

| Skrip | Fungsi |
|-------|--------|
| `fix_disk_ide_minimal.py`, `fix_router_ide.py` | Ubah `hda_disk_interface` sata→ide via controller API (PUT minimal body) |
| `rebuild_sockets.py` | Stop/start node via API — perbaiki link sepihak (ubridge) |
| `list_links.py` | Peta kabel aktual dari GET `/projects/{pid}/links` |
| `reload_sw1_capture.py` | Reload node sambil menangkap log boot (diagnosis flash) |

### Diagnostik (pola yang layak ditiru)

| Skrip | Teknik |
|-------|--------|
| `counter_compare.py` | Bandingkan counter paket 2 ujung link → deteksi link mati sepihak |
| `micro_l2_test.py` | clear mac-table → kirim frame → cek klasifikasi VLAN & learning |
| `check_access_ports.py` | Audit `switchport access vlan` vs vlan brief |
| `raw_diag_ping.py` / `raw_dump_r1_pc.py` | Dump mentah konsol tanpa filter parsing |
| `debug_sw2_console.py` | Dump byte-level interaksi telnet konsol |
| `probe_vlan_error.py` | Tangkap teks error persen (%) yang disembunyikan parser |
| `check_vm_disks.py`, `check_qemu_cmd.py`, `check_backing2.py` | Forensik disk dari dalam GNS3 VM (SSH gns3) |
| `find_gns3_api.py` | Temukan port API gns3server di VM |

### Pola kode inti (salin-tempel aman)

```python
# Prompt-synced console I/O - LIHAT implementasi lengkap:
#   backend/finalize_sw2_v3.py  (class Console)
#   backend/phase1_recovery.py  (slow() + clear_dialog())
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")
```

Aturan emas:
1. Kirim command hanya saat prompt siap; tunggu prompt kembali.
2. JANGAN kirim ENTER saat baris terakhir berakhir `:` (`Password:`).
3. Selalu akhiri dengan bukti `show startup-config`.
