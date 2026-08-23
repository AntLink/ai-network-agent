import asyncio
import httpx
import json

BASE = "http://127.0.0.1:8000"
CISCO_ID = "cisco-iosv-r1"
MIK_ID = "mikrotik-chr-mk-1"

# GET endpoints (resource reads)
CISCO_GET = [
    "/resources/version",
    "/resources/interfaces",
    "/resources/interfaces-detail",
    "/resources/routes",
    "/resources/arp",
    "/resources/cpu-memory",
    "/resources/acls",
    "/resources/cdp-neighbors",
    "/resources/nat-translations",
    "/resources/logs",
]

MIK_GET = [
    "/resources/ip-addresses",
    "/resources/pools",
    "/resources/dhcp-servers",
    "/resources/dhcp-leases",
    "/resources/bridges",
    "/resources/bridge-ports",
    "/resources/firewall/filter",
    "/resources/firewall/nat",
    "/resources/firewall/mangle",
    "/resources/firewall/address-lists",
    "/resources/ospf",
    "/resources/bgp",
    "/resources/static-routes",
    "/resources/ppp-secrets",
    "/resources/ppp-profiles",
    "/resources/wireless",
    "/resources/wireless-security-profiles",
    "/resources/snmp",
    "/resources/users",
    "/resources/logging",
    "/resources/hotspot/servers",
    "/resources/hotspot/profiles",
    "/resources/hotspot/users",
    "/resources/hotspot/user-profiles",
    "/resources/hotspot/active",
    "/resources/hotspot/hosts",
    "/resources/hotspot/ip-bindings",
    "/resources/hotspot/walled-garden",
    "/resources/ppp-active",
    "/resources/pppoe-servers",
    "/resources/tunnel/l2tp/server",
    "/resources/tunnel/l2tp/clients",
    "/resources/tunnel/pptp/server",
    "/resources/tunnel/pptp/clients",
]

# Safe POST endpoints with minimal payloads
CISCO_POST = {
    "/commands/run": {"commands": ["show clock"]},
    "/tools/ping": {"address": "172.22.37.62", "repeat": 2, "timeout": 2},
    "/tools/traceroute": {"address": "172.22.37.62", "timeout": 2, "probes": 1},
    "/config/backup": {},
    "/config/save": {},
}

MIK_POST = {
    "/commands/run": {"commands": ["/system clock print"]},
    "/tools/ping": {"address": "172.22.45.249", "count": 2},
    "/monitoring": {"metrics": ["cpu", "memory"]},
    "/config/backup": {},
}

async def test_get(client, base, device_id, paths, label):
    results = []
    for p in paths:
        url = f"{base}{p.replace('{device_id}', device_id)}"
        try:
            r = await client.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            size = len(json.dumps(data))
            results.append((p, "OK", size))
        except Exception as e:
            results.append((p, f"FAIL: {e}", 0))
    print(f"\n=== {label} GET ({len([x for x in results if x[1].startswith('OK')])}/{len(results)} OK) ===")
    for p, status, sz in results:
        mark = "[OK]" if status.startswith("OK") else "[FAIL]"
        print(f"  {mark} {p} -> {status} ({sz} bytes)")
    return results

async def test_post(client, base, device_id, mapping, label):
    results = []
    for p, payload in mapping.items():
        url = f"{base}{p.replace('{device_id}', device_id)}"
        try:
            r = await client.post(url, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            size = len(json.dumps(data))
            results.append((p, "OK", size))
        except Exception as e:
            results.append((p, f"FAIL: {e}", 0))
    print(f"\n=== {label} POST ({len([x for x in results if x[1].startswith('OK')])}/{len(results)} OK) ===")
    for p, status, sz in results:
        mark = "[OK]" if status.startswith("OK") else "[FAIL]"
        print(f"  {mark} {p} -> {status} ({sz} bytes)")
    return results

async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        await test_get(client, BASE, CISCO_ID, CISCO_GET, "CISCO")
        await test_get(client, BASE, MIK_ID, MIK_GET, "MIKROTIK")
        await test_post(client, BASE, CISCO_ID, CISCO_POST, "CISCO")
        await test_post(client, BASE, MIK_ID, MIK_POST, "MIKROTIK")

if __name__ == "__main__":
    asyncio.run(main())