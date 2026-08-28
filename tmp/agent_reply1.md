# Menambahkan Static Route di MikroTik RouterOS

Berikut panduan operasional menambahkan static route di RouterOS, dilengkapi dengan kondisi live state masing-masing device yang Anda kelola.

---

## Ringkasan

| Device | IP Management | Static Route Count | Gateway Reachable | Status |
|---|---|---|---|---|
| TCI UPT PONTIANAK | 36.88.39.234 | *(perlu verifikasi)* | *(perlu verifikasi)* | Online |
| HOME-BAGEM | 192.168.30.1 | *(perlu verifikasi)* | *(perlu verifikasi)* | Online |
| MK-1 (CHR) | 172.22.37.168 | *(perlu verifikasi)* | *(perlu verifikasi)* | Online |
| SR-MT1 | 172.22.134.144 | *(perlu verifikasi)* | *(perlu verifikasi)* | Online |

---

## 1. TCI UPT PONTIANAK (mikrotik-rb5009-tci-upt-pontianak)

### Backend Snapshot (fact-based)
- **Hostname**: TCI UPT PONTIANAK
- **Board**: RB5009UG+S+
- **RouterOS**: v7.20.8 (long-term)
- **Uptime**: 4d15h54m58s
- **Management**: 36.88.39.234 (SSH aktif, banner `SSH-2.0-ROSSSH`)
- **Interfaces yang terdeteksi**: ether1–ether8, sfp-sfpplus1, bridge1, lo, `<l2tp-cc>`

### Temuan Routing (perlu diverifikasi live)
- State routing table (`/ip route`) tidak ada pada snapshot saat ini. Perlu eksekusi live command berikut:
  ```
  /ip route print detail
  /ip address print
  ```

### Analisis
Device ini online dan responsif via SSH. Interface `ether1` sudah up (link-downs=2) dan terhubung ke bridge1. Karena ini adalah RB5009 dengan banyak interface, static route biasanya dipakai untuk pointing subnet LAN ke gateway upstream pada interface tertentu.

### Rekomendasi: Sintaks menambahkan static route
```routeros
/ip route
add dst-address=192.168.99.0/24 gateway=192.168.1.1 distance=1 comment="Route-to-backbone-99"
```

**Parameter penting:**
- `dst-address` — network tujuan (CIDR)
- `gateway` — IP gateway langsung (harus berada di jaringan yang terhubung langsung ke salah satu interface)
- `distance` — nilai administratife (default=1, semakin rendah semakin disukai)
- `comment` — label untuk identifikasi
- `check-gateway` — `ping` atau `arp` (opsional, untuk failover)

**Failover aktif dengan routing mark:**
```routerotik
/ip route
add dst-address=0.0.0.0/0 gateway=192.168.1.1 distance=1 check-gateway=ping
add dst-address=0.0.0.0/0 gateway=192.168.1.2 distance=2 check-gateway=ping
```

### Langkah berikutnya (TCI UPT PONTIANAK)
1. Cek tabel rute saat ini: `/ip route print detail`
2. Cek alamat IP interface: `/ip address print`
3. Identifikasi gateway upstream yang valid (harus reachable langsung)
4. Tambahkan route: `/ip route add dst-address=<network> gateway=<gw> distance=1 comment="<deskripsi>"`
5. Verifikasi: `/ip route print detail where dst-address=<network>`

---

## 2. HOME-BAGEM (mikrotik-rb951ui-2hnd-home-bagem)

### Backend Snapshot
- **Hostname**: HOME-BAGEM
- **Management**: 192.168.30.1
- **Platform**: routeros

### Temuan Routing (perlu diverifikasi live)
State routing table dan alamat IP tidak tersedia pada snapshot saat ini. Perlu eksekusi:
```
/ip route print detail
/ip address print
```

### Analisis
Device HOME-BAGEM adalah RB951Ui-2HnD. Berdasarkan nama, ini adalah perangkat home/SMB dengan kemungkinan skenario routing sederhana.

### Rekomendasi: Sintaks menambahkan static route
```routeros
/ip route
add dst-address=10.0.0.0/8 gateway=192.168.30.254 distance=1 comment="Route-to-corporate"
```

### Langkah berikutnya (HOME-BAGEM)
1. Jalankan: `/ip address print` — lihat interface mana yang memiliki subnet 192.168.30.x
2. Pastikan gateway (misal 192.168.30.254) berada di jaringan yang sama
3. Tambahkan static route sesuai kebutuhan
4. Verifikasi dengan `/ip route print`

---

## 3. MK-1 (mikrotik-chr-mk-1)

### Backend Snapshot
- **Hostname**: MK-1
- **Platform**: routeros (CHR — Cloud Hosted Router)
- **Management**: 172.22.37.168

### Temuan Routing (perlu diverifikasi live)
State routing table dan alamat IP tidak tersedia pada snapshot. Perlu eksekusi:
```
/ip route print detail
/ip address print
```

### Analisis
CHR biasanya dipakai sebagai router virtual untuk lab/simulasi. Static route di sini sering dipakai untuk routing antar lab network.

### Rekomendasi: Sintaks menambahkan static route
```routeros
/ip route
add dst-address=172.16.0.0/16 gateway=172.22.37.1 distance=1 comment="Route-to-lab-core"
```

### Langkah berikutnya (MK-1)
1. Cek interface dan alamat IP: `/ip address print`
2. Identifikasi gateway yang valid untuk subnet 172.22.x.x
3. Tambahkan static route dengan `/ip route add`
4. Pastikan route tidak bentrok dengan route dinamis yang ada

---

## 4. SR-MT1 (static-routing-mt1)

### Backend Snapshot
- **Hostname**: SR-MT1
- **Platform**: routeros
- **Management**: 172.22.134.144

### Temuan Routing (perlu diverifikasi live)
State routing table dan alamat IP tidak tersedia pada snapshot. Perlu eksekusi:
```
/ip route print detail
/ip address print
```

### Analisis
Device ini secara khusus digunakan untuk skenario static routing (berdasarkan nama `static-routing-mt1`). Ini adalah device latar belakang yang mungkin menjadi gateway atau peer static routing.

### Rekomendasi: Sintaks menambahkan static route
```routeros
/ip route
add dst-address=192.168.50.0/24 gateway=172.22.134.1 distance=1 comment="Route-to-SR-R2"
```

### Langkah berikutnya (SR-MT1)
1. Cek daftar alamat IP: `/ip address print` — lihat subnet di interface mana saja
2. Cek route yang sudah ada: `/ip route print detail`
3. Tambahkan static route ke network yang belum terjangkau
4. Uji reachability dengan: `ping 192.168.50.1` (ganti dengan gateway tujuan)

---

## Ringkasan Umum: Cara Menambah Static Route di MikroTik

### Sintaks dasar (CLI)
```routeros
/ip route add dst-address=<network/CIDR> gateway=<gateway-IP> [distance=<1-255>] [comment="<deskripsi>"]
```

### Via Winbox/Web
1. Buka **IP → Routes**
2. Klik tambah (+), isi:
   - **Dst Address**: network tujuan (misal `192.168.99.0/24`)
   - **Gateway**: pilih IP gateway langsung
   - **Distance**: biarkan 1 (default)
3. Klik **OK**

### Verifikasi setelah menambah
```routeros
/ip route print detail where dst-address=<network-anda>
```

### Catatan penting
- Gateway **harus** berada di jaringan interface yang terhubung langsung (reachable via connected route). Jika tidak, route akan muncul sebagai **"unreachable (X)"** atau **"imprecise"**.
- Gunakan `check-gateway=ping` untuk failover otomatis.
- Gunakan `distance=` untuk mengontrol prioritas route (nilai lebih rendah = prioritas lebih tinggi).

---

## Langkah berikutnya umum
Untuk semua device di atas, yang belum memiliki state routing yang diverifikasi, jalankan live command pada masing-masing device untuk melihat kondisi aktual:

```routeros
/ip route print detail
/ip address print
```

Setelah kita tahu gateway upstream yang valid dan network yang belum terjangkau, baru tambahkan static route sesuai kebutuhan.

**Pertanyaan lanjutan?** Beri tahu device mana yang ingin diatur static routenya (misalnya: "tambah route di SR-MT1 ke network 192.168.50.0/24"), dan saya akan bantu verifikasi gateway yang tepat.