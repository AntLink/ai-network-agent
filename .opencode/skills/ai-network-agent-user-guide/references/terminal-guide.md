# Terminal Guide

Route:

```text
/terminal
```

The terminal uses backend-managed SSH sessions. The browser does not open SSH directly.

Basic use:

1. Select device.
2. Click connect.
3. Wait for the prompt.
4. Type commands directly in the terminal.
5. Use reconnect if the session expires.

Common commands:

```text
Cisco:
show ip interface brief
show ip route
show version

MikroTik:
/interface print
/ip address print
/ip route print

Linux:
ip addr
ip route
systemctl status frigate --no-pager
docker ps
ss -tulpen
```

Autocomplete:

- Cisco uses `?` style suggestions.
- MikroTik uses `?` style suggestions through backend session suggest.
- Suggestions should come from the connected device/session, not local hardcoded data.

If the terminal says session not found:

- reconnect the device,
- refresh sessions,
- avoid reusing old session IDs after backend restart.

