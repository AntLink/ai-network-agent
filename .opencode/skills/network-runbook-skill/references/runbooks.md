# Network Runbooks

## Device down

Read-only checks:

```text
inventory health
ping/SSH reachability
management IP
GNS3 node status
console availability
last seen
```

Then:

```text
if GNS3 node stopped -> ask approval to start
if SSH failed but console works -> recommend SSH config check
if management IP missing -> inspect interface/routing
```

## Interface down

Cisco:

```text
show ip interface brief
show interfaces <name>
show running-config interface <name>
show log | include <name>
```

MikroTik:

```text
/interface print detail
/interface ethernet monitor <name> once
/ip address print where interface=<name>
```

Changes such as `no shutdown`, enable interface, or cable/topology changes require approval.

## Routing issue

Checks:

```text
interface state
IP addressing
connected routes
static routes
OSPF/BGP neighbors
next-hop reachability
ARP/neighbor table
ACL/firewall impact
```

Never change routing until current state and impact are shown.

## OSPF neighbor down

Cisco:

```text
show ip ospf neighbor
show ip ospf interface brief
show ip route ospf
show running-config | section router ospf
```

MikroTik:

```text
/routing ospf neighbor print detail
/routing ospf interface-template print detail
/ip route print where ospf
```

Check area, network type, MTU, authentication, passive-interface, and reachability.

## Linux service down

Read-only:

```text
systemctl status <service> --no-pager
systemctl is-active <service>
journalctl -u <service> -n 80 --no-pager
ps aux | grep -i '[s]ervice'
ss -tulpen | grep -i <service>
```

Restart requires approval.

## Docker or Frigate issue

Read-only:

```text
docker ps
docker ps -a
docker logs --tail 100 <container>
docker compose ps
docker compose logs --tail 100
ss -tulpen
df -h
free -m
```

Restarting containers or compose stacks requires approval.

## GNS3 node issue

Read-only:

```text
list projects
get project
list nodes
list links
get node console info
get topology snapshot
```

Start/stop/restart/delete node requires approval.

## Backup before change

Before config changes:

```text
collect running config
store backup artifact
show backup ID
verify backup checksum or non-empty content
```

## Rollback

Rollback requires:

```text
backup ID
target device
config diff
approval
post-check verification
audit record
```

