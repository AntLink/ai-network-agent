#!/usr/bin/env python3
"""
Script sederhana untuk reset konfigurasi perangkat GNS3 menggunakan driver yang ada.

Script ini akan:
1. Menghapus startup-config (write erase)
2. Reload perangkat
3. Perangkat akan kembali ke konfigurasi default

Perangkat yang akan direset:
- cisco-iosvl2-sw1
- cisco-iosvl2-sw2  
- cisco-iosv-r1
- cisco-iosv-r2

Cara penggunaan:
    cd backend
    python reset_gns3_devices.py

CATATAN:
- Memerlukan console access (bukan SSH)
- Perangkat akan restart
- Semua konfigurasi akan hilang
"""

import sys
import os
import asyncio

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.drivers.cisco.connection import IOSConnection


# Daftar perangkat yang akan direset
DEVICES = [
    {
        "id": "cisco-iosvl2-sw1",
        "management_address": "172.22.38.10",
        "console_host": "172.22.37.68",
        "console_port": 5002,
    },
    {
        "id": "cisco-iosvl2-sw2",
        "management_address": "172.22.38.11",
        "console_host": "172.22.37.68",
        "console_port": 5004,
    },
    {
        "id": "cisco-iosv-r1",
        "management_address": "172.22.38.12",
        "console_host": "172.22.37.68",
        "console_port": 5006,
    },
    {
        "id": "cisco-iosv-r2",
        "management_address": "172.22.38.13",
        "console_host": "172.22.37.68",
        "console_port": 5008,
    },
]


async def reset_device(device: dict) -> bool:
    """Reset single device."""
    device_id = device["id"]
    print(f"\n{'=' * 60}")
    print(f"  Reset: {device_id}")
    print(f"{'=' * 60}")
    
    try:
        # Gunakan console transport
        conn = IOSConnection(device)
        
        # Login via console
        print(f"  Login via console (port {device['console_port']})...")
        try:
            netmiko_conn = conn.connect()
        except Exception as e:
            print(f"  ERROR: Gagal login - {e}")
            return False
        
        print(f"  Login berhasil")
        
        # Disable paging
        print(f"  Disable paging...")
        try:
            netmiko_conn.send_command("terminal length 0")
        except Exception as e:
            print(f"  WARNING: terminal length 0 gagal - {e}")
        
        # Erase startup-config
        print(f"  Menghapus startup-config...")
        try:
            output = netmiko_conn.send_command("write erase")
            print(f"  Output: {output.strip()[:200]}")
            
            # Jika ada confirm prompt, jawab
            if "confirm" in output.lower() or "?" in output:
                netmiko_conn.send_command("")
                print(f"  Confirmed")
        except Exception as e:
            print(f"  WARNING: write erase gagal - {e}")
        
        # Reload perangkat
        print(f"  Reload perangkat...")
        try:
            output = netmiko_conn.send_command("reload", expect_string=r"[yes/no]")
            if "yes/no" in output:
                netmiko_conn.send_command("no")
                print(f"  Reload tanpa save - perangkat akan restart")
            else:
                print(f"  Output: {output.strip()[:200]}")
        except Exception as e:
            print(f"  ERROR: reload gagal - {e}")
            return False
        
        # Disconnect
        conn.disconnect()
        print(f"  Disconnected")
        
        # Tunggu sebentar untuk reload
        print(f"  Menunggu perangkat restart...")
        await asyncio.sleep(5)
        
        print(f"  SUCCESS: {device_id} akan restart dengan konfigurasi default")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("  GNS3 DEVICE RESET UTILITY")
    print("  Reset konfigurasi perangkat ke default")
    print("=" * 60)
    
    print("\nPerangkat yang akan direset:")
    for device in DEVICES:
        print(f"  - {device['id']} (console: {device['console_host']}:{device['console_port']})")
    
    print("\n" + "=" * 60)
    print("  PERINGATAN!")
    print("=" * 60)
    print("  1. Perangkat akan di-reload (restart)")
    print("  2. SEMUA KONFIGURASI AKAN HILANG")
    print("  3. Perangkat akan kembali ke konfigurasi default")
    print("  4. Anda perlu setup ulang Perangkat")
    print()
    
    # Konfirmasi
    response = input("  Lanjutkan reset? (y/N): ").strip().lower()
    if response != 'y':
        print("\n  Reset dibatalkan.")
        return
    
    print()
    
    # Reset semua perangkat
    results = {}
    for device in DEVICES:
        success = await reset_device(device)
        results[device["id"]] = "SUCCESS" if success else "FAILED"
    
    # Summary
    print("\n" + "=" * 60)
    print("  RINGKASAN")
    print("=" * 60)
    for device_id, status in results.items():
        print(f"  {device_id}: {status}")
    
    success_count = sum(1 for s in results.values() if s == "SUCCESS")
    print(f"\n  Total: {success_count}/{len(results)} perangkat berhasil direset")
    
    print("\n" + "=" * 60)
    print("  LANJUTAN")
    print("=" * 60)
    print("  1. Tunggu semua perangkat selesai restart (~2-5 menit)")
    print("  2. Login ke masing-masing perangkat")
    print("  3. Lakukan konfigurasi ulang:")
    print("     - hostname")
    print("     - enable secret")
    print("     - IP addresses")
    print("     - VLANs, trunks, access ports")
    print("     - OSPF")
    print()
    print("  Atau jalankan script setup:")
    print("    python phase1_recovery.py")
    print("    python phase2_verify.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
