# Aruba AOS-CX Troubleshooting

## Interface down

Read-only checks:

```text
show interface brief
show interface <interface>
show running-config interface <interface>
show logging -r
show lldp neighbor-info detail
```

Check:

```text
admin state
link state
speed/duplex
transceiver
VLAN mode
LLDP neighbor
error counters
```

## VLAN issue

Read-only checks:

```text
show vlan
show vlan <id>
show running-config interface <interface>
show mac-address-table
show spanning-tree
```

Check access/trunk mode, native VLAN, allowed VLANs, and STP state.

## Routing issue

Read-only checks:

```text
show ip interface
show ip route
show arp
ping <target>
traceroute <target>
```

For OSPF:

```text
show ip ospf
show ip ospf neighbor
show running-config | include ospf
```

## SSH or management issue

Read-only checks:

```text
show ip interface
show ssh server
show running-config | include ssh
show aaa authentication
show user-group
```

Do not change AAA or SSH settings without explicit approval and console fallback plan.

