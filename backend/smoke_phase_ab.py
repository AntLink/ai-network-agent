"""Smoke test Phase A+B against the live GNS3 lab."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import os

os.environ.setdefault("CISCO_IOSV_R1_PASSWORD", "Admin123!")
os.environ.setdefault("CISCO_IOSV_R1_SECRET", "Admin123!")

from app.services.device_service import device_service


async def main():
    print("=== 1. console_exec R1 (full telnet dialog) ===")
    res = await device_service.console_exec("cisco-iosv-r1", "show ip interface brief")
    lines = [l for l in res["output"].splitlines() if l.strip()][:8]
    print("\n".join(lines))

    print()
    print("=== 2. health R1 (flash sanity) ===")
    h = await device_service.health("cisco-iosv-r1")
    for k in ("reachable", "ssh_banner", "flash_size", "flash_ok", "flash_broken_hint"):
        print(f"   {k}: {h.get(k)}")

    print()
    print("=== 3. save_config verification R1 ===")
    drv = __import__("app.drivers.factory", fromlist=["get_driver"]).get_driver(
        {"id": "cisco-iosv-r1", "management_address": "172.22.45.249",
         "vendor": "cisco", "console_host": "172.22.37.68", "console_port": 5006}
    )
    s = await drv.save_config()
    print(f"   saved={s['saved']} verified={s.get('verified')} host={s.get('hostname')}")


asyncio.run(main())
