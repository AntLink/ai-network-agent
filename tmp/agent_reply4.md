Berikut panduan memeriksa penggunaan disk dan memory di server Linux Ubuntu, disusun per perangkat berdasarkan status terbaru dari lab GNS3.

---

## Ringkasan

Permintaan Anda adalah bagaimana cara memeriksa penggunaan **disk** dan **memory** di server **Linux Ubuntu**.

Lab GNS3 saat ini memiliki tiga host Linux yang aktif:
- `linux-ubuntu` (hostname: **ubuntu**, IP: 192.168.210.51) → **online dan dapat diakses**
- `linux-debian` (hostname: **fauzan**, IP: 172.23.193.80) → **tidak dapat dijangkau dalam snapshot terakhir**
- `linux-embedded` (hostname: **CSMS-SINGKAWANG**, IP: 192.168.162.20) → **tidak dapat dijangkau dalam snapshot terakhir**

---

## 1. Perangkat: **ubuntu** (Linux Ubuntu)

### ✅ Status Perangkat
- **Hostname**: ubuntu  
- **IP Manajemen**: 192.168.210.51  
- **Platform**: Ubuntu  
- **Transport**: SSH  
- **Status**: Aktif dan terhubung  

### 🖥️ Temuan dari Snapshot Terbaru

#### 🔹 Antarmuka Jaringan
Terdapat beberapa antarmuka jaringan termasuk:
- `lo`: loopback
- `enp2s0`: utama, UP, dengan IP 192.168.210.51
- `wlp3s0`: tidak aktif (NO-CARRIER)
- `docker0`: bridge Docker aktif
- `br-dc7a8a53329a`, `br-e35e598509e7`: bridge tambahan
- `veth4b7792e`: virtual ethernet terhubung ke docker0

> *Catatan: Docker dan bridge jaringan menunjukkan sistem container aktif.*

### 📊 Analisis dan Rekomendasi

#### 💾 **Disk Usage**

Gunakan perintah berikut untuk memeriksa penggunaan penyimpanan:

```bash
df -h
```

Contoh keluaran:
```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   30G   18G  63% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
```

Jika ingin melihat penggunaan ruang per direktori:
```bash
du -sh /var/
du -sh /home/*
```

Untuk cek partisi spesifik:
```bash
lsblk
```

#### 💾 **Memory Usage**

Gunakan perintah berikut untuk mengecek penggunaan memori:

```bash
free -h
```

Atau alternatif lebih rinci:
```bash
cat /proc/meminfo
```

Contoh keluaran:
```text
               total        used        free      shared  buff/cache   available
Mem:            15Gi       4.2Gi       8.1Gi       123Mi       3.5Gi        10Gi
Swap:          2.0Gi          0B       2.0Gi
```

Jika ingin memantau secara real-time:
```bash
htop
```

atau tanpa GUI:
```bash
top
```

### ⚙️ Langkah Berikutnya

- Jalankan perintah `df -h` dan `free -h` langsung di server Ubuntu melalui SSH.
- Jika belum terpasang, install `htop` untuk pemantauan interaktif:
  ```bash
  sudo apt update && sudo apt install htop
  ```

---

## 2. Perangkat: **fauzan** (Linux Debian)

### ❌ Status Perangkat
- **Hostname**: fauzan  
- **IP Manajemen**: 172.23.193.80  
- **Platform**: Debian  
- **Transport**: SSH  
- **Status**: **Tidak dapat dijangkau dalam snapshot terakhir**

### 🛑 Temuan
- Perangkat tidak merespons probe kesehatan.
- Semua data terkait (interfaces, routes) dilewati.

### 🔧 Langkah Berikutnya
- Pastikan host ini hidup dan terhubung jaringan.
- Lakukan ping ke alamat manajemennya:
  ```bash
  ping 172.23.193.80
  ```
- Coba SSH kembali:
  ```bash
  ssh user@172.23.193.80
  ```
- Jika tetap tidak responsif, cek VM/nodenya di GNS3 atau hypervisor.

---

## 3. Perangkat: **CSMS-SINGKAWANG** (Linux Embedded)

### ❌ Status Perangkat
- **Hostname**: CSMS-SINGKAWANG  
- **IP Manajemen**: 192.168.162.20  
- **Platform**: Embedded Linux  
- **Transport**: SSH  
- **Status**: **Tidak dapat dijangkau dalam snapshot terakhir**

### 🛑 Temuan
- Perangkat tidak merespons probe kesehatan.
- Semua data terpaut dilewati.

### 🔧 Langkah Berikutnya
- Verifikasi ketersediaan fisik atau VM ini.
- Lakukan ping dan SSH serupa seperti pada perangkat Debian.

---

## Ringkasan Akhir

| No | Hostname        | IP              | Status     | Rekomendasi                             |
|----|------------------|------------------|------------|------------------------------------------|
| 1  | ubuntu          | 192.168.210.51    | Online     | Gunakan `df -h` dan `free -h`            |
| 2  | fauzan          | 172.23.193.80     | Offline    | Periksa konektivitas dan layanan SSH     |
| 3  | CSMS-SINGKAWANG | 192.168.162.20    | Offline    | Verifikasi host/noda di GNS3             |

Jika Anda ingin saya mengeksekusi langsung perintah di atas di salah satu perangkat yang online, beri tahu saya.