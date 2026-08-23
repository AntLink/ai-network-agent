import asyncio
import httpx
import json

BASE = "http://127.0.0.1:8000"
CISCO_ID = "cisco-iosv-r1"
MIK_ID = "mikrotik-chr-mk-1"

CISCO_GET = [
    "/api/v1/cisco/{device_id}/resources/version",
    "/api/v1/cisco/{device_id}/resources/interfaces",
    "/api/v1/cisco/{device_id}/resources/interfaces-detail",
    "/api/v1/cisco/{device_id}/resources/routes",
    "/api/v1/cisco/{device_id}/resources/arp",
    "/api/v1/cisco/{device_id}/resources/cpu-memory",
    "/api/v1/cisco/{device_id}/resources/acls",
    "/api/v1/cisco/{device_id}/resources/cdp-neighbors",
    "/api/v1/cisco/{device_id}/resources/nat-translations",
    "/api/v1/cisco/{device_id}/resources/logs",
]

MIK_GET = [
    "/api/v1/mikrotik/{device_id}/resources/ip-addresses",
    "/api/v1/mikrotik/{device_id}/resources/pools",
    "/api/v1/mikrotik/{device_id}/resources/dhcp-servers",
    "/api/v1/mikrotik/{device_id}/resources/dhcp-leases",
    "/api/v1/mikrotik/{device_id}/resources/bridges",
    "/api/v1/mikrotik/{device_id}/resources/bridge-ports",
    "/api/v1/mikrotik/{device_id}/resources/firewall/filter",
    "/api/v1/mikrotik/{device_id}/resources/firewall/nat",
    "/api/v1/mikrotik/{device_id}/resources/firewall/mangle",
    "/api/v1/mikrotik/{device_id}/resources/firewall/address-lists",
    "/api/v1/mikrotik/{device_id}/resources/ospf",
    "/api/v1/mikrotik/{device_id}/resources/bgp",
    "/api/v1/mikrotik/{device_id}/resources/static-routes",
    "/api/v1/mikrotik/{device_id}/resources/ppp-secrets",
    "/api/v1/mikrotik/{device_id}/resources/ppp-profiles",
    "/api/v1/mikrotik/{device_id}/resources/wireless",
    "/api/v1/mikrotik/{device_id}/resources/wireless-security-profiles",
    "/api/v1/mikrotik/{device_id}/resources/snmp",
    "/api/v1/mikrotik/{device_id}/resources/users",
    "/api/v1/mikrotik/{device_id}/resources/logging",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/servers",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/profiles",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/users",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/user-profiles",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/active",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/hosts",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/ip-bindings",
    "/api/v1/mikrotik/{device_id}/resources/hotspot/walled-garden",
    "/api/v1/mikrotik/{device_id}/resources/ppp-active",
    "/api/v1/mikrotik/{device_id}/resources/pppoe-servers",
    "/api/v1/mikrotik/{device_id}/resources/tunnel/l2tp/server",
    "/api/v1/mikrotik/{device_id}/resources/tunnel/l2tp/clients",
    "/api/v1/mikrotik/{device_id}/resources/tunnel/pptp/server",
    "/api/v1/mikrotik/{device_id}/resources/tunnel/pptp/clients",
]

CISCO_POST = {
    "/api/v1/cisco/{device_id}/commands/run": {"commands": ["show clock"]},
    "/api/v1/cisco/{device_id}/tools/ping": {"address": "172.22.37.62", "repeat": 2, "timeout": 2},
    "/api/v1/cisco/{device_id}/tools/traceroute": {"address": "172.22.37.62", "timeout": 2, "probes": 1},
    "/api/v1/cisco/{device_id}/config/backup": {},
    "/api/v1/cisco/{device_id}/config/save": {},
}

MIK_POST = {
    "/api/v1/mikrotik/{device_id}/commands/run": {"commands": ["/system clock print"]},
    "/api/v1/mikrotik/{device_id}/tools/ping": {"address": "172.22.45.249", "count": 2},
    "/api/v1/mikrotik/{device_id}/monitoring": {"metrics": ["cpu", "memory"]},
    "/api/v1/mikrotik/{device_id}/config/backup": {},
}

async def test_get(client, paths, device_id, label):
    results = []
    for p in paths:
        url = f"{BASE}{p.replace('{device_id}', device_id)}"
        try:
            r = await client.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            size = len(json.dumps(data))
            results.append((p, "OK", size))
        except Exception as e:
            results.append((p, f"FAIL: {e}", 0))
    ok = sum(1 for _, s, _ in results if s.startswith("OK"))
    print(f"\n=== {label} GET ({ok}/{len(results)} OK) ===")
    for p, status, sz in results:
        mark = "[OK]" if status.startswith("OK") else "[FAIL]"
        print(f"  {mark} {p} -> {status} ({sz} bytes)")
    return results

async def test_post(client, mapping, device_id, label):
    results = []
    for p, payload in mapping.items():
        url = f"{BASE}{p.replace('{device_id}', device_id)}"
        try:
            r = await client.post(url, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            size = len(json.dumps(data))
            results.append((p, "OK", size))
        except Exception as e:
            results.append((p, f"FAIL: {e}", 0))
    ok = sum(1 for _, s, _ in results if s.startswith("OK"))
    print(f"\n=== {label} POST ({ok}/{len(results)} OK) ===")
    for p, status, sz in results:
        mark = "[OK]" if status.startswith("OK") else "[FAIL]"
        print(f"  {mark} {p} -> {status} ({sz} bytes)")
    return results

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        await test_get(client, CISCO_GET, CISCO_ID, "CISCO")
        await test_get(client, MIK_GET, MIK_ID, "MIKROTIK")
        await test_post(client, CISCO_POST, CISCO_ID, "CISCO")
        await test_post(client, MIK_POST, MIK_ID, "MIKROTIK")

if __name__ == "__main__":
    asyncio.run(main())