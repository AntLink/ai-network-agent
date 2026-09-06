# Session Log: Terminal Backend Integration

Tanggal: 2026-08-25

## Fokus

Memulai Phase C: menghubungkan halaman `/terminal` ke endpoint command backend tanpa SSH langsung dari browser.

## Perubahan

- Menambahkan `TerminalCommandResult` di `src/types/network.ts`.
- Menambahkan `runBackendTerminalCommand()` di `src/api/network/backend-client.ts`.
- Mengekspor `runTerminalCommand()` dari `src/api/network/index.ts`.
- Memperbarui `src/views/terminal/index.tsx`:
  - device selector sekarang mengubah target device
  - command dikirim async ke backend
  - output masuk ke transcript lokal
  - command history lokal ditambahkan
  - ada running state
  - ada error banner
  - ada pesan policy blocked jika backend menolak direct endpoint
  - ada catatan bahwa streaming/SSE belum tersedia
  - ada command autocomplete/helper per vendor
  - ada risk badge untuk command input
  - read-only command langsung jalan
  - low/medium/high risk command butuh confirmation
  - critical command diblokir dari terminal

## Endpoint Yang Dipakai

- Cisco: `POST /api/v1/cisco/{device_id}/exec`
- MikroTik: `POST /api/v1/mikrotik/{device_id}/commands/run`
- Fallback: `POST /api/v1/devices/{device_id}/console/exec`

## Catatan Safety

- Frontend tidak membuka SSH langsung.
- Credential tidak disimpan di frontend.
- Backend `direct_write_guard` dapat memblokir command endpoint jika `ALLOW_DIRECT_WRITE=false`.
- Untuk command konfigurasi berisiko, workflow jangka panjang tetap harus lewat config plan/policy/apply.
- Risk classifier frontend hanya guard UX. Backend policy tetap menjadi enforcement utama.

## Validasi

- `npm run lint` sukses.
- `npm run build` sukses.
