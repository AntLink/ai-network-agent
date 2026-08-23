# Session Log — 2026-08-22: MikroTik Management API & Konfigurasi Live

Durasi kerja: satu sesi (API + operasi live 2 device MikroTik)
Operator: user (mohfa) + opencode agent

---

## 1. Pengembangan Backend (AI Network Agent)

### 1.1 Modul API MikroTik baru
| File | Perubahan |
|------|-----------|
| `backend/app/drivers/mikrotik/driver.py` | Ekstensi besar: read-only resources, write config, hotspot, PPP/tunnel suite (~100 metode) |
| `backend/app/schemas/mikrotik.py` | BARU — ~30 model Pydantic request |
| `backend/app/api/v1/endpoints/mikrotik.py` | BARU — router vendor-specific |
| `backend/app/api/v1/router.py` | Registrasi `include_router(mikrotik.router, prefix="/mikrotik")` |

Total endpoint akhir: **88 path** (`/api/v1/mikrotik/{device_id}/...`).

Rilis bertahap dalam sesi ini:
1. **v1 core** (43 endpoint): ip-address, vlan, bridge(+port), static-route,
   firewall filter/nat/address-list, dhcp-server, ip-pool, interface set/enable/disable,
   system identity/users/ntp/dns, wireless security-profile, commands/run, monitoring.
2. **Hotspot** (+17): servers, profiles, users, user-profiles, active, hosts,
   ip-bindings, walled-garden; CRUD voucher, kick, reset-counters(-all).
3. **PPP & VPN Tunnel** (+12 path): ppp secret CRUD + active + kick;
   server l2tp/pptp/sstp/ovpn (status + set enabled/ipsec-secret/profile);
   instance pppoe-server; client CRUD enable/disable/monitor utk
   l2tp/pptp/sstp/ovpn/pppoe (pppoe pakai `interface=`, lainnya `connect-to=`).

### 1.2 Isu Swagger UI
- Laporan: field `device_id` read-only di `/docs` (GET/POST/DELETE sama).
- Diagnosis: OpenAPI schema benar; penyebab tombol **"Try it out"** belum diklik.
- Sempat diterapkan serving aset swagger lokal (`backend/static/swagger-ui/`) lalu
  **dikembalikan ke default CDN** setelah konfirmasi penyebab. Tidak ada perubahan final di main.py.

---

## 2. Onboarding Device Baru

Device: 192.168.30.1, admin/815m1ll4h.
- Teridentifikasi: identity `HOME-BAGEM`, board **RB951Ui-2HnD**, RouterOS 6.49.11.
- Masuk inventory awal sebagai `mikrotik-rb951`.

## 3. Rename ID Inventory (sesuai identity + board name)

Temuan penting: device 36.88.39.234 yang lama terdaftar "rb4011" ternyata **RB5009UG+S+**
(identity `TCI UPT PONTIANAK`, arm64).

| Lama | Baru |
|------|------|
| mikrotik-rb4011 / router-core | `mikrotik-rb5009-tci-upt-pontianak` |
| mikrotik-rb951 / rb951-office | `mikrotik-rb951ui-2hnd-home-bagem` |

Ikut diubah: `inventory/devices.json`, prefix kredensial `backend/.env`
(`MIKROTIK_RB5009_TCI_UPT_PONTIANAK_*` = ozan, `MIKROTIK_RB951UI_2HND_HOME_BAGEM_*` = admin).
Verifikasi identify kedua device: OK.

---

## 4. Perubahan Konfigurasi Live

### 4.1 RB951Ui-2HnD (HOME-BAGEM, 192.168.30.1)
a) **WiFi scan** wlan1 (mode station, SSID aktif saat itu "BALE NET").
   Ditemukan: BALE NET (-29 dBm), CV.ASTR (-58), ZTE_2.4G (-65), aula/NABILA03/
   Pendopo/VICIDINO (lemah).

b) **IP wlan1 dinamis (DHCP)** — backup dulu:
   - Sebelum: statis `192.168.11.201/24` → SALAH subnet (BALE NET sebenarnya
     192.168.210.0/24); internet via wifi tidak pernah jalan.
   - Apply: `dhcp-client add interface=wlan1 add-default-route=yes use-peer-dns=yes`
     → bound `192.168.210.11/24` gw `192.168.210.1`.
   - Hapus IP statis lama (find dengan quote diperlukan).
   - Verifikasi: ping 8.8.8.8 = 3/3 @44ms.

c) **L2TP client ke hub**:
   ```
   /interface l2tp-client add name=l2tp-to-rb4011 connect-to=36.88.39.234 \
       user=rb951 password=Rb951Tunnel2026 use-ipsec=yes ipsec-secret=balmon12345 \
       add-default-route=no disabled=no
   ```
   Status: connected, encoding cbc(aes)+hmac(sha1), local 192.168.6.164 → remote 192.168.6.80.
   Ping ke .80 sukses 3/3 @45ms. Internet tetap via WiFi (add-default-route=no).

### 4.2 RB5009UG+S+ (TCI UPT PONTIANAK, 36.88.39.234)
- Cek L2TP server: enabled, use-ipsec=yes secret balmon12345, MTU/MRU 1450,
  default-profile default-encryption.
- **User PPP baru dibuat** (permintaan user, tidak memakai `pontianak`):
  ```
  /ppp secret add name=rb951 password=Rb951Tunnel2026 service=l2tp \
      profile=default local-address=192.168.6.80 remote-address=192.168.6.164
  ```
- Sesi terverifikasi di `/ppp active` (rb951 → 192.168.6.164).
- Catatan topologi: hub-spoke, tiap spoke hanya punya rute /32 sendiri;
  spoke-to-spoke belum tembus (by design). NAT hub sudah memakai pola
  masquerade dst-address per LAN remote (162.0/24, 163.0/24, 161.0/24, 6.220).

### 4.3 Diskusi (belum dieksekusi)
Opsi menghubungkan RB951 ke seluruh jaringan antar-site:
- **Opsi A (rekomendasi)**: 3 rute statis di RB951 saja
  (192.168.6.0/24, 192.168.162.0/24, 192.168.163.0/24 via l2tp-to-rb4011);
  manfaat masquerade hub yang sudah ada; router remote tak disentuh.
- **Opsi B**: full routing tanpa NAT di semua spoke (perlu akses tiap router).

---

## 5. Backup yang Dihasilkan (`backups/`)
| File | Tujuan |
|------|--------|
| mikrotik-rb951-before-dhcp-wlan1-20260822-131208.rsc | sebelum ubah DHCP wlan1 |
| mikrotik-rb4011-before-add-ppp-secret-20260822-132620.rsc | sebelum tambah secret rb951 (hub) |
| mikrotik-rb951-before-add-l2tp-client-20260822-132844.rsc | sebelum tambah l2tp-client |

(Nama file memakai id lama karena dibuat sebelum rename.)

## 6. Kredensial Tunnel (referensi)
- Hub L2TP/IPsec: 36.88.39.234 — ipsec-secret `balmon12345`
- User tunnel RB951: `rb951` / `Rb951Tunnel2026` (service=l2tp only)
- IP tunnel RB951: 192.168.6.164/32

## 7. To-do Berikutnya
1. [ ] Eksekusi Opsi A (rute statis RB951) setelah approval.
2. [ ] Implement persist plan/validate/rollback di `/config/*` (masih stub).
3. [ ] Connection pooling/reuse SSH di driver (saat ini 1 koneksi per command).
4. [ ] Parser output RouterOS → JSON terstruktur (saat ini masih `{"raw": ...}`).

---
---

# Sesi Lanjutan — 2026-08-22 (sore): Onboarding MikroTik CHR Virtual

Operator: user (mohfa) + opencode agent
Target: MikroTik virtual 172.22.37.62 (admin/admin)

## 8. Onboarding & Identifikasi
- Device baru masuk inventory sementara sebagai `mikrotik-virtual-chr`
  (hostname awal `MikroTik-VM`), kredensial prefix `MIKROTIK_VIRTUAL_CHR_*`.
- Identify via SSH: identity default `MikroTik`, board **CHR QEMU**
  (`QEMU Ubuntu 26.04 PC i440FX`, x86_64, 1 vCPU @2400MHz),
  RouterOS **7.22.1** (stable), RAM 384 MiB, disk 89.2 MiB.
- Backend di-start ulang (uvicorn port 8000) karena sebelumnya mati.

## 9. Perubahan: Set Identity + Rename ID Inventory
Alur safety: backup → apply → verify (endpoint `/config/*` dan `policy_check`
masih stub 404, jadi plan/policy dilewati; approval eksplisit dari operator).

a) **Backup** sebelum change: dibuat manual via `POST /mikrotik/{id}/commands/run`
   dengan `/export terse` → disimpan ke:
   `backups/mikrotik-virtual-chr-before-set-identity-20260822-*.rsc`

b) **Set hostname**: `POST /api/v1/mikrotik/{device_id}/system/identity` name=`MK-1`
   → status applied; verify identify: `name: MK-1`.

c) **Rename ID** sesuai konvensi `mikrotik-<board>-<identity>`:

| | Lama | Baru |
|---|------|------|
| ID | mikrotik-virtual-chr | `mikrotik-chr-mk-1` |
| Hostname | MikroTik-VM | `MK-1` |

   Ikut diubah: `inventory/devices.json` (id + hostname), prefix kredensial
   `backend/.env` → `MIKROTIK_CHR_MK_1_USERNAME/PASSWORD` (admin/admin).
   Backend di-restart agar prefix .env baru ter-load, verify identify
   dengan ID baru: OK.

## 10. Temuan Infrastruktur (dikonfirmasi ulang)
- `/config/backup`, `/config/plan`, `policy_check` → masih stub / 404
  (konsisten dengan to-do #2 di atas). Backup manual via `commands/run`.
- Kredensial driver MikroTik resolve dari `{DEVICE_ID_UPPER}_USERNAME/PASSWORD`
  di `backend/.env`; perlu restart backend setelah rename prefix.

## 11. To-do Baru
1. [x] Onboarding CHR virtual + rename → selesai (item ini).
2. [ ] Survey kondisi MK-1: interface/route/firewall/config.

---
---

# Sesi Lanjutan — 2026-08-23: Cisco IOSv Onboarding, Driver Refactor & Config Transaction

Operator: user (mohfa) + opencode agent
Target: Cisco IOSv virtual 172.22.45.249 (admin/Admin123!)

## 12. Onboarding & Identifikasi Cisco
- Device ditambahkan ke inventory sebagai `cisco-iosv-r1` (hostname `R1`).
- Identify via SSH: Cisco IOSv 15.6(2)T, 4× GigabitEthernet, RAM ~512 MiB.
- Legacy SSH algorithms required: `diffie-hellman-group14-sha1`, `ssh-rsa`, `hmac-sha1`.
- Driver Cisco diperbarui: kredensial per-device (`CISCO_IOSV_R1_*`), `connect_options` untuk algoritma legacy.

## 13. Refactor Arsitektur SSH & Driver
- **SSHTransport** (vendor-neutral): `connect_options`, async context manager `interactive()`, deadline, `drain_until` → `PromptTimeoutError`.
- **Exception hierarchy**: `SSHTransportError` → `SSHConnectError`, `SSHTimeoutError`, `PromptTimeoutError`; `CiscoCLIError`.
- **FastAPI exception handlers** memetakan ke HTTP 502/504/503/422.
- **Cisco CLI layer** (`drivers/cisco/cli.py`): prompt regex, output cleaner, `%` error parsing, batch `run_batch`, config session `run_config_lines`, interactive confirm-loop.
- Semua logika vendor dipindahkan keluar transport.

## 14. Config Transaction (Backup → Apply → Verify → Commit/Rollback)
- Endpoint baru: `POST /api/v1/cisco/{id}/config/transaction`.
- Flow: copy running-config ke `flash0:pre-txn.cfg` → `conf t` apply commands → verify via `run_batch` (expect substring) → jika gagal `configure replace flash0:pre-txn.cfg force` (Rollback Done) → hapus file flash.
- Tes live:
  - **Commit sukses**: ACL `ARCH-COMMIT` dibuat, verify pass, commit.
  - **Rollback otomatis**: ACL `ARCH-ROLLBACK` apply OK, verify mismatch → rollback → ACL hilang.

## 15. Endpoint Test Results (Live)
Devices: `cisco-iosv-r1`, `mikrotik-chr-mk-1`.

| Vendor | GET resources | POST safe | Notes |
|--------|---------------|-----------|-------|
| **Cisco** | 10/10 OK (version, interfaces, routes, arp, cpu-mem, acls, cdp, nat, logs) | 5/5 OK (commands/run, ping, traceroute, config/backup, config/save) | Clean output (no banner), batch + transaction functional |
| **MikroTik** | 28/34 OK (core resources OK) | 2/4 OK (commands/run, monitoring) | 6 GET 422 (features absent on CHR: wireless, snmp, pppoe-server, tunnel servers); 2 POST 404 (/tools/ping, /config/backup not implemented) |

No primary IP/SSH configs altered on either device.

## 16. To-do Berikutnya (Global)
1. [ ] Implement `/config/plan|validate|apply|rollback` for MikroTik (parity with Cisco transaction).
2. [ ] Add missing MikroTik POST endpoints (`/tools/ping`, `/config/backup`).
3. [ ] Connection pooling / session reuse for high throughput.
4. [ ] Structured parsers (JSON) instead of raw text for both vendors.
5. [ ] Device profile YAML (move `connect_options` out of code).

