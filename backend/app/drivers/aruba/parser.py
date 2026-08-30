"""Parsers for Aruba AOS-CX show command output.

Converts raw AOS-CX CLI text into structured JSON for the UI.
All methods are @staticmethod and must tolerate banners, separators and
missing data (graceful fallback to raw text).
"""
import re
from typing import Any, Dict, List


class ArubaParser:
    """Parser for Aruba AOS-CX structured output."""

    @staticmethod
    def parse_version(raw_text: str) -> Dict[str, Any]:
        """Parse 'show version' output.

        Example:
            ArubaOS-CX
            (c) Copyright Hewlett Packard Enterprise Development LP
            -----------------------------------------------------------------------------
            Version      : Virtual.10.10.1181
            Build Date   :
            Build ID     : ArubaOS-CX:Virtual.10.10.1181:1210b2dbabfa:202608270652
            Build SHA    : 1210b2dbabfa94e271975551dcbc5f9840447274
            Active Image :
        """
        info: Dict[str, Any] = {
            "os": "AOS-CX",
            "version": None,
            "build_id": None,
            "build_sha": None,
            "active_image": None,
        }
        if not raw_text:
            return info
        for line in raw_text.replace("\r", "").splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "version":
                info["version"] = value or None
            elif key == "build id":
                info["build_id"] = value or None
            elif key == "build sha":
                info["build_sha"] = value or None
            elif key == "active image":
                info["active_image"] = value or None
        return info

    @staticmethod
    def parse_system(raw_text: str) -> Dict[str, Any]:
        """Parse 'show system' output.

        Example:
            Hostname               : switch
            System Description     : Virtual.10.10.1181
            Vendor                 : Aruba
            Product Name           : ABC123 ArubaOS-CX_OVA
            Chassis Serial Nbr     : OVAE10F24
            Base MAC Address       : 080009-e10f24
            ArubaOS-CX Version     : Virtual.10.10.1181
            Time Zone              : UTC
            Up Time                : 1 hour, 12 minutes
            CPU Util (%)           : 5
            CPU Util (% avg 1 min) : 5
            CPU Util (% avg 5 min) : 6
            Memory Usage (%)       : 42
        """
        info: Dict[str, Any] = {
            "hostname": None,
            "system_description": None,
            "vendor": None,
            "product_name": None,
            "serial": None,
            "base_mac": None,
            "version": None,
            "time_zone": None,
            "uptime": None,
            "cpu_util": None,
            "cpu_util_1min": None,
            "cpu_util_5min": None,
            "memory_usage": None,
        }
        if not raw_text:
            return info
        mapping = {
            "hostname": "hostname",
            "system description": "system_description",
            "vendor": "vendor",
            "product name": "product_name",
            "chassis serial nbr": "serial",
            "base mac address": "base_mac",
            "arubaos-cx version": "version",
            "time zone": "time_zone",
            "up time": "uptime",
        }
        for line in raw_text.replace("\r", "").splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key_norm = key.strip().lower()
            value = value.strip()
            if key_norm in mapping:
                info[mapping[key_norm]] = value or None
                continue
            m = re.match(r"cpu util\s*\(?\s*%\s*(?:\()?(?:avg\s+(\d+)\s*min)?", key_norm)
            if m:
                if m.group(1) == "1":
                    info["cpu_util_1min"] = ArubaParser._to_int(value)
                elif m.group(1) == "5":
                    info["cpu_util_5min"] = ArubaParser._to_int(value)
                else:
                    info["cpu_util"] = ArubaParser._to_int(value)
                continue
            if "memory usage" in key_norm:
                info["memory_usage"] = ArubaParser._to_int(value)
        return info

    @staticmethod
    def _to_int(value: str):
        m = re.search(r"\d+", value or "")
        return int(m.group(0)) if m else None

    @staticmethod
    def parse_facts(version_raw: str, system_raw: str) -> Dict[str, Any]:
        """Merge show version + show system into one facts dict."""
        facts = ArubaParser.parse_system(system_raw)
        ver = ArubaParser.parse_version(version_raw)
        facts.update({k: v for k, v in ver.items() if v is not None})
        facts.setdefault("vendor", "Aruba")
        facts.setdefault("platform", "AOS-CX")
        return facts

    @staticmethod
    def parse_interfaces_brief(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show interface brief' output.

        Header columns: Port | Native VLAN | Mode | Type | Enabled |
        Status | Reason | Speed | Description
        """
        interfaces: List[Dict[str, Any]] = []
        if not raw_text:
            return interfaces
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lowered = line.lower()
            if stripped.split(maxsplit=1)[0].lower() == "port":
                continue  # header ("Port Native Mode Type Enabled Status Reason ...")
            if re.fullmatch(r"[- ]+", stripped):
                continue  # separator
            cols = re.split(r"\s{2,}", stripped)
            if len(cols) < 6:
                continue
            # AOS-CX pads "Mode" and "Type" with ONE space between them, so
            # the tokenizer merges them into cols[2] (e.g. "routed --").
            mode_type = cols[2].split(" ", 1)
            iface: Dict[str, Any] = {
                "name": cols[0],
                "native_vlan": cols[1],
                "mode": mode_type[0],
                "type": mode_type[1] if len(mode_type) > 1 else "",
                "enabled": (cols[3].lower() in ("yes", "up", "true")),
                "admin": cols[3],
                "status": cols[4],
                "reason": cols[5] if len(cols) > 5 else "",
                "speed": cols[6] if len(cols) > 6 else "",
                "description": " ".join(cols[7:]) if len(cols) > 7 else "",
            }
            interfaces.append(iface)
        return interfaces

    @staticmethod
    def parse_ip_interfaces(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip interface' output (one block per interface).

        Example block:
            Interface 1/1/1 is down (Administratively down)
             Admin state is down
             State information: Administratively down
             Hardware: Ethernet, MAC Address: 08:00:09:e1:0f:24
             IP MTU 1500
             Encapsulation dot1q ID:
             No IPv4 address configured
        """
        blocks: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            m = re.match(r"^Interface\s+(\S+)\s+is\s+(up|down)(?:\s*\((.*?)\))?\s*$", stripped)
            if m:
                if current:
                    blocks.append(current)
                current = {
                    "name": m.group(1),
                    "status": m.group(2),
                    "oper_state": m.group(3) or "",
                    "admin_state": None,
                    "ip_address": None,
                    "mtu": None,
                    "mac_address": None,
                    "vrf": "",
                }
                continue
            if current is None:
                continue
            low = stripped.lower()
            if low.startswith("admin state is"):
                current["admin_state"] = stripped.split(" is ", 1)[-1].strip()
            elif "mtu" in low and ":" in stripped:
                val = stripped.split(":", 1)[-1].strip()
                m2 = re.search(r"\d+", val)
                current["mtu"] = int(m2.group(0)) if m2 else None
            elif "mac address" in low:
                m3 = re.search(r"[0-9a-fA-F:.-]{8,}", stripped)
                if m3:
                    current["mac_address"] = m3.group(0)
            elif low.startswith("ipv4 address") and "no ipv4" not in low:
                current["ip_address"] = stripped.split("address", 1)[-1].strip()
            elif re.search(r"vrf\b", low) and ":" in stripped:
                current["vrf"] = stripped.split(":", 1)[-1].strip()
            elif "no ipv4 address" in low and "vrf" not in low:
                current["ip_address"] = None
        if current:
            blocks.append(current)
        return blocks

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip route' output (best effort, AOS-CX format).

        Handles connected (directly connected) and via (next-hop) forms.
        """
        routes: List[Dict[str, Any]] = []
        if not raw_text:
            return routes
        connected_re = re.compile(
            r"^\s*([A-Za-z*]+)\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+is directly connected,?\s*(\S+)"
        )
        via_re = re.compile(
            r"^\s*([A-Za-z*]+)\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+(?:\[(\d+)/(\d+)\] )?via\s+(\S+),?\s*(.*)$"
        )
        # AOS-CX tabular form: "S*  0.0.0.0/0  192.168.1.254  1/1/1  0  1  -"
        tabular_re = re.compile(
            r"^\s*([A-Za-z*]+)\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+"
            r"(\d+\.\d+\.\d+\.\d+)\s+(\S+)\s+(\d+)\s+(\d+)"
        )
        for line in raw_text.replace("\r", "").splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"(?i)(displaying|state|codes|gateway|via)", line):
                continue
            m = connected_re.match(line)
            if m:
                code, network, iface = m.groups()
                routes.append({
                    "code": code.replace("*", ""),
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
                    "code": code.replace("*", ""),
                    "network": network,
                    "type": "static" if "s" in code.lower() else "dynamic",
                    "next_hop": next_hop.rstrip(","),
                    "distance": int(distance) if distance else None,
                    "metric": int(metric) if metric else None,
                }
                if rest:
                    route["interface"] = rest.strip().rstrip(",")
                routes.append(route)
                continue
            m = tabular_re.match(line)
            if m:
                code, network, next_hop, iface, metric, distance = m.groups()
                routes.append({
                    "code": code.replace("*", ""),
                    "network": network,
                    "type": "connected" if code.upper() == "C" else "static" if "s" in code.lower() else "dynamic",
                    "next_hop": next_hop.rstrip(","),
                    "interface": iface,
                    "distance": int(distance),
                    "metric": int(metric),
                })
        return routes

    @staticmethod
    def parse_vlans(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show vlan' output.

        Example:
            VLAN  Name           Status  Reason          Type     Interfaces
            1     DEFAULT_VLAN_1 down    no_member_port  default
        """
        vlans: List[Dict[str, Any]] = []
        if not raw_text:
            return vlans
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = line.lower()
            if ("vlan" in low and "name" in low and "status" in low) or re.fullmatch(r"[- ]+", stripped):
                continue
            if not re.match(r"^\d+\s", stripped):
                continue
            cols = re.split(r"\s{2,}", stripped)
            if len(cols) < 4:
                continue
            vlan: Dict[str, Any] = {
                "vlan_id": int(cols[0]),
                "name": cols[1],
                "status": cols[2],
                "reason": cols[3],
                "type": cols[4] if len(cols) > 4 else "",
                "interfaces": " ".join(cols[5:]) if len(cols) > 5 else "",
            }
            vlans.append(vlan)
        return vlans

    @staticmethod
    def parse_arp(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show arp' output (best effort).

        AOS-CX header: IPv4 Address   MAC Address    Type     Interface
        """
        entries: List[Dict[str, Any]] = []
        if not raw_text:
            return entries
        if "no arp entries" in raw_text.lower():
            return entries
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = line.lower()
            if ("ipv4" in low and "mac" in low and "type" in low) or re.fullmatch(r"[- ]+", stripped):
                continue
            m = re.match(
                r"^(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F.:-]+)\s+(\S+)\s+(\S+)\s*$", stripped
            )
            if m:
                entries.append({
                    "address": m.group(1),
                    "mac": m.group(2),
                    "type": m.group(3),
                    "interface": m.group(4),
                })
        return entries

    @staticmethod
    def parse_running_config(raw_text: str) -> Dict[str, Any]:
        """Parse AOS-CX running-config into practical JSON sections."""
        result: Dict[str, Any] = {
            "hostname": None,
            "version": None,
            "interfaces": [],
            "vlans": [],
            "routing": {"static_routes": [], "protocols": []},
            "users": [],
            "global": [],
            "sections": [],
        }
        if not raw_text:
            return result
        lines = raw_text.replace("\r", "").splitlines()
        current: Dict[str, Any] | None = None
        header_re = re.compile(r"^(interface|vlan|router|ip route|user|username)\b")

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
                    "mode": None,
                    "vlan_access": None,
                    "vlan_trunk": None,
                    "shutdown": False,
                    "commands": body,
                }
                for cmd in body:
                    if cmd.startswith("description "):
                        iface["description"] = cmd.removeprefix("description ").strip()
                    elif cmd.startswith("ip address "):
                        iface["ip_addresses"].append(cmd.removeprefix("ip address ").strip())
                    elif cmd.startswith("vlan access "):
                        iface["vlan_access"] = cmd.removeprefix("vlan access ").strip()
                    elif cmd.startswith("vlan trunk allowed "):
                        iface["vlan_trunk"] = cmd.removeprefix("vlan trunk allowed ").strip()
                    elif cmd.startswith("no shutdown"):
                        iface["shutdown"] = False
                    elif cmd == "shutdown":
                        iface["shutdown"] = True
                    elif cmd.startswith("routing "):
                        iface["mode"] = cmd.removeprefix("routing ").strip()
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
                result["routing"]["protocols"].append({"name": header, "commands": body})
            elif header.startswith("ip route "):
                result["routing"]["static_routes"].append(header + (" " + " ".join(body) if body else ""))
            elif header.startswith(("user", "username")):
                result["users"].append({"command": header})
            current = None

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped or stripped in ("!", "end") or stripped.startswith("startup-config snapshot"):
                continue
            if raw_line.startswith(" ") and current is not None:
                current["commands"].append(stripped)
                continue
            flush_section()
            if header_re.match(stripped):
                current = {"header": stripped, "commands": []}
                continue
            if stripped.startswith("hostname "):
                result["hostname"] = stripped.removeprefix("hostname ").strip()
            elif stripped.startswith(("!","vlan 1")):
                pass
            else:
                result["global"].append(stripped)

        flush_section()

        for vlan in result["vlans"]:
            try:
                vlan["vlan_id"] = int(vlan["vlan_id"])
            except (TypeError, ValueError):
                pass
        return result