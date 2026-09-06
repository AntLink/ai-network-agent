## Ringkasan

Berikut panduan membuat VLAN dan mengkonfigurasi trunk pada switch Cisco IOS (Layer 2), lengkap dengan sintaks, verifikasi, dan contoh kasus.

---

## Apa Itu VLAN dan Trunk?

- **VLAN (Virtual LAN)**: Memecah broadcast domain secara logis pada switch layer 2. Setiap VLAN adalah broadcast domain tersendiri.
- **Trunk**: Link point-to-point yang dapat membawa lalu lintas dari **banyak VLAN** secara bersamaan menggunakan tag IEEE 802.1Q.

---

## Langkah 1: Membuat VLAN

```ios
Switch> enable
Switch# configure terminal
Switch(config)# vlan 10
Switch(config-vlan)# name Sales
Switch(config-vlan)# exit
Switch(config)# vlan 20
Switch(config-vlan)# name Engineering
Switch(config-vlan)# exit
```

### Penjelasan:
| Perintah | Keterangan |
|---|---|
| `vlan <id>` | Membuat/masuk ke VLAN dengan ID tertentu |
| `name <nama>` | Memberi nama pada VLAN (opsional tapi disarankan) |
| `exit` | Keluar dari mode VLAN |

---

## Langkah 2: Menambahkan Port ke VLAN (Access Port)

Port yang menjadi anggota VLAN harus diatur sebagai **access port**:

```ios
Switch(config)# interface range fastethernet 0/1 - 12
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport access vlan 10
Switch(config-if-range)# exit
```

### Penjelasan:
| Perintah | Keterangan |
|---|---|
| `switchport mode access` | Mengatur port sebagai access port |
| `switchport access vlan <id>` | Menentukan VLAN mana yang menampung port ini |

---

## Langkah 3: Membuat Trunk Port

Port trunk menghubungkan dua switch dan membawa lalu lintas dari banyak VLAN:

```ios
Switch(config)# interface gigabitethernet 0/24
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk allowed vlan 10,20
Switch(config-if)# exit
```

### Penjelasan:
| Perintah | Keterangan |
|---|---|
| `switchport mode trunk` | Mengaktifkan mode trunk (auto-negosiasi IEEE 802.1Q) |
| `switchport trunk allowed vlan 10,20` | Membatasi/mematulkan VLAN yang dapat melewati trunk |

Untuk mengizinkan **semua VLAN** (default):
```ios
Switch(config-if)# switchport trunk allowed vlan all
```

---

## Langkah 4: Verifikasi Konfigurasi

```ios
Switch# show vlan brief
Switch# show interfaces trunk
Switch# show interfaces g0/24 switchport
Switch# show spanning-tree vlan 10
```

---

## Contoh Kasus Lengkap

Skenario: Membuat 3 VLAN dan menghubungkan 2 switch via trunk.

### Switch A (Primary):
```ios
Switch> enable
Switch# configure terminal
!
! Membuat VLAN
vlan 10
 name Sales
vlan 20
 name Engineering
vlan 30
 name Guest
!
! Mengatur access port
interface range fa0/1 - 6
 switchport mode access
 switchport access vlan 10
!
interface range fa0/7 - 12
 switchport mode access
 switchport access vlan 20
!
! Mengatur trunk
interface gi0/24
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
!
end
write memory
```

### Switch B (Remote):
```ios
Switch> enable
Switch# configure terminal
!
vlan 10
 name Sales
vlan 20
 name Engineering
vlan 30
 name Guest
!
interface range fa0/1 - 4
 switchport mode access
 switchport access vlan 10
!
interface gi0/24
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
!
end
write memory
```

---

## Best Practice

```ios
! Hapus VLAN default (VLAN 1) dari trunk agar lebih aman
interface gi0/24
 switchport trunk allowed vlan 10,20,30

! Matikan DTP (Dynamic Trunking Protocol) untuk keamanan
interface gi0/24
 switchport mode trunk
 switchport nonegotiate

! Verifikasi
show interfaces trunk
show vlan brief
```

---

```plan
{
  "steps": [
    "Masuk ke switch via SSH/console",
    "Buat VLAN dengan perintah: vlan <id>, name <nama>",
    "Atur port sebagai access port: switchport mode access, switchport access vlan <id>",
    "Atur uplink sebagai trunk: switchport mode trunk, switchport trunk allowed vlan <list>",
    "Verifikasi dengan: show vlan brief, show interfaces trunk",
    "Simpan konfigurasi: write memory / copy running-config startup-config"
  ],
  "risk": "Rendah — tidak ada perubahan pada perangkat produksi langsung"
}
```

---

## Langkah berikutnya

Jika ingin mempraktikkan di lab GNS3, saya dapat bantu verifikasi konfigurasi pada switch **SW1** atau **SW2** yang tersedia. Namun perlu dipastikan switch tersebut sudah berjalan dan dapat dijangkau (pada snapshot terkini, keduanya tercatat **not reachable**). Silakan konfirmasi apakah ingin saya bantu cek status connectivitynya dulu.