# Aruba AOS-CX Safety

## Read-only

These are read-only:

```text
show version
show system
show interface brief
show vlan
show ip route
show arp
show lldp neighbor-info
show running-config
show startup-config
show logging -r
ping
traceroute
```

## Approval required

Require approval for:

```text
interface shutdown/no shutdown
VLAN create/delete/change
trunk allowed VLAN changes
IP address changes
static route changes
OSPF/BGP changes
AAA/SSH/user changes
write memory
copy running-config startup-config
firmware or boot changes
reload
```

## High risk

Treat these as high risk:

```text
management interface changes
default route changes
uplink trunk changes
AAA/authentication changes
delete VLAN
reload
erase startup-config
```

## Required workflow for changes

```text
Collect current state
Backup running config
Generate candidate config
Dry run and risk analysis
Approval
Apply
Verify
Save only after verification
Audit
```

