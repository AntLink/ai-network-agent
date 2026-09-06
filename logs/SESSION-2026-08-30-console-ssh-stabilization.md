# Session 2026-08-30 - Console & SSH Stabilization + Approval Flow

## Tujuan

Menstabilkan jalur eksekusi perangkat (console telnet GNS3 & SSH), memastikan
respond tidak terpotong oleh pager (`--More--` / `<--- More --->`), menambahkan
alur persetujuan (approval) yang eksplisit & teraudit, serta menyiapkan SSH
sebagai transport utama di device lab.

## Masalah yang ditemukan & diperbaiki

1. **Console telnet GNS3 tidak punya serialisasi per port.**
   Dua sesi paralel ke port yang sama menabrakkan karakter → console rusak
   ("login dialog did not reach a CLI prompt"), command tertelan, output kacau.

2. **Output panjang memicu pager** di console:
   - Cisco IOSv: `<--- More --->` + artefak indentasi 8-9 spasi.
   - ASAv: `---- More ----`; raw `show running-config` sempat terpotong di
     `pager lines 23`.
   - MikroTik: pager `-- More --` / `-- [Q quit|D dump|down]`.

3. **Login/dialog console rapuh:**
   - RouterOS 7 merender ulang "MikroTik Login:" berkali-kali saat menjawab
     query telnet → username/password terkirim berulang → auth gagal.
   - Console yang tertinggal di **config-mode** → semua perintah baru `% Invalid
     input` (ditemukan di Cisco-Router).
   - `enable` tanpa password: ASAv menolak empty → loop tak terbatas sampai
     timeout.
   - MikroTik CHR: password admin ter-set (`admin123`) & wizard first-boot
     meminta password baru → butuh fallback kredensial.

4. **Alur write di agent tool menyasar jalur yang salah:**
   - `CiscoDriver.apply()` memakai EXEC batch (`run_batch`) → perintah config
     (`interface ...`) gagal `% Invalid input` di jalur SSH.
   - `AsaDriver` tidak punya `exec_logged` → `show` read di-route ke config-mode.
   - `.env` tidak di-inject ke `os.environ` → kredensial per-device tidak
     terbaca → SSH auth gagal + fallback konsol.

5. **Approval loop putus:** command berisiko mengembalikan `approval_id` tapi
   tidak ada cara meninjau antrean / menyetujui secara eksplisit.

6. **Tabrakan port console di inventory:** `pc-vm-1` & `pc-attacker` (Linux)
   menunjuk `console 5007` = console **Cisco-Switch** → driver Linux mengirim
   `cat /etc/os-release` / `apt --version` ke console switch. `fw-asav` menunjuk
   `5001` = console **Cisco-Router**.

## Perubahan kode

### `backend/app/transports/console.py`
- **Lock per port** (`_console_lock`, keyed loop+host+port) di `open()`/`close()` —
  sesi console serial, cegah tabrakan karakter.
- `clean_command_output()` diperkuat: hapus `<--- More --->`,
  `---- More ----`, `-- More --` di mana pun + hilangkan artefak indentasi
  8+ spasi dari redraw pager IOSv.
- `run()`/`run_scripted()`: jalankan `pager_off_command` sebelum command
  (`terminal length 0` / `terminal pager 0`).
- Login input robust:
  - kandidat password: configured → bootstrap → Enter-kosong → admin123,
    anti-loop max 3×;
  - abaikan redraw "MikroTik Login:" saat username sudah dikirim
    (`_password_sent`);
  - `enable` dicoba sekali; ditolak → fallback user-mode;
  - console yang mewarisi config-mode → Ctrl-Z (`\x1a`) ke EXEC;
  - `run_scripted(...)` baru: command + daftar `{"pattern","send"}` untuk
    prompt interaktif (keygen, copy, dsb).

### `backend/app/drivers/cisco/driver.py`
- `_console_transport()`: `pager_off_command="terminal length 0"`.
- `apply()` → `_configure()` (jalur `configure terminal`) — sebelumnya EXEC
  batch sehingga command config gagal di SSH.

### `backend/app/drivers/cisco/asa.py` (file baru di git)
- `_console_transport()` alias, `exec_logged()`, `pager_off_command=
  "terminal pager 0"`, `_logged()` audit; step manual `enable` redundan dihapus.

### `backend/app/api/v1/endpoints/gns3.py`
- `_infer_pager_off(node)`: deteksi image `asav`→`terminal pager 0`,
  `vios/iosv/c7200`→`terminal length 0` untuk console-exec otomatis.
- Endpoint baru `POST .../console-interactive` (scripted prompts).
- Pydantic `Field` import.

### `backend/app/agent/tools.py`
- `list_pending_approvals()` & `approve_command(approval_id, approved_by)`.

### `backend/app/api/v1/endpoints/agent.py`
- `GET /tools/pending-approvals`, `POST /tools/approve`.

### `backend/app/core/config.py`
- `load_dotenv(.env)` — inject env ke `os.environ` untuk kredensial driver.

### `mcp-bridge`
- Tool baru: `net_console_interactive`, `net_list_pending_approvals`,
  `net_approve_command` (+ registrasi `server.py`).

### `inventory/devices.json`
- Management address real: cisco-router 172.22.138.112, cisco-switch
  172.22.134.49, asa-fw 172.22.134.50, mikrotik-chr 172.22.143.61
  (transport ssh, port 22).
- `pc-vm-1`/`pc-attacker`: mapping console 5007 (collision switch) dihapus →
  transport ssh.
- `fw-asav`: console 5001 (collision router) → 5004 (ASAv asli).

## Lab: SSH & DHCP di device GNS3 "Lab-Cloud-VM-Devices"

- DHCP client aktif: Cisco-Router Gi0/0=172.22.138.112 (dhcp), MikroTik-CHR
  ether1=172.22.143.61/20 (bound), ASA Management0/0=172.22.134.50/20 (dhcp,
  nameif management). Cisco-Switch (image vios_l2 tak dukung DHCP client SVI)
  pakai IP statis Vlan1 172.22.134.49/20 → ping gateway 172.22.128.1 OK.
- SSH enabled + key RSA: Router (hostname R1), Switch, ASAv; user
  admin/admin123 (vty login local / aaa LOCAL). MikroTik sudah ROSSH by default.
- Eksplorasi via SSH transport teruji: facts, interfaces, routes,
  running-config (Cisco, MikroTik). Driver ASA konsol-based (ASAv tak dukung
  exec-request SSH).

## Verifikasi

- `pytest` console transport tests (telnet IAC, ANSI, pager, newpass) lestari.
- 8 endpoint read (config/router/switch/ASA/MikroTik, SSH & console) dicek:
  tidak ada literal `--More--` / `<--- More --->`, raw lengkap sampai penutup.
- Approval flow end-to-end: command → approval_required → list pending →
  approve(approved_by) → executed → antrean kosong.

## Catatan

- Tool baru di mcp-bridge aktif penuh setelah MCP server restart (sesi baru).
- Koneksi console pertama ke node idle GNS3 kadang perlu 1× retry (flake wajar,
  bukan regresi).
- `logs/config-plans.json`, `uvicorn_*.log` tidak ikut di-commit.