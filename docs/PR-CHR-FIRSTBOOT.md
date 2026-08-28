# PR - Full-auto First-boot MikroTik CHR (via console telnet GNS3)

## Status: TUNTAS (validated 2026-08-28)

First-boot MikroTik CHR fresh sudah berhasil direproduksi lewat endpoint FastAPI
pada node baru di project GNS3 `Security-Lab`.

## Konteks & arsitektur
- Engine console: `backend/app/transports/console.py` (`ConsoleTransport`).
- Jalur endpoint: `POST /api/v1/gns3/projects/{p}/nodes/{n}/console-exec` (`gns3.py`) -> `ConsoleTransport.run()`.
- Tool MCP: `net_console_exec_node(project_id, node_id, command, username, password, enable, bootstrap, ...)`.

## Root cause yang ditangani
- Telnet console GNS3 mengirim IAC negotiation berulang; balasan duplicate bisa membuat dialog login tidak stabil.
- Byte IAC dan ANSI/private terminal sequence masuk ke buffer parsing sehingga prompt `MikroTik Login:` kadang tidak terbaca bersih.
- RouterOS CHR menerima username paling stabil dengan `CR` saja, bukan `CRLF`.
- Prompt first-boot RouterOS kadang dirender per karakter, misalnya `n\ne\nw\n \np...`; regex biasa tidak cukup.
- RouterOS menolak password baru yang sama dengan password lama (`admin`), sehingga `bootstrap_password=admin` perlu fallback ke password berbeda.

## Urutan first-boot CHR yang dipakai
```text
connect -> Enter
MikroTik Login: admin
Password: (kosong)
Do you want to see the software license? [Y/n]: n
new password> admin
Try again, error: New password is the same as old one
new password> admin123
repeat new password> admin123
[admin@MikroTik] >
```

## Yang diterapkan di ConsoleTransport
- Stateful telnet IAC negotiation: opsi yang sudah dijawab tidak dibalas ulang.
- Strip byte telnet IAC sebelum decode dan prompt parsing.
- ANSI cleaner diperluas untuk sequence RouterOS seperti `ESCc` dan `ESC[?7l`.
- Login prompt dan password prompt dipisah agar `MikroTik Login:` selalu diperlakukan sebagai username.
- Username dikirim dengan `CR` saja untuk RouterOS CHR.
- Prompt `new password>` / `repeat new password>` dikenali walau dirender per karakter dengan newline.
- Bootstrap password memakai kandidat unik: nilai request, lalu fallback `admin123`.

## Validasi live
- Project GNS3: `Security-Lab`
- Project ID: `1157797f-3412-4d88-9dd3-eec35662be45`
- Node fresh endpoint: `CHR-FRESH-ENDPOINT2`
- Node ID: `cccac051-e219-43cf-8402-00ff37f05a3e`
- Template: `MikroTik CHR 7.22.1`
- Endpoint create node: `POST /api/v1/gns3/projects/{project_id}/nodes/create`
- Endpoint start node: `POST /api/v1/gns3/projects/{project_id}/nodes/{node_id}/start`
- Endpoint first-boot console exec: `POST /api/v1/gns3/projects/{project_id}/nodes/{node_id}/console-exec`
- Payload first boot: `username=admin`, `password=""`, `allow_empty_password=true`, `bootstrap_password=admin`
- Command validasi: `/system identity print`
- Output berhasil memuat: `name: MikroTik`
- Uji sesi lanjutan berhasil via endpoint dengan `username=admin`, `password=admin123`.

## Regression test
Test di `backend/tests/test_console_transport.py`:
- IAC negotiation bytes dibuang sebelum prompt parsing.
- ANSI/private RouterOS sequence dibersihkan.
- Duplicate telnet option tidak dibalas ulang.
- Bootstrap password fallback dari `admin` ke `admin123` ketika RouterOS menolak password yang sama dengan password lama.
- Prompt password RouterOS yang terpecah per karakter tetap terdeteksi sebagai `newpass`.

## Pattern operasional
- CHR fresh: jalankan first-boot via `console-exec` dengan empty password + `bootstrap_password`.
- Jika `bootstrap_password=admin`, transport otomatis fallback ke `admin123`.
- CHR setelah first-boot: jalankan `console-exec(username="admin", password="admin123")`.
- Setelah lab siap, pindah ke SSH (`transport=ssh`) untuk operasi RouterOS normal.
