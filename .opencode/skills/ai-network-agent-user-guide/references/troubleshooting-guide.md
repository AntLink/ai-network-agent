# Troubleshooting Guide

Common issues and answers.

## Backend not connected

Check:

```text
http://localhost:8000/api/v1/devices
```

If it fails, restart FastAPI from the backend directory:

```text
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Frontend not connected

Check Vite:

```text
http://localhost:5173
```

## Device not found

Check `/devices`.

Make sure:

- hostname is correct,
- device ID is unique,
- vendor/platform are set,
- management address is reachable.

## Agent gives generic answer

Ask more specifically:

```text
cek interface R1
cek service frigate di ubuntu
jalankan live check docker di ubuntu
tampilkan routing table MK-1
```

## Terminal session not found

Reconnect the terminal session. Backend restarts clear active interactive terminal sessions.

## GNS3 topology not matching

Open `/gns3`, choose the project, then open `/topology-builder?projectId=<project_id>`.

Save the builder layout so `/topology` uses the updated snapshot.

## Service status unclear

For Linux service checks, use:

```text
systemctl status <service> --no-pager
systemctl is-active <service>
ps aux | grep -i '[s]ervice'
ss -tulpen | grep -i <service>
journalctl -u <service> -n 80 --no-pager
```

