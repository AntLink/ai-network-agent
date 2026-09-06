# AI Network Agent — Handoff untuk Agent Berikutnya

Tanggal handoff: 2026-09-07
Branch kerja: `v5-release-prep`
Commit dasar: `c5b30e7` — `chore: record production gate and OpenHands runtime`

## Status saat ini

Milestone 1 sampai 5 memiliki bukti implementasi dan pengujian bertahap. Release
v0.2.2 sudah dibangun, ditandatangani, diverifikasi, dan diuji pada Edge native
di host production. Production gate terakhir menghasilkan `PASS`.

Bukti utama:

- `docs/production/release-manifest-v0.2.2.json`
- `docs/evidence/production-gates/production-gate-20260907-020201.json`
- `docs/evidence/pki-overlay/production-nginx-revocation-20260907.json`
- `docs/session-logs/2026/09/2026-09-03_1957_phase-04_five-block-production-hardening.md`
- `docs/runbooks/deployment-runbook.md`
- `docs/traceability/requirements-matrix.md`

Jangan memasukkan password, token, private key, certificate private material,
atau isi keystore ke log, commit, issue, atau output diagnostik.

## Perubahan terakhir

- Manifest release v0.2.2 disejajarkan dengan image Central/Edge, SBOM, bundle
  signature, dan hash binary yang sudah diverifikasi.
- `production_ready=true` hanya setelah persetujuan operator tercatat sebagai
  `approved_by=mohfa` dan referensi lisensi `LIC-2026-09-06-001-COMMERCIAL`.
- Evidence PKI/Nginx CRL live ditambahkan; sertifikat probe yang direvoke
  ditolak Nginx sebelum diteruskan ke Central.
- Inventory Central dipersistenkan melalui bind mount
  `/etc/ainet/inventory:/inventory`.
- Installer systemd Edge ditambahkan di
  `edge/installers/systemd/ainet-edge.service`.
- Wrapper OpenHands yang aman di-commit di `openhands/`: README, launcher
  PowerShell, dan DeepSeek browser bridge. Token, database, log, backup,
  dependency, build output, dan dua checkout source nested sengaja tidak
  di-commit.

## Verifikasi yang harus diulang setelah checkout

```powershell
.\env\Scripts\python.exe tools\validate_release_evidence.py
.\env\Scripts\python.exe tools\validate_pki_overlay_evidence.py
.\env\Scripts\python.exe .agents\skills\ainet-zerotier-platform\scripts\production_gate.py --config docs\production\production-gate.json
```

Expected result: ketiga perintah mengembalikan exit code `0`; production gate
menampilkan `PASS: production gate`.

## Langkah berikutnya yang direkomendasikan

1. Pastikan commit ini sudah masuk `main` melalui pull request dari
   `v5-release-prep`; jangan melakukan force-push atau reset terhadap riwayat.
2. Jalankan workflow release dari `main` hanya jika ada perubahan artefak.
   Verifikasi signature dan attestation memakai timeout helper yang ada di
   workflow, bukan loop `cosign` tanpa batas.
3. Untuk perubahan production, ikuti section 19 runbook dan buat evidence baru
   di `docs/evidence/production-gates/`.
4. Untuk perubahan Central/Edge, perbarui traceability dan session log pada
   sesi yang sama; tambahkan ADR hanya untuk keputusan arsitektur berdampak
   tinggi.
5. Prioritas pasca-gate: observability/alert delivery, DR restore berkala,
   Central HA dengan Redis session routing, fault injection, dan semantic parity
   vendor. Jangan menganggap `production gate PASS` sebagai bukti semua skenario
   scale/HA sudah diuji live.

## Kondisi repository

Worktree masih memiliki banyak perubahan dan artefak pengguna lain di luar
commit `c5b30e7` (termasuk perubahan backend, edge, tmp, runtime, dan beberapa
file terhapus). Jangan menjalankan `git reset --hard`, `git clean`, atau staging
global. Selalu gunakan staging path-scoped dan tinjau `git diff --cached`.

Perintah aman untuk memulai:

```powershell
git status --short
git log -1 --oneline
git diff -- docs docs/handoff edge/installers tools/validate_release_evidence.py
```

## OpenHands

Runtime lokal dijalankan melalui script di `openhands/scripts/`. Checkout
`openhands/source/openhands-app` dan `openhands/source/software-agent-sdk`
adalah repository terpisah yang dapat memiliki modifikasi lokal; provision/clone
secara terpisah dan jangan menjadikannya gitlink tanpa `.gitmodules` serta
keputusan lisensi/upstream yang jelas.

## Handoff selesai

Mulai dari membaca dokumen ini, session log terbaru, runbook, traceability, dan
manifest release. Ambil keputusan berdasarkan bukti file dan hasil command,
bukan asumsi dari nama folder.
