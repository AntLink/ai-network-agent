# Panduan Menjalankan AI Network Agent V3 di PyCharm

---

## Daftar Isi
1. [Prerequisites](#prerequisites)
2. [Setup PyCharm](#setup-pycharm)
3. [Cara 1: Menggunakan Run Configuration (Rekomendasi)](#cara-1-menggunakan-run-configuration-rekomendasi)
4. [Cara 2: Manual via Terminal](#cara-2-manual-via-terminal)
5. [Cara 3: Menggunakan Batch File](#cara-3-menggunakan-batch-file)
6. [Verifikasi Server Berjalan](#verifikasi-server-berjalan)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- PyCharm (Community/Professional Edition)
- Python 3.10+ (direkomendasikan 3.14)
- Dependencies sudah terinstall:
  - fastapi
  - uvicorn
  - asyncssh
  - python-dotenv

---

## Setup PyCharm

### 1. Buka Project di PyCharm
- Open PyCharm
- File → Open → Pilih folder `ai-network-agent`
- Tunggu hingga PyCharm selesai indexing

### 2. Set Python Interpreter
- File → Settings → Project → Python Interpreter
- Pilih **Python 3.14** (C:\Python314\python.exe)
- Klik OK

### 3. Mark Sources Root
- Di Project view, klik kanan pada folder `backend`
- Pilih **Mark Directory as** → **Sources Root**

---

## Cara 1: Menggunakan Run Configuration (Rekomendasi)

Run configuration sudah disiapkan di `.idea/runConfigurations/`

### Langkah:
1. Pastikan file-file berikut ada:
   - `.idea/runConfigurations/FastAPI_Server.xml`
   - `.idea/runConfigurations/Tests.xml`

2. **Refresh PyCharm**:
   - File → Synchronize
   - Atau restart PyCharm

3. **Pilih Run Configuration**:
   - Di toolbar atas, pilih **"FastAPI Server"** dari dropdown
   - Klik tombol **Run** (▶️ hijau)

4. **Server akan berjalan** di:
   - URL: http://127.0.0.1:8000
   - Docs: http://127.0.0.1:8000/docs

### Catatan:
- Configuration menggunakan **uvicorn** dengan auto-reload
- Working directory: `backend/`
- Port: 8000
- Host: 0.0.0.0 (akses dari mana saja)

---

## Cara 2: Manual via Terminal

### Di PyCharm Terminal:
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Di Windows CMD:
```cmd
cd C:\Users\mohfa\PycharmProjects\ai-network-agent\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Cara 3: Menggunakan Batch File

File `run_backend.bat` sudah disediakan di root project.

### Cara jalankan:
1. Buka File Explorer
2. Navigasi ke: `C:\Users\mohfa\PycharmProjects\ai-network-agent`
3. Double-click file `run_backend.bat`
4. Server akan berjalan di jendela CMD

---

## Verifikasi Server Berjalan

### 1. Check di Browser
- Buka: http://127.0.0.1:8000
- Harus muncul: `{"status": "ok", "service": "AI Network Agent API"}`

### 2. Check API Docs (Swagger UI)
- Buka: http://127.0.0.1:8000/docs
- Harus muncul dokumentasi API interaktif

### 3. Check Health Endpoint
```bash
curl http://127.0.0.1:8000/health
# Output: {"status":"ok","service":"AI Network Agent API"}
```

### 4. Check MikroTik Endpoint (jika device tersedia)
```bash
curl http://127.0.0.1:8000/api/v1/devices
# Output: Daftar device dari inventory/devices.json
```

---

## Troubleshooting

### Error: ModuleNotFoundError

**Masalah**: `ModuleNotFoundError: No module named 'app'`

**Solusi**:
1. Pastikan working directory adalah `backend/`
2. Atau set environment variable: `PYTHONPATH=backend`

---

**Masalah**: `ModuleNotFoundError: No module named 'uvicorn'`

**Solusi**:
```bash
pip install uvicorn fastapi asyncssh python-dotenv
```

---

**Masalah**: Port 8000 sudah dipakai

**Solusi**:
- Ganti port di run configuration: `--port 8001`
- Atau matikan aplikasi lain yang pakai port 8000

---

**Masalah**: .env file tidak ditemukan

**Solusi**:
- Pastikan file `.env` ada di folder `backend/`
- Atau copy dari `.env.example`
- Isi credentials yang diperlukan

---

**Masalah**: Connection timeout ke device

**Solusi**:
- Pastikan device (MikroTik/Cisco/Linux) menyala
- Cek koneksi jaringan
- Verifikasi credentials di `.env` file

---

## Environment Variables

File `.env` sudah disediakan di `backend/.env` dengan credentials:
- MikroTik RB5009, RB951Ui, CHR
- Cisco IOSv R1, R2, SW1, SW2
- Linux Embedded, Debian, Ubuntu

**JANGAN COMMIT** file `.env` ke Git!

---

## Run Tests

Untuk menjalankan tests:

### Di PyCharm:
1. Pilih run configuration **"Run Tests"**
2. Klik tombol Run

### Manual:
```bash
cd backend
python -m pytest ../tests/ -v
```

---

## Tips & Tricks

### 1. Auto-Reload
Configuration sudah include `--reload` flag. Server akan auto-restart jika ada perubahan code.

### 2. Logs
- Server logs: Terlihat di PyCharm Run console
- Audit logs: Disimpan di `logs/audit.log`

### 3. Multiple Instances
Untuk menjalankan di port berbeda:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## Summary

| Method | Command | Working Dir | Auto-Reload |
|--------|---------|-------------|-------------|
| Run Configuration | (PyCharm) | backend/ | ✅ |
| Terminal | `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | backend/ | ✅ |
| Batch File | `run_backend.bat` | auto | ✅ |

---

## Need Help?

Jika masih mengalami masalah:
1. Cek console output di PyCharm
2. Pastikan semua dependencies terinstall
3. Verifikasi file `.env` ada dan berisi credentials yang benar
4. Cek koneksi jaringan ke perangkat target
