# Session Log — 2026-08-22 (sore): Onboarding Cisco IOSv R1

Operator: user (mohfa) + opencode agent
Target: Cisco IOSv virtual 172.22.45.249

---

## 1. Diagnosis Login SSH Gagal
- Gejala: user tidak bisa `ssh admin@172.22.45.249` tanpa opsi tambahan.
- Konektivitas: ping OK (TTL 255), port 22 terbuka → masalah di layer SSH.
- Penyebab: IOS 15.6(2)T hanya menawarkan algoritma legacy:
  - KEX `diffie-hellman-group14-sha1`
  - Host key `ssh-rsa` (SHA-1)
  - MAC `hmac-sha1`
  OpenSSH modern menonaktifkan algoritma tersebut secara default.
  Workaround user (berhasil):
  ```
  ssh -oKexAlgorithms=+diffie-hellman-group14-sha1 \
      -oHostKeyAlgorithms=+ssh-rsa -oMACs=+hmac-sha1 admin@172.22.45.249
  ```
- Driver backend memakai `asyncssh` yang masih mengaktifkan algoritma legacy,
  jadi konek tanpa flag tambahan. Tes via script `tmp/diag_ssh_cisco.py`
  (banner `SSH-2.0-Cisco-1.25`, login admin OK).

## 2. Fix Driver Cisco (kredensial per-device)
| File | Perubahan |
|------|-----------|
| `backend/app/drivers/cisco/driver.py` | `_transport()` tidak lagi pakai kredensial global `NETWORK_*`; sekarang pola `{PREFIX}_USERNAME/PASSWORD` dari `backend/.env` (konsisten dgn driver MikroTik/Linux) |

## 3. Onboarding & Rename ID
- Masuk inventory sementara sebagai `cisco-iosv-lab`.
- Identify: **R1**, Cisco IOSv `VIOS-ADVENTERPRISEK9-M` 15.6(2)T,
  4x GigabitEthernet, Processor Board ID 9G581LH6Z8NQM27WH0H5D.
- Rename sesuai konvensi `<vendor>-<model>-<hostname>`:

| | Lama | Baru |
|---|------|------|
| ID | cisco-iosv-lab | `cisco-iosv-r1` |
| Hostname | cisco-iosv | `R1` |

- Ikut diubah: `inventory/devices.json` (id + hostname), prefix kredensial
  `backend/.env` → `CISCO_IOSV_R1_USERNAME=admin` / `CISCO_IOSV_R1_PASSWORD`.
- Backend restart + verify identify dengan ID baru: OK.

## 4. Insiden Kecil (diperbaiki)
- Saat menghapus quote pada nilai password di `backend/.env`, regex salah
  sehingga prefix key hilang (`Admin123!` tanpa key). Terdeteksi saat verifikasi
  panjang nilai env; langsung dikoreksi manual. Pelajaran: selalu verify isi
  `.env` setelah edit programatik.

## 5. To-do Berikutnya
1. [ ] Survey R1: interface/route/running-config.
2. [ ] Pertimbangkan upgrade algoritma SSH di IOS (ip ssh server algorithm)
       agar kompatibel klien modern, atau dokumentasikan flag workaround.
