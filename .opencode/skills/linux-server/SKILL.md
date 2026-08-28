---
name: linux-server
description: Knowledge for managing Linux servers (Debian, RHEL, SUSE, Arch).
metadata:
  compatibility: OpenCode
---

# Linux Server

Use standardized tools.

## AI Network Agent Integration

Use this skill when inventory resolves a device as:

```text
vendor=linux
platform=ubuntu | debian | rhel | centos | rocky | alma | suse | arch | embedded
```

Device targets must come from the dynamic inventory behind `/api/v1/devices`; do not hardcode only `ubuntu`, `fauzan`, or `linux-embedded`.

Preferred agent tool namespace:

```text
linux.exec_readonly
linux.exec_guarded
linux.service_status
linux.process_list
linux.port_check
linux.docker_status
linux.file_read
linux.file_patch
linux.restart_service
linux.journalctl
linux.verify_change
```

Evidence rules:

- Clearly separate `backend_snapshot`, `live_command_output`, `generated_plan`, and `dry_run`.
- Do not claim a service/process/port was checked unless the result came from a backend tool or `command_output` event.
- If the current snapshot only has facts/interfaces/routes, say service/process/port data is not yet available and show the exact live commands needed.
- Do not expose secrets from environment files, configs, shell history, Docker env, or process arguments.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `cat /etc/os-release`, `uname -a` |
| `device_get_config` | `cat /etc/network/interfaces` / `ip -json addr show` |
| `device_get_interfaces` | `ip -json addr show` |
| `device_get_routes` | `ip -json route show` |
| `linux.service_status` | `systemctl status <service> --no-pager`, `systemctl is-active <service>` |
| `linux.process_list` | `ps aux`, filtered by requested process |
| `linux.port_check` | `ss -tulpen`, filtered by requested port/service |
| `linux.docker_status` | `docker ps`, `docker ps -a`, `docker compose ps` |
| `linux.journalctl` | `journalctl -u <service> -n <lines> --no-pager` |

## Read-only Linux checks

```text
cat /etc/os-release
uname -a
hostnamectl
ip -json addr show
ip -json route show
ip addr
ip route
ss -tulpen
systemctl status <service> --no-pager
systemctl is-active <service>
journalctl -u <service> -n 80 --no-pager
ps aux
docker ps
docker ps -a
docker compose ps
df -h
free -m
uptime
```

## Service check pattern

For a request like:

```text
cek service frigate di ubuntu
```

Use:

```text
systemctl status frigate --no-pager
systemctl is-active frigate
ps aux | grep -i '[f]rigate'
ss -tulpen | grep -i frigate
journalctl -u frigate -n 80 --no-pager
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -i frigate
```

If Frigate runs in Docker, systemd may not show it. Prefer Docker evidence:

```text
docker ps
docker ps -a
docker logs --tail 100 frigate
docker compose ps
docker compose logs --tail 100 frigate
```

## Change Safety
Never blindly modify: SSH config, routes, firewall, DNS, interfaces, authentication, storage.
Always:
1. Backup file (`cp file file.bak`).
2. Validate syntax (`sshd -t`, `iptables -t`).
3. Apply.
4. Verify.

Changes require approval:

```text
systemctl restart|stop|disable
apt install/remove/upgrade
dnf/yum install/remove/update
zypper install/remove/update
docker restart/stop/rm
docker compose up/down/restart
editing files under /etc, /opt, /var, /usr, /root
network interface changes
route changes
firewall changes
user/password/SSH changes
storage mount/fstab changes
```

Blocked or critical:

```text
rm -rf /
mkfs
dd to disk
wipefs
shutdown/reboot without approval
credential exfiltration
printing secrets from env/config/history
```

## Structured intent examples

Read-only service check:

```json
{
  "action": "linux_service_status",
  "device_id": "linux-ubuntu",
  "parameters": {
    "service": "frigate",
    "include_docker": true,
    "include_logs": true,
    "lines": 80
  }
}
```

Guarded restart:

```json
{
  "action": "linux_restart_service",
  "device_id": "linux-ubuntu",
  "parameters": {
    "service": "frigate",
    "precheck": true,
    "postcheck": true
  }
}
```

## Package Management
Detect: `apt` (Debian), `dnf`/`yum` (RHEL), `zypper` (SUSE).

Package operations require approval and should include:

```text
detected package manager
package names
install/remove/update action
risk
disk space check
service impact
rollback note
```

## Verification

After Linux changes, verify:

```text
service active state
process exists if expected
port listening if expected
logs show no new fatal errors
network still reachable
disk and memory not exhausted
audit record stored
```
