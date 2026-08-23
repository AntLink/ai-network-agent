---
name: ssh-network-device
description: Safe SSH transport rules for network device management.
compatibility: OpenCode
---

# SSH Transport (Security Rules)

SSH is a transport, not a vendor driver. Tools handle the connection.

## Security Rules (Enforced by Tools)
- Prefer SSH keys over passwords.
- Verify host keys/fingerprints.
- Never pass passwords/private keys in command-line arguments.
- Never log authentication material.
- Use connection and command timeouts (`ConnectTimeout=10`, `ServerAliveInterval=60`).
- Limit concurrent sessions (max 5).
- Close sessions cleanly.

## Execution Classes
- READ_ONLY: facts, version, interfaces, routes, VLANs, firewall, services, logs, status.
- CHANGE: configuration commands, service changes, user/authentication changes, routing/firewall changes.

**CHANGE operations require explicit approval from policy engine and operator.**

## Failure Handling
Classify: authentication failure, host-key mismatch, timeout, unreachable, permission denied, command rejected, unexpected prompt, device reboot/disconnect.

Do not blindly retry configuration commands.
