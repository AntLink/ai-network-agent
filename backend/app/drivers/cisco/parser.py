"""Parsers for Cisco IOS show command output.

Converts raw CLI text into structured JSON data for easier frontend consumption.
"""
import re
import ipaddress
from typing import List, Dict, Optional, Any
from .models import Interface, StaticRoute


class IOSParser:
    """Parser for Cisco IOS structured output using TextFSM."""

    @staticmethod
    def parse_interfaces(raw_data: List[Dict]) -> List[Interface]:
        """Convert TextFSM output to list of Interface objects."""
        interfaces = []
        for item in raw_data:
            # Netmiko TextFSM keys for 'show ip interface brief'
            intf_name = item.get("intf") or item.get("interface") or ""
            ip_addr = item.get("ipaddr") or item.get("ip_addr") or item.get("ip_address")
            status = item.get("status", "").lower()
            proto = item.get("proto") or item.get("protocol") or ""
            
            interfaces.append(
                Interface(
                    name=intf_name,
                    ip_address=ip_addr if ip_addr != "unassigned" else None,
                    subnet_mask=None,  # not in brief output
                    description="",
                    is_enabled=status != "administratively down",
                    is_up=status == "up" and proto == "up",
                )
            )
        return interfaces

    @staticmethod
    def parse_static_routes(raw_text: str) -> List[StaticRoute]:
        """Parse plain-text 'show ip route static' output."""
        routes = []
        # S*  0.0.0.0/0 [1/0] via 10.0.0.1   |   S  10.99.0.0 [1/0] via 192.168.200.2
        pat = re.compile(
            r"^\s*S\*?\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?\s+\[\d+/\d+\]\s+via\s+(\S+)",
            re.MULTILINE,
        )
        for net, plen, nh in pat.findall(raw_text or ""):
            if plen is not None:
                mask = str(ipaddress.ip_network(f"0.0.0.0/{plen}").netmask)
            else:
                mask = ""
            routes.append(StaticRoute(destination=net, mask=mask, next_hop=nh))
        return routes

    @staticmethod
    def parse_cpu_memory(cpu_text: str, memory_text: str) -> Dict[str, Any]:
        """Parse CPU and memory output into a UI-friendly JSON shape."""
        result: Dict[str, Any] = {
            "cpu": {
                "summary": "",
                "five_seconds": None,
                "interrupt": None,
                "one_minute": None,
                "five_minutes": None,
            },
            "memory": {
                "pools": [],
                "summary": {},
            },
            "processes": [],
            "warnings": [],
        }

        if cpu_text and "invalid" not in cpu_text.lower() and "autocommand" not in cpu_text.lower():
            cpu_lines = cpu_text.strip().split('\n')
            for line in cpu_lines:
                line = line.strip()
                if not line:
                    continue

                if 'CPU utilization' in line or 'CPU usage' in line:
                    result["cpu"]["summary"] = line
                    m = re.search(
                        r'five seconds:\s*(\d+(?:\.\d+)?)%/?(\d+(?:\.\d+)?)?%;\s*'
                        r'one minute:\s*(\d+(?:\.\d+)?)%;\s*'
                        r'five minutes:\s*(\d+(?:\.\d+)?)%',
                        line,
                        re.IGNORECASE,
                    )
                    if m:
                        result["cpu"]["five_seconds"] = float(m.group(1))
                        result["cpu"]["interrupt"] = float(m.group(2)) if m.group(2) else None
                        result["cpu"]["one_minute"] = float(m.group(3))
                        result["cpu"]["five_minutes"] = float(m.group(4))
                    else:
                        pcts = re.findall(r'(\d+(?:\.\d+)?)%', line)
                        if pcts:
                            result["cpu"]["five_seconds"] = float(pcts[0])
                    continue

                # IOS process rows usually start with PID then runtime fields.
                if re.match(r'^\d+\s+', line):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        process = {
                            "pid": int(parts[0]),
                            "runtime_ms": None,
                            "invoked": None,
                            "usecs": None,
                            "five_sec": None,
                            "one_min": None,
                            "five_min": None,
                            "tty": None,
                            "process": "",
                        }
                        if len(parts) >= 8:
                            process["runtime_ms"] = int(parts[1]) if parts[1].isdigit() else None
                            process["invoked"] = int(parts[2]) if parts[2].isdigit() else None
                            process["usecs"] = int(parts[3]) if parts[3].isdigit() else None
                            process["five_sec"] = parts[4]
                            process["one_min"] = parts[5]
                            process["five_min"] = parts[6]
                            process["tty"] = parts[7]
                            process["process"] = " ".join(parts[8:])
                        else:
                            process["process"] = " ".join(parts[1:])
                        result["processes"].append(process)
        elif cpu_text:
            result["warnings"].append("CPU output could not be parsed")

        if memory_text and "invalid" not in memory_text.lower():
            mem_lines = memory_text.strip().split('\n')

            mem_pool_re = re.compile(
                r'^(Processor|I/O)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
            )
            for line in mem_lines:
                line = line.strip()
                if not line:
                    continue
                m = mem_pool_re.match(line)
                if m:
                    total = int(m.group(3))
                    used = int(m.group(4))
                    free = int(m.group(5))
                    result["memory"]["pools"].append({
                        "pool": m.group(1),
                        "head": m.group(2),
                        "total_bytes": total,
                        "used_bytes": used,
                        "free_bytes": free,
                        "lowest_bytes": int(m.group(6)),
                        "largest_bytes": int(m.group(7)),
                        "used_percent": round((used / total) * 100, 2) if total else None,
                        "free_percent": round((free / total) * 100, 2) if total else None,
                    })
                    continue

                pool_match = re.search(r'Processor.*Total:\s*(\d+),?\s*Used:\s*(\d+),?\s*Free:\s*(\d+)', line, re.IGNORECASE)
                if pool_match:
                    total = int(pool_match.group(1))
                    used = int(pool_match.group(2))
                    free = int(pool_match.group(3))
                    result["memory"]["pools"].append({
                        "pool": "Processor",
                        "head": "",
                        "total_bytes": total,
                        "used_bytes": used,
                        "free_bytes": free,
                        "lowest_bytes": None,
                        "largest_bytes": None,
                        "used_percent": round((used / total) * 100, 2) if total else None,
                        "free_percent": round((free / total) * 100, 2) if total else None,
                    })

            total_memory = sum(pool["total_bytes"] for pool in result["memory"]["pools"] if pool["total_bytes"])
            used_memory = sum(pool["used_bytes"] for pool in result["memory"]["pools"] if pool["used_bytes"])
            free_memory = sum(pool["free_bytes"] for pool in result["memory"]["pools"] if pool["free_bytes"])
            result["memory"]["summary"] = {
                "total_bytes": total_memory,
                "used_bytes": used_memory,
                "free_bytes": free_memory,
                "used_percent": round((used_memory / total_memory) * 100, 2) if total_memory else None,
                "free_percent": round((free_memory / total_memory) * 100, 2) if total_memory else None,
            }
        elif memory_text:
            result["warnings"].append("Memory output could not be parsed")

        return result

    @staticmethod
    def parse_interfaces_brief(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip interface brief' output into list of interface dicts.
        
        Example input:
        Interface          IP-Address      OK? Method Status    Protocol
        GigabitEthernet0/0 192.168.1.1    YES manual up        up
        GigabitEthernet0/1 unassigned    YES unset  administratively down down
        """
        interfaces = []
        if not raw_text:
            return interfaces
        
        lines = raw_text.strip().replace('\r', '').split('\n')
        # Skip header line(s): the column header contains "Interface" + "IP-Address"
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if 'Interface' in line and 'IP-Address' in line and 'OK' in line:
                continue
            # Use regex to handle variable spacing
            # Format: Interface IP-Address OK? Method Status Protocol
            match = re.match(
                r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)$',
                line
            )
            if match:
                name, ip_addr, ok, method, status, protocol = match.groups()
                interfaces.append({
                    "name": name,
                    "ip_address": ip_addr if ip_addr != 'unassigned' else None,
                    "is_ok": ok == 'YES',
                    "method": method,
                    "status": status.strip(),
                    "protocol": protocol
                })
            else:
                # Fallback: split by whitespace
                parts = [p for p in line.split(' ') if p]
                if len(parts) >= 5:
                    interfaces.append({
                        "name": parts[0],
                        "ip_address": parts[1] if parts[1] != 'unassigned' else None,
                        "is_ok": parts[2] == 'YES',
                        "method": parts[3],
                        "status": ' '.join(parts[4:-1]) if len(parts) > 5 else parts[4],
                        "protocol": parts[-1] if len(parts) > 5 else ""
                    })
        return interfaces

    @staticmethod
    def parse_interfaces_detail(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show interfaces' output into list of interface dicts."""
        interfaces = []
        if not raw_text:
            return interfaces
        
        current_if = None
        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Interface header: "GigabitEthernet0/0 is up, line protocol is up"
            if ' is ' in line and not line.startswith(' '):
                if current_if:
                    interfaces.append(current_if)
                parts = line.split(' is ')
                if_name = parts[0]
                status_parts = parts[1].split(', line protocol is ')
                current_if = {
                    "name": if_name,
                    "status": status_parts[0].strip(),
                    "line_protocol": status_parts[1].strip() if len(status_parts) > 1 else "",
                    "hardware": "",
                    "mtu": 0,
                    "input_packets": 0,
                    "output_packets": 0,
                    "input_errors": 0,
                    "output_errors": 0,
                    "drops": 0
                }
            elif current_if and ':' in line:
                # Parse key-value pairs
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip().rstrip('\r')
                    
                    # Extract numeric values
                    if key == "MTU":
                        try:
                            current_if["mtu"] = int(value.split()[0])
                        except:
                            current_if["mtu"] = 0
                    elif key == "Hardware":
                        current_if["hardware"] = value
                    elif "packets input" in key.lower():
                        try:
                            current_if["input_packets"] = int(value.split()[0].replace(',', ''))
                        except:
                            pass
                    elif "packets output" in key.lower():
                        try:
                            current_if["output_packets"] = int(value.split()[0].replace(',', ''))
                        except:
                            pass
                    elif "input errors" in key.lower():
                        try:
                            current_if["input_errors"] = int(value.split()[0].replace(',', ''))
                        except:
                            pass
                    elif "output errors" in key.lower():
                        try:
                            current_if["output_errors"] = int(value.split()[0].replace(',', ''))
                        except:
                            pass
                    elif "drops" in key.lower():
                        try:
                            current_if["drops"] = int(value.split()[0].replace(',', ''))
                        except:
                            pass
        
        if current_if:
            interfaces.append(current_if)
        return interfaces

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip route' output into list of route dicts.

        Handles:
        - Connected:  C        10.0.0.0/24 is directly connected, Loopback0
        - Local:      L        10.0.0.1/32 is directly connected, Loopback0
        - OSPF/static:O        10.255.20.0/30 [110/2] via 10.255.12.2, 11:27:12, Gi0/3
        - Default:    S*       0.0.0.0/0 [1/0] via 10.0.0.1
        """
        routes = []
        if not raw_text:
            return routes

        # Connected / Local: "C  10.0.0.0/24 is directly connected, Gi0/1"
        connected_re = re.compile(
            r'^([A-Za-z]+)\*?\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+is directly connected,?\s*(\S+)'
        )
        # Via routes: "O  10.255.20.0/30 [110/2] via 10.255.12.2, 11:27:12, Gi0/3"
        via_re = re.compile(
            r'^([A-Za-z]+)\*?\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+'
            r'\[(\d+)/(\d+)\]\s+via\s+(\S+),?\s*(.*)$'
        )
        # Via routes without metric: "S  10.0.0.0/8 via 10.0.0.1"
        via_nometric_re = re.compile(
            r'^([A-Za-z]+)\*?\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+via\s+(\S+),?\s*(.*)$'
        )

        for line in raw_text.strip().replace('\r', '').split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('Codes:') or line.startswith('Gateway'):
                continue

            m = connected_re.match(line)
            if m:
                code, network, iface = m.groups()
                routes.append({
                    "code": code,
                    "network": network,
                    "type": "connected",
                    "interface": iface,
                    "next_hop": "-",
                    "distance": 0,
                    "metric": 0,
                })
                continue

            m = via_re.match(line)
            if m:
                code, network, distance, metric, next_hop, rest = m.groups()
                route = {
                    "code": code,
                    "network": network,
                    "type": "static" if code.upper() == 'S' else "dynamic",
                    "next_hop": next_hop.rstrip(','),
                    "distance": int(distance),
                    "metric": int(metric),
                }
                # rest may contain age + interface: "11:27:12, GigabitEthernet0/3"
                if ',' in rest:
                    _, iface = rest.rsplit(',', 1)
                    route["interface"] = iface.strip()
                routes.append(route)
                continue

            m = via_nometric_re.match(line)
            if m:
                code, network, next_hop, rest = m.groups()
                route = {
                    "code": code,
                    "network": network,
                    "type": "static" if code.upper() == 'S' else "dynamic",
                    "next_hop": next_hop.rstrip(','),
                }
                if rest:
                    route["interface"] = rest.strip().rstrip(',')
                routes.append(route)

        return routes

    @staticmethod
    def parse_arp(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip arp' output into list of ARP entries."""
        arp_entries = []
        if not raw_text:
            return arp_entries
        
        lines = raw_text.strip().replace('\r', '').split('\n')
        # Skip header line (column titles)
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if 'Protocol' in line and 'Hardware Addr' in line:
                continue
            
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 5:
                arp_entries.append({
                        "protocol": parts[0],
                        "address": parts[1],
                        "age": parts[2],
                        "mac": parts[3],
                        "type": parts[4],
                        "interface": parts[5] if len(parts) > 5 else ""
                    })
        return arp_entries

    @staticmethod
    def parse_version(raw_text: str) -> Dict[str, Any]:
        """Parse 'show version' output into structured data."""
        info = {}
        if not raw_text:
            return info
        
        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.6(3)M2
            if 'Cisco IOS Software' in line and 'Version' in line:
                version_match = re.search(r'Version\s+(\S+)', line)
                if version_match:
                    info["ios_version"] = version_match.group(1)
                software_match = re.search(r'(\S+)\s+Software', line)
                if software_match:
                    info["software"] = software_match.group(1)
            
            # ROUTER-1 uptime is 1 week, 2 days, 3 hours, 4 minutes
            elif 'uptime is' in line:
                uptime = line.split('uptime is ')[-1]
                info["uptime"] = uptime
            
            # System returned to ROM by reload
            elif 'System returned to ROM by' in line:
                info["last_reload_reason"] = line
            
            # System image file is "flash0:vios-adventerprisek9-m"
            elif 'System image file is' in line:
                image_match = re.search(r'"([^"]+)"', line)
                if image_match:
                    info["image_file"] = image_match.group(1)
            
            # Configuration register is 0x2102
            elif 'Configuration register is' in line:
                reg_match = re.search(r'0x([0-9A-Fa-f]+)', line)
                if reg_match:
                    info["config_register"] = f"0x{reg_match.group(1)}"
            
            # Processor board ID FTX12345678
            elif 'Processor board ID' in line:
                id_match = re.search(r'(\S+)$', line)
                if id_match:
                    info["processor_id"] = id_match.group(1)
            
            # cisco iosv-r1 (revision 1.0) with 401668K/30720K bytes of memory
            elif 'with' in line and 'bytes of memory' in line:
                mem_match = re.search(r'(\d+)K/(\d+)K bytes of memory', line)
                if mem_match:
                    info["memory_total"] = f"{mem_match.group(1)}K"
                    info["memory_used"] = f"{mem_match.group(2)}K"
            
            # 1 GigabitEthernet interface(s)
            elif re.match(r'\d+\s+\w+Ethernet', line):
                interface_match = re.match(r'(\d+)\s+(\w+Ethernet)', line)
                if interface_match:
                    info["interface_count"] = int(interface_match.group(1))
                    info["interface_type"] = interface_match.group(2)
            
            # 256K bytes of non-volatile configuration memory
            elif 'bytes of non-volatile' in line:
                nvram_match = re.search(r'(\d+)K bytes of non-volatile', line)
                if nvram_match:
                    info["nvram_size"] = f"{nvram_match.group(1)}K"
            
            # License Info: ...
            elif 'License Info' in line:
                info["license_info"] = line
        
        return info

    @staticmethod
    def parse_access_lists(raw_text: str) -> Dict[str, Any]:
        """Parse 'show access-lists' output into structured data."""
        acls = {}
        if not raw_text:
            return acls
        
        current_acl = None
        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # ACL header: Standard IP access list 10
            acl_match = re.match(r'(Standard|Extended)\s+IP access list\s+(\S+)', line)
            if acl_match:
                acl_type = acl_match.group(1).lower()
                acl_name = acl_match.group(2)
                current_acl = {
                    "type": acl_type,
                    "name": acl_name,
                    "rules": []
                }
                acls[acl_name] = current_acl
            elif current_acl and line.startswith(' '):
                # ACL rule
                rule_line = line.strip()
                if rule_line and not rule_line.startswith('---'):
                    current_acl["rules"].append(rule_line)
        
        return acls

    @staticmethod
    def parse_cdp_neighbors(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show cdp neighbors detail' output into list of neighbor dicts."""
        neighbors = []
        if not raw_text:
            return neighbors
        
        current_nbr = None
        for line in raw_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Device ID: SW1
            if line.startswith('Device ID:'):
                if current_nbr:
                    neighbors.append(current_nbr)
                current_nbr = {"device_id": line.split(': ')[1]}
            elif current_nbr:
                if line.startswith('Entry address:'):
                    current_nbr["addresses"] = [line.split(': ')[1]]
                elif line.startswith('Platform:'):
                    current_nbr["platform"] = line.split(': ')[1]
                elif line.startswith('Capabilities:'):
                    current_nbr["capabilities"] = line.split(': ')[1]
                elif line.startswith('Interface:'):
                    current_nbr["local_interface"] = line.split(': ')[1].split(',')[0]
                elif line.startswith('Port ID (outgoing port):'):
                    current_nbr["port_id"] = line.split(': ')[1]
                elif line.startswith('Holdtime :'):
                    current_nbr["holdtime"] = line.split(': ')[1]
        
        if current_nbr:
            neighbors.append(current_nbr)
        return neighbors

    @staticmethod
    def parse_nat_translations(raw_text: str) -> Dict[str, Any]:
        """Parse 'show ip nat translation' output into structured data."""
        nat = {"total": 0, "entries": []}
        if not raw_text:
            return nat
        
        for line in raw_text.strip().replace('\r', '').split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if 'Total number of translations' in line:
                total_match = re.search(r'(\d+)', line)
                if total_match:
                    nat["total"] = int(total_match.group(1))
            else:
                # Parse NAT entry: Pro  Inside global      Inside local       Outside local      Outside global
                parts = re.split(r'\s{2,}', line)
                if len(parts) >= 5:
                    entry = {
                        "protocol": parts[0],
                        "inside_global": parts[1],
                        "inside_local": parts[2],
                        "outside_local": parts[3] if len(parts) > 3 else "",
                        "outside_global": parts[4] if len(parts) > 4 else ""
                    }
                    nat["entries"].append(entry)
        
        return nat

    @staticmethod
    def parse_vlans_brief(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show vlan brief' output into list of VLAN dicts.
        
        Example input:
        VLAN Name                             Status    Ports
        ---- -------------------------------- --------- -------------------------------
        1    default                          active    Gi0/1, Gi0/2
        10   VLAN10                          active    Gi0/3
        20   VLAN20                          active    
        """
        vlans = []
        if not raw_text:
            return vlans
        
        lines = raw_text.strip().replace('\r', '').split('\n')
        # Skip header lines (first 2 lines)
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            # Split by 2+ spaces
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 3:
                vlan = {
                    "vlan_id": parts[0].strip(),
                    "name": parts[1].strip(),
                    "status": parts[2].strip(),
                    "ports": parts[3].strip() if len(parts) > 3 else ""
                }
                # Try to convert vlan_id to int
                try:
                    vlan["vlan_id"] = int(vlan["vlan_id"])
                except ValueError:
                    pass
                vlans.append(vlan)
        
        return vlans

    @staticmethod
    def parse_logs(raw_text: str) -> Dict[str, Any]:
        """Parse 'show logging' output into structured data.

        Output shape:
            Syslog logging: enabled (0 messages dropped, 3 messages rate-limited, ...)
            No Active Message Discriminator.
            Console logging: level debugging, 836 messages logged, ...
            Monitor logging: level debugging, 0 messages logged, ...
            Buffer logging:  level debugging, 836 messages logged, ...
            Trap logging:    level informational, ...
        """
        info: Dict[str, Any] = {
            "syslog": {}, "console": {}, "monitor": {}, "buffer": {}, "trap": {},
            "messages": [],
        }
        if not raw_text:
            return info

        in_message_list = False
        for line in raw_text.strip().replace('\r', '').split('\n'):
            line = line.strip()
            if not line:
                continue

            # Match: "<target> logging: <detail>"
            m = re.match(r'^(Syslog|Console|Monitor|Buffer|Trap)\s+logging:\s+(.+)$', line)
            if m:
                target = m.group(1).lower()
                detail = m.group(2)
                info[target] = {
                    "summary": detail,
                    "enabled": 'enabled' in detail,
                    "level": '',
                    "messages": None,
                }
                lvl = re.search(r'level\s+(\S+)', detail)
                if lvl:
                    info[target]["level"] = lvl.group(1)
                msgs = re.search(r'(\d+)\s+messages logged', detail)
                if msgs:
                    info[target]["messages"] = int(msgs.group(1))
                continue

            if 'Active Message Discriminator' in line or 'Inactive Message Discriminator' in line:
                continue

            # Message list starts after buffer logging block; entries often
            # timestamped or sequential numbers
            if line.startswith('Buffer logging') or 'messages logged, xml disabled' in line:
                in_message_list = True
                continue

            if in_message_list and re.match(r'^\d{2}\s', line) or (
                in_message_list and re.match(r'^\S', line)
            ):
                # cap message list to avoid noise
                info["messages"].append(line)
                if len(info["messages"]) > 200:
                    in_message_list = False

        # drop empty message list
        if not info["messages"]:
            info.pop("messages", None)
        return info

    @staticmethod
    def parse_running_config(raw_text: str) -> Dict[str, Any]:
        """Parse IOS running-config into practical JSON sections.

        The raw config remains the source of truth; this parser extracts the
        sections most useful for UI tables and config review.
        """
        result: Dict[str, Any] = {
            "hostname": None,
            "version": None,
            "interfaces": [],
            "vlans": [],
            "routing": {"static_routes": [], "protocols": []},
            "access_lists": [],
            "users": [],
            "line_sections": [],
            "services": [],
            "global": [],
            "sections": [],
        }
        if not raw_text:
            return result

        lines = raw_text.replace('\r', '').splitlines()
        current: Dict[str, Any] | None = None

        def flush_section():
            nonlocal current
            if not current:
                return
            result["sections"].append(current)
            header = current["header"]
            body = current["commands"]

            if header.startswith("interface "):
                name = header.removeprefix("interface ").strip()
                iface: Dict[str, Any] = {
                    "name": name,
                    "description": None,
                    "ip_addresses": [],
                    "switchport_mode": None,
                    "access_vlan": None,
                    "trunk_allowed_vlans": None,
                    "encapsulation": None,
                    "shutdown": False,
                    "commands": body,
                }
                for cmd in body:
                    if cmd.startswith("description "):
                        iface["description"] = cmd.removeprefix("description ").strip()
                    elif cmd.startswith("ip address "):
                        iface["ip_addresses"].append(cmd.removeprefix("ip address ").strip())
                    elif cmd.startswith("switchport mode "):
                        iface["switchport_mode"] = cmd.removeprefix("switchport mode ").strip()
                    elif cmd.startswith("switchport access vlan "):
                        iface["access_vlan"] = cmd.removeprefix("switchport access vlan ").strip()
                    elif cmd.startswith("switchport trunk allowed vlan "):
                        iface["trunk_allowed_vlans"] = cmd.removeprefix("switchport trunk allowed vlan ").strip()
                    elif cmd.startswith("encapsulation "):
                        iface["encapsulation"] = cmd.removeprefix("encapsulation ").strip()
                    elif cmd == "shutdown":
                        iface["shutdown"] = True
                result["interfaces"].append(iface)
            elif header.startswith("vlan "):
                vlan: Dict[str, Any] = {
                    "vlan_id": header.removeprefix("vlan ").strip(),
                    "name": None,
                    "commands": body,
                }
                for cmd in body:
                    if cmd.startswith("name "):
                        vlan["name"] = cmd.removeprefix("name ").strip()
                result["vlans"].append(vlan)
            elif header.startswith("router "):
                result["routing"]["protocols"].append({
                    "name": header,
                    "commands": body,
                })
            elif header.startswith("line "):
                result["line_sections"].append({
                    "name": header,
                    "commands": body,
                })
            current = None

        section_prefixes = ("interface ", "router ", "line ", "vlan ", "ip access-list ")
        skip_prefixes = (
            "Building configuration",
            "Current configuration",
            "!",
            "end",
        )

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                continue
            if any(stripped.startswith(prefix) for prefix in skip_prefixes):
                continue

            if not line.startswith(" ") and stripped.startswith(section_prefixes):
                flush_section()
                current = {"header": stripped, "commands": []}
                continue

            if current and line.startswith(" "):
                current["commands"].append(stripped)
                continue

            flush_section()

            if stripped.startswith("hostname "):
                result["hostname"] = stripped.removeprefix("hostname ").strip()
            elif stripped.startswith("version "):
                result["version"] = stripped.removeprefix("version ").strip()
            elif stripped.startswith("username "):
                parts = stripped.split()
                result["users"].append({
                    "username": parts[1] if len(parts) > 1 else "",
                    "privilege": parts[parts.index("privilege") + 1] if "privilege" in parts and parts.index("privilege") + 1 < len(parts) else None,
                    "has_secret": "secret" in parts,
                    "command": stripped,
                })
            elif stripped.startswith("ip route "):
                result["routing"]["static_routes"].append(stripped)
            elif stripped.startswith("access-list "):
                result["access_lists"].append(stripped)
            elif stripped.startswith(("service ", "no service ", "ip ssh ", "ip domain-", "enable secret", "aaa ")):
                result["services"].append(stripped)
            else:
                result["global"].append(stripped)

        flush_section()

        for vlan in result["vlans"]:
            try:
                vlan["vlan_id"] = int(vlan["vlan_id"])
            except (TypeError, ValueError):
                pass

        return result
