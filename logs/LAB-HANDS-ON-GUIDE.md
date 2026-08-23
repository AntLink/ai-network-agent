# Panduan Hands-On Lab GNS3 — Pahami & Uji Sendiri

Untuk operator yang ingin memahami dan menguji lab secara mandiri.
Pasangan dengan: `LAB-GNS3-REFERENCE.md` (referensi cepat) dan
`SESSION-2026-08-23-gns3-lab-recovery.md` (kisah perbaikannya).

---

# BAGIAN 1 — ANALOGI TOPOLOGI

Bayangkan sebuah **perusahaan dengan 2 kantor cabang** yang saling
terhubung lewat **penyedia jaringan (ISP)**:

```
   KANTOR A                          KANTOR B
┌─────────────────┐              ┌─────────────────┐
│ PC-A1 (Staf)    │              │ PC-B1 (Staf)    │
│ PC-A2 (Server?) │              │ PC-B2 (Server?) │
│     │           │              │     │           │
│   [SW1] panel   │              │   [SW2] panel   │
│     LAN gedung  │              │     LAN gedung  │
│     │trunk      │              │     │trunk      │
│   [R1] gerbang  │═══jalan═══╗ ╔═│   [R2] gerbang  │
└─────────────────┘  tikus    ║ ║ └─────────────────┘
                        (R1-R2 langsung)
                       ║               ║
                  ┌────▼───────────────▼────┐
                  │      ISP = MK-1 CHR     │
                  │  (juga punya LAN sendiri│
                  │   berisi PC-M "server   │
                  │        pusat")          │
                  └─────────────────────────┘
```

| Objek di lab | Analogi dunia nyata |
|---|---|
| **PC-A1 dst (VPCS)** | Komputer karyawan. Sengaja pakai VPCS (simulator PC super ringan) supaya fokus ke jaringan, bukan OS |
| **SW1/SW2 (switch)** | Panel distribusi LAN di gedung: mencolok banyak kabel, lalu lintas data diarahkan hanya ke tujuan (berdasar MAC address) |
| **VLAN 10 & 20** | Pemisahan departemen di kabel fisik yang sama — seperti satu gedung punya "lantai virtual": lantai 10 khusus staf, lantai 20 khusus server. Mereka TIDAK bisa bicara walau satu kabel |
| **Trunk Gi0/0** | Satu koridor utama dari panel ke gerbang yang bisa dilewati kedua "lantai" sekaligus — setiap frame diberi label/tag (dot1Q 10 atau 20) agar tidak tertukar |
| **R1/R2 (router-on-a-stick)** | Gerbang keluar gedung. Satu kabel fisik (Gi0/1) tapi dibagi jadi 2 pintu logis (subinterface .10 dan .20), masing-masing jadi "gerbang default" bagi VLAN-nya |
| **Link 10.255.x.x /30** | Jalan tol antar gedung/ISP — alamatnya hemat (/30 = cuma cukup untuk 2 ujung) |
| **R1↔R2 langsung (10.255.12.0/30)** | Jalan tikus antar dua gedung. Awalnya direncanakan cadangan, tapi karena lebih dekat (OSPF cost lebih kecil), dia malah jadi **jalur utama antar cabang** |
| **MK-1 (MikroTik CHR)** | ISP/penyedia transit. Menghubungkan kedua gedung DAN punya LAN sendiri (192.168.100.0/24) berisi PC-M — anggap server pusat/data center |
| **OSPF** | Para router bertukar peta secara otomatis seperti komunitas GPS: jika ada jalan macet, peta diperbarui otomatis dan rute diubah |
| **Cloud node (Gi0/0 router)** | Pintu darurat keluar dari simulasi menuju dunia nyata (jaringan Hyper-V host) — dipakai untuk akses manajemen (SSH) dari laptop kita. Ini istilahnya **OOB management** |

**Alur cerita lengkap saat PC-A1 kirim file ke PC-B1:**
PC-A1 → (lihat tujuan beda network) kirim ke gerbang 192.168.10.1 → SW1
menandai frame VLAN 10 di trunk → R1 membuka tag, cek peta OSPF:
"ke 192.168.30.0 lewat jalan tikus 10.255.12.0" → kirim ke R2 → R2 lewat
trunk VLAN 10 → SW2 → PC-B1. Balasan jalan sebaliknya. Semuanya < 15 ms.

---

# BAGIAN 2 — DAFTAR LENGKAP (IP, VLAN, ROUTING)

## 2.1 Subnet & Peran

| Subnet | Nama | Dipakai siapa |
|---|---|---|
| 192.168.10.0/24 | USERS-A | PC-A1 + gateway R1 |
| 192.168.20.0/24 | SERVERS-A | PC-A2 + gateway R1 |
| 192.168.30.0/24 | USERS-B | PC-B1 + gateway R2 |
| 192.168.40.0/24 | SERVERS-B | PC-B2 + gateway R2 |
| 192.168.100.0/24 | LAN-M | PC-M + gateway MK-1 |
| 10.255.10.0/30 | WAN R1↔MK | R1(.2) ↔ MK ether2(.1) |
| 10.255.20.0/30 | WAN R2↔MK | R2(.2) ↔ MK ether3(.1) |
| 10.255.12.0/30 | JALAN TIKUS R1↔R2 | R1(.1) ↔ R2(.2) |
| 172.22.32.0/20 | Dunia nyata (mgmt) | Cloud node + GNS3 VM (.68) |

## 2.2 Interface Kunci per Device

**R1** — `telnet 172.22.37.68 5006`
```
Gi0/0      172.22.45.249/20  mgmt OOB (ke Cloud2)
Gi0/1      trunk (tanpa IP)
Gi0/1.10   192.168.10.1/24   encapsulation dot1Q 10
Gi0/1.20   192.168.20.1/24   encapsulation dot1Q 20
Gi0/2      10.255.10.2/30    ke MK
Gi0/3      10.255.12.1/30    jalan tikus ke R2
```

**R2** — `telnet 172.22.37.68 5008`
```
Gi0/0      172.22.36.184/20  mgmt OOB
Gi0/1      trunk
Gi0/1.10   192.168.30.1/24   (VLAN 10 situs B!)
Gi0/1.20   192.168.40.1/24   (VLAN 20 situs B!)
Gi0/2      10.255.20.2/30    ke MK
Gi0/3      10.255.12.2/30    jalan tikus ke R1
```
Perhatikan: VLAN 10 di kedua situs TETAP subnet BERBEDA
(10 vs 30). Nomor VLAN lokal saja yang sama.

**SW1** — `telnet 172.22.37.68 5002`
```
Gi0/0 trunk (dot1q, semua VLAN) → R1
Gi0/1 access VLAN 10 → PC-A1        SVI Vlan10 = 192.168.10.2
Gi0/2 access VLAN 20 → PC-A2        (untuk manajemen switch)
Gi0/3 access VLAN 1  → Cloud4       (sisa jalur mgmt lama)
```

**SW2** — `telnet 172.22.37.68 5004` — pola sama: Gi0/1→VLAN10(PC-B1),
Gi0/2→VLAN20(PC-B2), Gi0/0 trunk ke R2, SVI Vlan10=192.168.30.2.

**MK-1** — SSH `admin@172.22.37.168` (password: admin)
```
ether1 DHCP 172.22.37.168/20 (mgmt)
ether2 10.255.10.1/30  OSPF area bk2
ether3 10.255.20.1/30  OSPF area bk2
ether4 192.168.100.1/24 (LAN-M)
```

## 2.3 Router-ID OSPF & Kredensial

| Device | Router-ID | User/Pass |
|--------|-----------|-----------|
| R1 | 1.1.1.1 | admin / Admin123! (enable sama) |
| R2 | 2.2.2.2 | idem |
| MK-1 | 3.3.3.3 | admin / admin |

## 2.4 Jalur Aktual (hasil traceroute nyata!)

```
PC-A1 → PC-B1 : 192.168.10.1 (R1) → 10.255.12.2 (R2) → tujuan
                [via JALAN TIKUS, bukan ISP! cost OSPF 2 < 3]
PC-A1 → PC-M  : 192.168.10.1 (R1) → 10.255.10.1 (MK) → tujuan
PC-B2 → PC-A2 : 192.168.40.1 (R2) → 10.255.12.1 (R1) → tujuan
```
Kenapa jalur tikus menang? OSPF menghitung biaya total:
- Lewat jalan tikus: R1 keluar Gi0/3 (cost 1) + R2 keluar Gi0/1.10 (1) = **2**
- Lewat ISP MK: Gi0/2 (1) + ether3 (1) + Gi0/1.10 (1) = 3
Angka `[110/2]` di `show ip route` artinya: protokol OSPF (AD 110),
metric 2.

---

# BAGIAN 3 — TAHAPAN PENGUJIAN MANUAL

Cara konek: dari Windows `telnet 172.22.37.68 <port>` (aktifkan fitur
Telnet Client dulu), atau klik konsol node di GUI GNS3.
Password IOS: `Admin123!`. Untuk masuk mode config: `enable` → `conf t`.

### TAHAP 0 — Cek Kesehatan Dasar (semua device)
```
R1/SW1: show ip interface brief     ← semua interface penting up/up
SW1    : show ip interface brief | include Vlan
```
✅ Lulus bila: Gi0/1.10/.20 (router) up/up; Vlan10 SVI up.

### TAHAP 1 — Uji Akses Lokal (PC → Gerbangnya)
Di konsol PC (`telnet ... 5010` untuk A1):
```
show ip                 ← pastikan ip/gateway benar
ping 192.168.10.1       ← harus 100% sukses
arp                     ← MAC gerbang tercatat
```
✅ Lulus bila ping 5/5. ❌ Gagal = masalah akses VLAN/switch (Tahap 2).

### TAHAP 2 — Uji Switching & VLAN (SW1)
```
show vlan brief                    ← Gi0/1 di baris VLAN 10, Gi0/2 di VLAN 20
show interfaces status             ← status connected, vlan benar
show mac address-table dynamic     ← PC di port Gi0/1 VLAN 10
show interfaces trunk              ← Gi0/0 trunking VLAN 10,20
```
🔍 Eksperimen: lihat kolom Ports di `show vlan brief` berubah saat
Anda colok/pindahkan PC (di GNS3).

### TAHAP 3 — Uji Trunk & Router-on-a-Stick (R1)
```
show interfaces GigabitEthernet0/1        ← up, tanpa IP (memang begitu)
show interfaces GigabitEthernet0/1.10     ← 192.168.10.1, up
show vlan dot1q tag native                ← info tagging
```
Buktikan tagging bekerja: dari PC-A1 `ping 192.168.10.1` sambil di R1
jalankan `debug arp` (jangan lupa `undebug all` setelahnya!).

### TAHAP 4 — Uji WAN & Jalan Tikus (antara router)
Di R1:
```
ping 10.255.10.1      ← ke MK (harus sukses)
ping 10.255.12.2      ← ke R2 via jalur tikus (harus sukses)
ping 10.255.20.2      ← ke interface WAN R2 yang jauh (sukses via rute)
```

### TAHAP 5 — Uji OSPF (inti lab!)
Di R1:
```
show ip ospf neighbor
```
✅ Harus 2 neighbor FULL:
```
2.2.2.2   FULL/DR   ... 10.255.12.2   Gi0/3   ← R2
3.3.3.3   FULL/DR   ... 10.255.10.1   Gi0/2   ← MK
```
```
show ip route ospf        ← semua LAN tetangga muncul dgn huruf O
show ip protocols         ← ringkasan konfigurasi OSPF
```
Di MK-1 (SSH): `/routing ospf neighbor print` → 2 entri `"Full"`.

🔍 Analogi debugging: neighbor STUCK di EXSTART/EXCHANGE = masalah MTU;
tidak ada neighbor sama sekali = masalah L2/hello (cek `network`
statement, encapsulation, kabel).

### TAHAP 6 — Uji End-to-End + Lihat Jalurnya
Dari PC-A1:
```
ping 192.168.30.10     ← PC-B1 lintas situs
trace 192.168.30.10    ← LIHAT: lewat 10.255.12.2 (jalan tikus)!
ping 192.168.100.10    ← PC-M di LAN ISP
trace 192.168.100.10   ← lewat 10.255.10.1 (MK)
```

### TAHAP 7 — Uji Persistensi (pelajaran hari ini!)
Di R1: `write memory` → `reload` → tunggu boot →
```
show running-config | include hostname|router ospf
show ip ospf neighbor
```
✅ Config masih utuh & OSPF re-form otomatis = persistensi SEHAT.
(Sekali waktu ini gagal senyap — lihat log sesi 23 Aug.)

### TAHAP 8 — Eksperimen Kegagalan (opsional, aman!)
1. Di R1: `interface g0/3` → `shutdown` (putus jalur tikus)
2. Dari PC-A1: `trace 192.168.30.10` → kini lewat 10.255.10.1 (MK)!
3. OSPF konvergen dalam ±beberapa detik — inilah "GPS komunitas".
4. Jangan lupa: `no shutdown` balikkan.
5. Coba juga: shutdown subinterface `.20`, lalu rasakan PC-A2 hilang
   tapi PC-A1 tetap normal (bukti isolasi VLAN bekerja).

---

# BAGIAN 4 — LATIHAN MANDIRI (naikkan level)

1. **VLAN baru**: buat VLAN 30 "GUEST-A" di SW1+subinterface Gi0/1.30
   di R1 (IP 192.168.50.1/24), advertise di OSPF, tes dari VPCS baru.
2. **Manipulasi cost**: di R1 Gi0/3 set `ip ospf cost 100` → traceroute
   PC-A1→PC-B1 kini harus memutar lewat MK! Kembalikan setelahnya.
3. **DHCP**: ganti IP statis PC-A1 menjadi DHCP dari R1
   (`ip dhcp pool`, exclude gateway).
4. **Keamanan**: batasi SSH R1 hanya dari 172.22.32.0/20 (ACL + line vty).
5. **Backup otomatis**: ekspor config R1 berkala ke TFTP/GNS3 VM.

---

## Kartu Contekan Cepat

| Ingin tahu | Perintah | Device |
|---|---|---|
| Siapa saya | `show version` / hostname prompt | IOS |
| IP semua interface | `show ip int brief` | IOS |
| Siapa tetangga OSPF | `show ip ospf neighbor` | IOS |
| Peta rute belajar OSPF | `show ip route ospf` | IOS |
| Isi "panel lantai" | `show vlan brief` | SW |
| Koridor trunk | `show interfaces trunk` | SW |
| Alamat MAC tercatat | `show mac address-table dyn` | SW |
| Tetangga OSPF (MK) | `/routing ospf neighbor print` | MK |
| Rute (MK) | `/ip route print where ospf` | MK |
| Jalur paket | `trace <ip>` | VPCS |
