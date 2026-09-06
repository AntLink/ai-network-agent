# Session Log: Config Workflow Integration

Tanggal: 2026-08-25

## Fokus

Memulai Phase D: menghubungkan halaman `/configurations` ke backend config governance, bukan direct vendor write endpoint.

## Perubahan

- Menambahkan type:
  - `ConfigPlan`
  - `ConfigApplyResult`
- Menambahkan service API:
  - `createConfigPlan()`
  - `getConfigPlan()`
  - `applyConfigPlan()`
- Memperbarui `src/views/configurations/index.tsx` menjadi workflow:
  - pilih target device
  - pilih mode raw/structured/AI placeholder
  - generate command candidate
  - create backend plan
  - tampilkan dry run, plan id, risk, target, status
  - require approval identity
  - confirmation modal sebelum apply
  - apply via `/api/v1/config/apply`
- Memperluas `ConfirmAction` agar dapat menjalankan `onConfirm` dan disabled state.

## Endpoint

- `POST /api/v1/config/plan`
- `GET /api/v1/config/plans/{plan_id}` disiapkan di service layer
- `POST /api/v1/config/apply`
- `POST /api/v1/config/rollback` belum diwiring ke UI karena butuh backup id valid

## Sanity Check

`POST /api/v1/config/plan` berhasil membuat plan:

```text
plan_id: 1059a24c
device_id: cisco-iosv-r1
risk_level: MEDIUM
status: planned
```

Tidak ada apply/deploy yang dijalankan pada sanity check ini.

## Safety

- Halaman `/configurations` tidak memakai direct Cisco/MikroTik write endpoint.
- Apply memerlukan confirmation modal.
- Apply memerlukan approval identity.
- Frontend tidak menyimpan credential dan tidak membuka SSH langsung.

## Validasi

- `npm run lint` sukses.
- `npm run build` sukses.
