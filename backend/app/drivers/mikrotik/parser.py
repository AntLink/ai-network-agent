"""Parsers for MikroTik RouterOS command output.

Converts raw CLI text into structured JSON data for easier frontend consumption.

RouterOS output has two shapes:
- `/system resource print`, `/system identity print` -> single record, `key: value`
  (colon separator)
- `/interface print detail`, `/ip address print detail`, etc. -> multi-line
  records, `key=value` (equals separator), with optional quoted values and
  leading index/flags.
"""
import re
from typing import List, Dict, Any


class MikroTikParser:
    """Parser for MikroTik RouterOS structured output."""

    @staticmethod
    def _clean_text(raw_text: str) -> str:
        """Clean MikroTik CLI output by removing \\r and normalizing line endings."""
        if not raw_text:
            return ""
        return raw_text.replace('\r\n', '\n').replace('\r', '').strip()

    # ------------------------------------------------------------------
    # Generic record parser (handles `print detail` `key=value` format)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_records(raw_text: str) -> List[Dict[str, Any]]:
        """Parse `print detail without-paging` output into a list of dicts.

        Handles the `key=value` (equals) format used by most `print detail`
        commands, including quoted values and multi-line records:

            Flags: D - DYNAMIC; R - RUNNING
             0   R   name="ether1" default-name="ether1" type="ether" mtu=1500
                     actual-mtu=1500 vrf=main mac-address=0C:01:A4:88:00:00

             1       name="ether2" default-name="ether2" type="ether" mtu=1500
                     actual-mtu=1500 vrf=main mac-address=0C:01:A4:88:00:00
        """
        records: List[Dict[str, Any]] = []
        if not raw_text:
            return records

        lines = MikroTikParser._clean_text(raw_text).split('\n')
        current: Dict[str, Any] | None = None

        for line in lines:
            stripped = line.rstrip()
            if not stripped.strip():
                continue
            if stripped.lstrip().startswith('Flags:') or stripped.lstrip().startswith('Columns:'):
                continue
            # Skip flag-legend continuation lines: "c - CONNECT", "H - HW-OFFLOADED"
            if re.match(r'^\s*[A-Za-z+]\s+-\s+\S', stripped):
                continue

            indent = len(stripped) - len(stripped.lstrip())

            # --- detect record start ---------------------------------
            is_new = False
            record_index = None
            payload = ""

            # Case 1: index-numbered record: " 0   R  address=..."
            m_idx = re.match(r'^\s*(\d+)\s+', stripped)
            if m_idx:
                is_new = True
                record_index = int(m_idx.group(1))
                payload = stripped[m_idx.end():].strip()
            # Case 2: flag-led record without index: "   DAd    dst-address=..."
            # (flags are 1-4 letters, optional trailing '+'; only on shallow indent)
            elif indent <= 5:
                m_flags = re.match(r'^[A-Za-z*;+]{1,4}\s+', stripped.lstrip())
                if m_flags:
                    is_new = True
                    payload = stripped.lstrip()[m_flags.end():].strip()

            if is_new:
                if '=' not in payload:
                    continue  # not a data record (e.g. stray legend line)
                if current is not None:
                    records.append(current)
                current = {"_index": record_index} if record_index is not None else {}
            elif current is not None:
                payload = stripped.strip()
            else:
                continue

            MikroTikParser._ingest_pairs(current, payload)

        if current is not None:
            records.append(current)

        return records

    @staticmethod
    def _ingest_pairs(record: Dict[str, Any], payload: str) -> None:
        """Extract `key=value` pairs; quoted values handled."""
        for m in re.finditer(r'([\w.-]+)=("[^"]*"|\S+)', payload):
            key = m.group(1)
            value = m.group(2)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            record[key] = value

    # ------------------------------------------------------------------
    # Single-record parsers (`key: value` colon format)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_identity(raw_text: str) -> Dict[str, Any]:
        """Parse '/system identity print' output (key: value)."""
        return MikroTikParser._parse_colon_kv(raw_text)

    @staticmethod
    def parse_resource(raw_text: str) -> Dict[str, Any]:
        """Parse '/system resource print' output (key: value)."""
        return MikroTikParser._parse_colon_kv(raw_text)

    @staticmethod
    def _parse_colon_kv(raw_text: str) -> Dict[str, Any]:
        """Generic parser for single-record `key: value` output."""
        info: Dict[str, Any] = {}
        if not raw_text:
            return info

        for line in MikroTikParser._clean_text(raw_text).split('\n'):
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip().rstrip(',').strip()
        return info

    # ------------------------------------------------------------------
    # Command-specific parsers (delegate to generic where possible)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_interfaces(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/interface print detail without-paging' output."""
        return MikroTikParser.parse_records(raw_text)

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip route print detail without-paging' output."""
        return MikroTikParser.parse_records(raw_text)

    @staticmethod
    def parse_ip_addresses(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip address print detail without-paging' output."""
        return MikroTikParser.parse_records(raw_text)

    @staticmethod
    def parse_system_users(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/user print detail without-paging' output."""
        return MikroTikParser.parse_records(raw_text)

    @staticmethod
    def parse_dhcp_server(raw_text: str) -> List[Dict[str, Any]]:
        """Parse '/ip dhcp-server print detail without-paging' output."""
        return MikroTikParser.parse_records(raw_text)

    @staticmethod
    def parse_config(raw_text: str) -> List[str]:
        """Parse '/export terse' output into list of config commands."""
        lines = []
        if not raw_text:
            return lines

        for line in MikroTikParser._clean_text(raw_text).split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        return lines