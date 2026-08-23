# Lab GNS3 "ai-netagent" — Referensi Cepat

Terakhir diperbarui: 2026-08-23. Status: **Fase 1+2 selesai, 8/8 tes lulus.**

## 1. Topologi & Rencana IP

```
Situs A                          Situs B
PC-A1 192.168.10.10 ─ Gi0/1      PC-B1 192.168.30.10 ─ Gi0/1
PC-A2 192.168.20.10 ─ Gi0/2      PC-B2 192.168.40.10 ─ Gi0/2
              │ SW1                      │ SW2
        Gi0/0 trunk dot1q          Gi0/0 trunk dot1q
              │                          │
        R1  Gi0/1 (.1 kedua VLAN)  R2  Gi0/1 (.1 kedua VLAN)
   Gi0/2 10.255.10.2/30       Gi0/2 10.255.20.2/30
   Gi0/3 10.255.12.1/30 ────── Gi0/3 10.255.12.2/30 (backup)
              │                          │
              └────── MK-1 CHR ──────────┘
                ether2 10.255.10.1/30 (OSPF ke R1)
                ether3 10.255.20.1/30 (OSPF ke R2)
                ether4 192.168.100.1/24 ─ PC-M 192.168.100.10
                ether1 → Cloud1 (mgmt 172.22.37.168/20 via DHCP)
R1 mgmt: 172.22.45.249/20 (Gi0/0→Cloud2) | R2: 172.22.36.184/20 (Cloud3)
SW1 SVI Vlan10 = 192.168.10.2 (gw .1)    | SW2 SVI Vlan10 = 192.168.30.2
```

- OSPF process 1, area 0, router-id: R1=1.1.1.1, R2=2.2.2.2, MK=3.3.3.3.
- Passive-interface pada semua subinterface LAN.
- MK: instance `lab`, area `bk2`, interface-template per network.

## 2. Peta Port Konsol (telnet 172.22.37.68)

| Port | Node | | Port | Node |
|------|------|-|------|------|
| 5002 | SW1 | | 5012 | PC-A2 |
| 5004 | SW2 | | 5014 | PC-B1 |
| 5006 | R1  | | 5016 | PC-B2 |
| 5008 | R2  | | 5018 | PC-M |
| 5010 | PC-A1 | | | |

Catatan: ini port proxy gns3server; port serial qemu aktual = port−1.

## 3. Kredensial

| Target | User/Pass | Catatan |
|--------|-----------|---------|
| R1/R2/SW1/SW2 | admin / Admin123! | priv15, enable secret sama |
| MK-1 SSH | admin / admin | 172.22.37.168 |
| GNS3 VM SSH | gns3 / gns3 | sudo tersedia |
| Controller API | Basic `admin:<pw>` | pw di `%APPDATA%\GNS3\2.2\gns3_server.ini` |

SSH ke IOS lab hanya jalan dengan algoritma legacy:
`KexAlgorithms=+diffie-hellman-group14-sha1 HostKeyAlgorithms=+ssh-rsa MACs=+hmac-sha1`.

## 4. Aturan Emulasi yang WAJIB (pelajaran berdarah)

1. **Semua node Cisco (vIOS/vIOS-L2 dari image VMDK asli) wajib
   `hda_disk_interface: ide`.** Kernel vmdk.SSA/vmdk.SPA tidak punya driver
   AHCI. Gejala SATA: `flash0:/ No such device`, vlan.dat gagal ditulis,
   `write memory [OK]` palsu, config hilang saat reload.
2. Template default sudah diubah ke ide (2026-08-23) — jangan dikembalikan.
3. Setelah menulis konfigurasi: WAJIB bukti persisten
   `show startup-config | include <pola-kunci>` (hostname + trunk + access vlan + ospf).
4. Link tampak "connected" tapi counter input = 0 → socket ubridge rusak;
   perbaiki dengan stop/start node ujung-ujung link via controller API.
5. Otomasi konsol harus prompt-synced; jangan kirim ENTER saat prompt
   berakhir `:` (dianggap jawaban kosong).

## 5. Perintah Berguna

```powershell
# Daftar link aktual (peta kabel)
python backend/list_links.py

# Suite tes end-to-end (8 tes)
python backend/grand_finale_ping.py

# Rebuild socket link setelah proses qemu dibunuh/di-restart
python backend/rebuild_sockets.py
```

```bash
# Di dalam GNS3 VM: cek disk interface node berjalan
ps aux | grep qemu | grep ' -name SW1 ' | grep -oE 'if=[a-z]+'

# Boot log sehat: ukuran CompactFlash TIDAK boleh "0K"
#   262144K bytes of ATA System CompactFlash 0  ← OK
#   0K bytes of ATA System CompactFlash 0       ← FLASH RUSAK (sata!)
```

## 6. ID Node (project a6967457-f60e-4752-be8f-6b66e925245c)

| Node | UUID | hda_disk.qcow2 (overlay → base VMDK) |
|------|------|--------------------------------------|
| SW1  | 18bd9697-da5c-41f2-8dd5-483315a7c99d | vios_l2-adventerprisek9-m.vmdk.SSA.152-4.0.55.E |
| SW2  | 12adbd8f-7400-4d36-816c-c2b1f0e428b3 | vios_l2-adventerprisek9-m.vmdk.SSA.152-4.0.55.E |
| R1   | e49bc1fc-27ad-4a70-859b-707d60a63501 | vios-adventerprisek9-m.vmdk.SPA.156-2.T |
| R2   | fb9b15d4-f82c-4082-be9e-9a5117d7abe7 | vios-adventerprisek9-m.vmdk.SPA.156-2.T |
| MK1  | 3601a488-07e9-4ce8-80b6-0fa17238970d | chr-7.22.1.img (virtio, aman) |

Overlay qcow2 ±1 MB normal (COW di atas base). Base images:
`/opt/gns3/images/QEMU/`.
