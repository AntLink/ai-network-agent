# Session Log: Frontend Read-only Backend Integration

Tanggal: 2026-08-25

## Fokus

Memulai integrasi frontend ke backend FastAPI sesuai rekomendasi Phase A dan Phase B.

## Perubahan

- Menambahkan API client foundation di `src/api/network/backend-client.ts`.
- Menambahkan timeout request, error normalization, dan fallback MSW saat mode dev.
- Menambahkan dukungan environment:
  - `VITE_API_BASE_URL`
  - `VITE_USE_MOCKS`
- Menambahkan `.env.example`.
- Menghubungkan hook read-only:
  - `useDashboardSummary`
  - `useNetworkHealth`
  - `useDevices`
  - `useDeviceDetail`
  - `useTopology`
  - `useAuditLogs`
- Menambahkan adapter backend agar response FastAPI yang belum seragam tetap masuk ke type frontend.

## Endpoint Backend Yang Dicek

- `GET /health` -> 200
- `GET /api/v1/devices` -> 200
- `GET /api/v1/topology` -> 200
- `GET /api/v1/audit` -> 200

## Catatan

- Tidak ada SSH langsung dari frontend.
- Hook lain seperti tasks, terminal, configurations, backups, alerts, credentials, settings, discovery, agent, GNS3, dan Containerlab masih memakai mock sampai phase integrasi berikutnya.
- `useNetworkHealth` sementara membuat series dari snapshot inventory device karena endpoint agregat monitoring belum tersedia.
- Backend topology saat ini masih mengembalikan topology kosong.

## Validasi

- `npm run lint` sukses.
- `npm run build` sukses.
- Warning Vite terkait `optimizeDeps.esbuildOptions` masih ada, tetapi bukan error dari perubahan ini.
