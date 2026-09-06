# Ringkasan

Panduan singkat untuk mengaktifkan SSH dan mengonfigurasi **line vty** pada Cisco IOS. Karena ini pertanyaan konfigurasi (bukan troubleshooting device tertentu), langsung saya sampaikan langkah-langkahnya.

---

## Analisis – Prasyarat SSH di Cisco IOS

Agar SSH dapat berfungsi pada router Cisco IOS, semua poin berikut **harus lengkap**:

| No | Komponen | Perintah verifikasi | Keterangan |
|---|----------|---------------------|------------|
| 1 | Nama domain (domain-name) | `show ip domain` | Wajib ada agar RSA key pair tergenerate |
| 2 | RSA key pair | `show crypto key mypubkey rsa` | Digenerasi dengan `crypto key generate rsa` |
| 3 | User lokal (local user) | `show running-config | include username` | Diperlukan untuk auth bila AAA tidak dipakai |
| 4 | Transport VTY | `show running-config | section line vty` | Harus allow `ssh` (bukan `telnet`) |

Jika salah satu kosong → SSH tidak akan bekerja meskipun sudah ada konfig `ip ssh`.

---

## Rekomendasi – Langkah demi langkah

### Langkah 1: Set hostname + domain-name
```ios
R1> enable
R1# configure terminal
R1(config)# hostname R1
R1(config)# ip domain-name tci.local
```

### Langkah 2: Generate RSA key pair (untuk enkripsi SSH)
```ios
R1(config)# crypto key generate rsa
  How many bits in the modulus [512]: 2048
  % The key pair was generated.
```
> 💡 Modulus minimal **2048-bit** agar aman. Jika device sudah pernah generate dengan 512-bit, hapus dulu: `crypto key zeroize rsa`.

### Langkah 3: Buat user lokal (jika tidak memakai AAA)
```ios
R1(config)# username admin privilege 15 secret 0 YourPassword123
```

### Langkah 4: Konfigurasi line VTY — hanya boleh SSH
```ios
R1(config)# line vty 0 15
R1(config-line)# transport input ssh
R1(config-line)# login local
R1(config-line)# exec-timeout 10 0
R1(config-line)# logging synchronous
R1(config-line)# exit
```

| Keyword | Fungsi |
|---------|--------|
| `transport input ssh` | Memblokir Telnet, hanya biarkan SSH |
| `login local` | Gunakan database user lokal |
| `exec-timeout` | Auto-disconnect setelah 10 menit idle |

### Langkah 5: (Opsional) Aktifkan SSH version 2
```ios
R1(config)# ip ssh version 2
R1(config)# ip ssh time-out 60
R1(config)# ip ssh authentication-retries 2
```

### Langkah 6: Verifikasi
```ios
R1# show ip ssh        ← cek apakah server SSH sudah berjalan
R1# show users         ← lihat sesi SSH yang aktif
R1# ping 172.22.45.249 ← pastikan management interface hidup
```

---

## Device State (snapshot backend)

Backend snapshot saat ini menunjukkan **semua perangkat tidak terjangkau** (`reachable: false`) — artinya interface dan routing table belum dapat diverifikasi langsung. Berikut ringkasan status tiap device:

```device_state
{
  "status_overview": [
    {"device": "R1 (cisco-iosv-r1)",        "mgmt_ip": "172.22.45.249",   "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"},
    {"device": "R2 (cisco-iosv-r2)",        "mgmt_ip": "172.22.36.184",   "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"},
    {"device": "SW1 (cisco-iosvl2-sw1)",    "mgmt_ip": "172.22.38.10",    "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"},
    {"device": "SW2 (cisco-iosvl2-sw2)",    "mgmt_ip": "172.22.39.10",    "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"},
    {"device": "SR-R1 (static-routing-r1)", "mgmt_ip": "172.22.134.144",  "port": 2201, "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"},
    {"device": "SR-R2 (static-routing-r2)", "mgmt_ip": "172.22.134.144",  "port": 2202, "reachable": false, "interfaces": "belum terambil data", "routes": "belum terambil data"}
  ]
}
```

> ⚠️ Semua device dalam snapshot **"state belum lengkap"** karena health probe gagal. Konfigurasi di atas bersifat umum dan dapat diterapkan lewat **console (GNS3 Console tab / PuTTY di console_host:console_port)** saat device belum bisa di-SSH-kan.

---

## Langkah berikutnya

Jika Anda ingin menerapkan konfigurasi ini ke salah satu device:

1. Pilih salah satu device (misalnya **R1**).
2. Buka **console session** via GNS3 (console_host `172.22.46.196`, port `5006`).
3. Login via console → masuk ke CLI IOS.
4. Ikuti langkah-langkah di atas **secara berurutan**.
5. Setelah selesai, verifikasi dengan `show ip ssh` dan lakukan test SSH dari host lain.

Ingin saya bantu terapkan konfig ini ke salah satu device tertentu dulu — misalnya **R1** atau **SR-R1**?