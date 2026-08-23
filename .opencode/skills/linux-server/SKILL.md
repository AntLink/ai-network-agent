---
name: linux-server
description: Knowledge for managing Linux servers (Debian, RHEL, SUSE, Arch).
compatibility: OpenCode
---

# Linux Server

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `cat /etc/os-release`, `uname -a` |
| `device_get_config` | `cat /etc/network/interfaces` / `ip -json addr show` |
| `device_get_interfaces` | `ip -json addr show` |
| `device_get_routes` | `ip -json route show` |

## Change Safety
Never blindly modify: SSH config, routes, firewall, DNS, interfaces, authentication, storage.
Always:
1. Backup file (`cp file file.bak`).
2. Validate syntax (`sshd -t`, `iptables -t`).
3. Apply.
4. Verify.

## Package Management
Detect: `apt` (Debian), `dnf`/`yum` (RHEL), `zypper` (SUSE).
