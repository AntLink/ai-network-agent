# RE csmsd.elf — TCI CSMS Spectrum Monitor (192.168.162.20)

Update: 2026-08-21 (Fase 1 + Fase 2 selesai)
Target: CSMS-SINGKAWANG (TCI Compact Spectrum Monitoring Server, fw 2.07.0010)
Binary: `/media/tci/csms/bin/csmsd.elf` — ARM32 EABI5, 12.4 MB, not stripped, DWARF v4 (-g1: line info only)

---

## 1. Service Management

| Aksi | Perintah |
|---|---|
| Start (stabil) | `cd / && setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'` |
| Start (resmi) | `PATH=/sbin:$PATH /etc/rc5.d/S99csmsd start` — **tidak stabil**: child `--daemon` sering mati diam-diam |
| Stop | `killall csmsd.elf` (tunggu mati total ±3 detik; SIGTERM ditangani tertunda) |
| Watchdog | `/media/tci/SpectrumMonitor` loop 30s auto-relaunch via S99csmsd |
| Catatan | csmsd saat start menjalankan `killall SpectrumMonitor`; port naik **±75 detik** setelah launch |

**Jebakan yang teridentifikasi:**
- Jangan pipe output ke `head` — child mewarisi pipe SSH → mati saat sesi tutup
- Hapus pidfile `/media/tci/csms/csmsd.pid` sebelum start manual
- dropbear menutup koneksi SSH jika command line > ~10 KB (pakai SFTP untuk payload besar)

## 1b. Urutan Boot Linux (rc5.d) — penting untuk environment csmsd

```
S01networking     : ifup dasar
S10dropbear       : SSH server
S18tcinet         : salin /media/httpd/cgi-bin/interfaces -> /etc/network,
                    ifdown/ifup ulang, verifikasi IP (DHCP atau static)
S20syslog         : syslog
S25tcistartup     : - start busybox httpd (port 80, root /media/httpd)
                    - copy CSMSConfig++.xml ke /media/httpd
                    - modprobe csmsdigi          (driver digitizer FPGA)
                    - ntpd -gGNc                 (waktu HARUS sync dulu)
                    - gpsd -G -n /dev/ttyPS1
                    - csmsAudio.elf &            (sebelum csmsd!)
                    - /media/TCI/SendIP.elf
                    - syslogd config TCI (/etc/syslog1|2 -> eventlog?)
                    - ifplugd -I -i eth0 -r /media/TCI/ifplugdnet.sh
                      ^^^ ifplugdnet.sh: ifdown -a; sysctl; ifup -a
                          (dipanggil SETIAP perubahan link eth0 -> SSH bisa putus)
                    - nodeId dari CSMSConfig.xml menentukan DF master/slave
S99csmsd          : csmsd --daemon (via start-stop-daemon)
```

Catatan: `ifplugdnet.sh` asli dipanggil dari `/media/TCI/ifplugdnet.sh`
(salinan lain ada di /media/httpd/cgi-bin/). Flap kabel eth0 = restart jaringan =
sesi SSH aktif akan terputus.

| Port | Kelas | Protokol |
|---|---|---|
| TCP 3302 | **CMetricsNet** | SSmsMsg binary (utama — kontrol+data pengukuran) |
| TCP 3303 | CVCPCtrlNet / EquipCtrlNet | SSmsMsg binary (VCP per-node) |
| TCP 3307 | CRealtimeNet | Header 12B (bodyLen u32@8), diam thd probe |
| UDP 5060 | csmsAudio.elf | RTP audio |
| TCP 80 | busybox httpd | Web UI |

## 2. Wire Format (port 3302/3303)

Pesan = `[header 20B][body bodyLen B]` — **TANPA delimiter**.

> ⚠️ KOREKSI PENTING (15:28): temuan lama "delimiter 0x0a" SALAH. Server memakai
> framing length-prefixed murni. Mengirim `\n` membuat server kehilangan sinkron
> 1 byte untuk SEMUA pesan berikutnya di koneksi yang sama → "invalid message type"
> / "bad version" dengan nilai sampah (terbukti via log: `type 6912 subtype 25599745`).
> Greeting tetap lolos karena pesan pertama, tapi pesan ke-2 dst rusak.

```
SSmsMsg::SHdr (20 byte, little-endian):
  +0x00 u32 marker/id   ← DI-ECHO balik server di response
  +0x04 u32 ?           (ikut ter-copy)
  +0x08 u16 msgType
  +0x0A u8  cmdVer      ← VERSI command (lihat catatan compressed di bawah)
  +0x0B u8  respVer     ← VERSI response
  +0x0C u32 subtype     (validasi per-handler)
  +0x10 u32 bodyLen     (divalidasi: bodyLen+20 == totalLen)
```

Error response: header 20B `msgType=9999 (0x270F)`, errorCode u32 @0xC, echo marker @0x00.

### 3a. Gate "compressed" — TERPECAHKAN

`CMetricsNet::IsBodyCompressed()` (0x11da90) menolak pesan yang versinya di bawah
threshold. Threshold ada di std::map runtime (base 0x1ad5c00) key `(msgType, subtype)`
→ value `(cmdVer_min, respVer_min)` (255 = wildcard).

Entri kunci (dump dari /proc/PID/mem):
```
8565 greeting REQ  sub0 → cmdVer_min=1  respVer=255
8566 greeting RES  sub0 → cmdVer=255    respVer_min=1
8563 pan REQ       sub1,2 → cmdVer_min=1
```

Jadi untuk greeting 8565 **cmdVer & respVer harus ≥ 1** (catatan lama "cmdVer harus 0"
ternyata SALAH). Test live (14:42): `cmdVer=1 respVer=1` → `sent MEASUREMENT_GREETING_RES`.

## 3. Dispatch Table Port 3302 (CMetricsNet::OnMessage) — TERKONFIRMASI

| Type | Handler | Status live test |
|---|---|---|
| 27 | `OnMeasureCtrl` | ✅ log "Got invalid MEASURE_CTRL subtype N" |
| 28 | `OnDemodCtrl` | err=3 (dikenal) |
| 30 | `OnOccupancyCtrl` | err=6 @subtype 0 |
| 31 | `OnBistCtrl` | err=6 @subtype 0 |
| 33 | `OnAvdCtrl` | err=6 @subtype 0 |
| 34 | `OnOccupancyDfCtrl` | err=6 @subtype 0 |
| 52 | `OnPriorityCtrl` | — |
| 53 | `OnSuperUserCtrl` | err=6 @subtype 0 |
| 60 | `Net::OnStatusCtrl` | sub1=no-op, sub3→err6, sub5=silent |
| 62 | `OnSystemStateCtrl` | err=6 @subtype 0 |
| 66 | `OnDmCtrl` | err=6 @subtype 0 |
| **8563** | **`OnMeasurementPanReq`** ⭐ | ✅ tercapai (log), err=3 dengan body kosong |
| **8565** | **`OnMeasurementGreetingReq`** ⭐ | ✅ pernah tercapai (log "Got MEASUREMENT_GREETING_REQ") |
| 8566 | `MEASUREMENT_GREETING_RES` | tipe response greeting (dari disasm) |

Handler lain terkonfirmasi via simbol (kelas CEquipControl/CMetrics): DfCtrl(25), MetricsCtrl(26),
PanDispCtrl(29), EquipmentCtrl(50), AntCtrl(61), VCPCtrl(64), DmCtrl(66).
`CEquipControl::OnStatusCtrl`: subtype 5 = GET_CSMS_FAULT → kirim `SGetCsmsFaultRespV2` (body 984B).

### Dispatch subtype type 27 (OnMeasureCtrl) — dipetakan 14:55

Subtype (header +0x0C) menentukan aksi; body wajib `[token 4B][param...]`:

| subtype | handler | arti |
|---|---|---|
| 9        | `SendAntListResp` | daftar antena |
| 71000 (0x11558) | `ScheduleMeasurement` ⭐ | jadwalkan pengukuran baru |
| 71001 (0x11559) | `DeleteResults` | hapus hasil |
| 71002 (0x1155a) | `RetrieveMeasurement` ⭐ | ambil hasil ukur (data spektrum) |
| 71003 (0x1155b) | `ForwardToEquipControl` | teruskan ke equip ctrl |
| 71016 (0x11568) | `ForwardToEquipControl` | idem |
| 71017 (0x11569) | `RetrieveIqData` | ambil data IQ |
| 71018 (0x1156a) | `RetrieveIqData` | idem |

Alur live: greeting → **ScheduleMeasurement (71000)** → tunggu → **RetrieveMeasurement (71002)**.
Body kedua request ini (struct `SMeasureCtrlMsgGenericRequestV0`) belum di-reverse; itu langkah terakhir.

## 4. Kode Error (SMS_ERROR_REPORT)

| Wire | Arti empiris |
|---|---|
| 2 | client lain sudah terdaftar (IsSameClient gagal) |
| 3 | handler dikenal, parameter/prasyarat salah (28,61 @sub0; PanReq body kosong) |
| 5 | tipe tidak dikenal |
| 6 | tipe dikenal, subtype invalid |
| 13 | versi/format request ditolak gate (TANPA log) |
| 169 | internal (jarang) |

## 5. Model Sesi Klien

- Hanya **satu measurement client** aktif global (`IsSameClient`, slot di CMetrics+0x44..0x70)
- Greeting: subtype harus 0; body ≥36 byte dipakai sebagai identitas klien
- Respons greeting = `MEASUREMENT_GREETING_RES` via `SendImmediateResp`
- **BLOCKER TERPECAHKAN** (14:45): greeting lolos dengan `cmdVer=1 respVer=1`.
  Penyebab lama: cmdVer=0 → `IsBodyCompressed` true → "unsupported compressed message" → err 13.
- **SESSION TOKEN**: body respons greeting (4 byte, mis. `b2d1be78`) disimpan server di
  `CMetrics+0x70`; request berikutnya (Pan/MeasureCtrl) wajib meng-echo token ini di
  **4 byte pertama body** (`OnMeasurementPanReq` membandingkan `body[0..4] == token`),
  dan harus datang dari koneksi TCP yang sama (slot `CMetrics+0x44`).

## 6. Data Alternatif (tanpa TCP)

- SQLite `/media/tci/csms/data/csmsdb.db` (36.9 MB):
  - `Schedule` 18 baris (task pengukuran), `Results` 1892 baris
  - MsgBody BLOB ≈ 1500 titik float64 dBm per sweep — **data spektrum asli siap pakai**
- Shared memory: TIDAK berguna (ShMem3230=32B, ShMem2630=304B — flag koordinasi saja)

## 7. Recovery csmsd

```sh
killall -9 csmsd.elf; rm -f /media/tci/csms/csmsd.pid
cd /
setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
# tunggu ±75-90s sampai netstat menunjukkan 3302/3303/3307
```

## 8. Langkah Lanjutan (urutan prioritas)

1. **Sniff trafik asli** (paling cepat): jalankan tcpdump/tcpflow di device sambil TCI client
   resmi (Windows) connect ke 3302 — seluruh handshake & format body langsung kelihatan tanpa tebakan.
2. Selesaikan precondition greeting (bedah gate err13-silent di CMetricsNet::OnMessage 0x123200-0x123320).
3. Format body per-komando via disasm handler masing-masing (struct V1..V6 ada di simbol `SSmsMsg::S*`).
4. Fallback praktis: SQLite reader (parser blob → array spektrum) untuk backend.

## 8a. Endpoint REST (Fase database - SIAP PAKAI)

Server: `python -m uvicorn app.csms_monitor.main:app --port 8000`

| Endpoint | Isi |
|---|---|
| GET /api/v1/spectrum-db/measurements?limit=N | daftar pengukuran + jadwal |
| GET /api/v1/spectrum-db/latest | 5 sweep sinyal terkuat + puncak |
| GET /api/v1/spectrum-db/spectrum/{id} | sweep lengkap per bin |

File: app/csms_monitor/spectrum_db.py (+ routers/spectrum_db.py).
Fitur: gzip transfer, cache TTL 300s, timeout SSH/SFTP.

## 9. Artefak Analisis (lokal)

- `csmsd_elf/csmsd.elf` — binary target; `csmsAudio.elf`, `ProcessConfig.elf`
- `analyze_csmsd_*.py` — script ELF/disasm/DWARF/line-info
- `csmsd_line_tables.pkl` — peta addr→file:line (MetricsNet.cpp & EquipCtrlNet.cpp)
- `re_csmsd_step*_log.txt` — log semua eksperimen live
- DB copy: `csmsd_elf/csmsdb_copy.db`

## 10. Cloudflared Auto-Restore (ditambahkan 2026-08-21)

Tunnel Cloudflare berbasis token (`tunnel run --token eyJ...`), tanpa config.yml.
File penting: binary+launcher di `/media/httpd/cgi-bin/`, init `/etc/init.d/cloudflared`,
link `/etc/rc5.d/S99cloudflared`. Backup lengkap: `/media/backup/cloudflared/`.

**Modifikasi `/media/TCI/ifplugdnet.sh`** (script ifplugd callback yang selalu jalan
saat boot/link event — baris terakhirnya sudah memanggil `S99csmsd start`):
ditambah blok auto-restore setelahnya:
1. Cek 4 file cloudflared (binary, launcher, init.d, rc-link)
2. Yang hilang dikembalikan dari `/media/backup/cloudflared/`
3. Start tunnel via `S99cloudflared start` jika `pidof cloudflared-linux-arm` kosong
4. Idempotent + logging ke syslog (`logger -t cf-restore`)

Backup script asli:
- Device : `/media/TCI/ifplugdnet.sh.bak-20260821`
- Lokal  : `backend/ifplugdnet.sh.orig`

Hasil uji: normal = no-op; simulasi file hilang = semua pulih otomatis,
tunnel tetap hidup. ✅
## 11. Config Auto-Restore + fix-dns (ditambahkan 2026-08-21)

Ternyata akar penyebab "konfigurasi sering hilang": `/etc/network/if-pre-up.d/fix-dns`
hilang -> tiap `ifup` (termasuk di ifplugdnet.sh), DHCP menimpa `/etc/resolv.conf`
-> DNS rusak -> tunnel cloudflared putus.

**Ditambahkan blok kedua ke `/media/TCI/ifplugdnet.sh`** (disisipkan SEBELUM `ifdown -a`):
1. Restore-if-missing dari `/media/backup/configs/<terbaru>/` untuk:
   hostname, hosts, fstab, inittab, **passwd**, **group**, profile,
   interfaces, dns-setup
2. Membuat `fix-dns` hook jika hilang: mengisi ulang nameserver
   (1.1.1.1, 8.8.8.8, 192.168.162.1) sebelum interface naik
3. Kebijakan aman: file yang ADA tidak pernah ditimpa (perubahan sengaja aman)

Catatan: backup `fix-dns.txt` korup (ada sisa heredoc) - konten benar ditulis
langsung di blok, bukan dari backup.

Backup script v3: `/media/TCI/ifplugdnet.sh.bak2-*` (device),
`ifplugdnet.sh.v2` (lokal). Uji: fix-dns dibuat & tervalidasi, passwd/group
tidak tersentuh, tunnel tetap hidup.

## 12. Sesi 2026-08-21 (sore): protokol measurement TERBUKA

### 12.1 SendIP.elf = servis "getip", bukan jalur data

Disasm penuh (19KB, `SendIP.c`, ARM32): bind UDP 0.0.0.0:**18331**, ioctl
`SIOCGIFADDR("eth0")`; kalau datagram berisi substring `"getip"` → balas
`"ip address = <ip-eth0>"` ke pengirim port 18331. Tidak ada relay data.
→ **UDP 18331 dieliminasi** dari daftar tap spektrum.

### 12.2 Dua tabel versi di memori csmsd (dump via /proc/PID/mem, Perl)

Struct global `0x1ad5c00` berisi DUA std::map keyed `(msgType, subtype)`:

| map | alamat | value | fungsi |
|---|---|---|---|
| MAP1 | 0x1ad5c00 | `(cmdVer_min, respVer_min)`, 255=wildcard | gate "compressed" (`IsBodyCompressed` 0x11da90) |
| MAP2 | 0x1ad5c18 | `(cmdVer_cur, respVer_cur)` | cek versi di `OnMessage` (upconvert / "bad version") |

Aturan gabungan untuk sebuah pesan:
```
MAP1: cmdVer >= cmdVer_min  DAN respVer >= respVer_min  → body tidak "compressed"
MAP2: cmdVer <= cmdVer_cur  DAN respVer <= respVer_cur  → versi dikenali
```
Entri penting (kedua map):

| type/sub | MAP1 min | MAP2 cur | arti |
|---|---|---|---|
| 8565/0 greeting REQ | cv≥1, rv≥1 | cv1 rv1 | **cv=1 rv=1** |
| 8566/0 greeting RES | cv=255, rv≥1 | cv1 rv1 | respon greeting |
| 27/71000 ScheduleMeasurement | cv≥2 | cv5 rv2 | jadwalkan ukur |
| 27/71002 RetrieveMeasurement REQ | cv≥1 | cv1 rv5 | ambil hasil |
| 27/**72002** Retrieve RES (SGetMeasRespV5) | cv=255, **rv≥2** | cv1 rv5 | **respon butuh rv≥2** |
| 8563/1..2 PanReq | cv≥1 | cv2 rv3 | panoramic |

### 12.3 RetrieveMeasurement — ALUR LENGKAP JALAN ✅

```
greeting(8565, cv=1, rv=1, body 36B)
  → 8566 + token 4B
retrieve(27, sub=71002, cv=1, rv=2, body=u32 measureId)   ← rv=2 WAJIB
  → 27/sub=72002, bodyLen≈40KB
     body[0:4]=measureId echo, body[40768]=status, body[40772]=stationId(IP)
```

Status yang teramati: **509** = entri schedule tidak ketemu di memori
(GetRow→101). DB SQLite punya MeasureId 5509–5595 State=2 + Results 1892 baris,
jadi lookup in-memory csmsd kemungkinan stale/pakai key lain (Key column?) —
investigasi lanjut.

Log bukti: `Got MEASUREMENT_REQUEST measId = 5595 from 192.168.6.80`.

### 12.4 Bug framing `\n` (penyebab semua request measurement "tidak merespons")

Gejala lama: greeting OK, pesan ke-2 dst → error sampah
(`invalid message type ... type 6912`) = header tergeser 1 byte.
Akar: `\n` tidak dikonsumsi server → nyangkut di buffer → pesan berikutnya
terbaca mulai dari byte `\n`. Fix: kirim tanpa `\n` (lihat §2).

### 12.5 Artefak

- `backend/csms_client.py` — client SMetricsNet final (tanpa `\n`,
  `retrieve_measurement(id)` pakai rv=2, konstanta subtype).
- Tap bridge (`csms-bridge-armv7` v0.3.0) ter-deploy; reassembly TCP
  3302/3303/3307 + `/spectrum/status` + `/spectrum/raw/live`.
- Dump tabel: `perl /tmp/dump_both.pl <pid>` (baca /proc/PID/mem).

### 12.6 Langkah lanjut

1. Cari key lookup schedule in-memory (kenapa 5595 → 509): bandingkan
   kolom `Key` vs `MeasureId`, atau trigger ScheduleMeasurement (71000, cv≥2)
   untuk membuat entri baru lalu retrieve.
2. Parse body 72002 → ekstrak array float64 sweep (format sama dengan
   MsgBody BLOB di Results).
3. Realtime live: tap 3307 (CRealtimeNet) saat pengukuran berjalan.