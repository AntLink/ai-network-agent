#!/usr/bin/env python3
"""
Quick configuration check - Versi sederhana menggunakan driver yang sudah ada.

Cara penggunaan:
    cd backend
    python quick_config_check.py

Output:
- Terminal: Ringkasan konfigurasi
- File: configs/quick_check_<timestamp>.txt
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.drivers.cisco import CiscoIOSRouter


# Daftar perangkat
DEVICES = [
    {
        "id": "cisco-iosvl2-sw1",
        "host": "172.22.38.10",
        "console_host": "172.22.37.68",
        "console_port": 5002,
    },
    {
        "id": "cisco-iosvl2-sw2",
        "host": "172.22.38.11",
        "console_host": "172.22.37.68",
        "console_port": 5004,
    },
    {
        "id": "cisco-iosv-r1",
        "host": "172.22.38.12",
        "console_host": "172.22.37.68",
        "console_port": 5006,
    },
    {
        "id": "cisco-iosv-r2",
        "host": "172.22.38.13",
        "console_host": "172.22.37.68",
        "console_port": 5008,
    },
]


def get_device_config(device: dict) -> dict:
    """Get configuration for single device."""
    device_id = device["id"]
    username = os.getenv(f"{device_id.upper()}_USERNAME", "admin")
    password = os.getenv(f"{device_id.upper()}_PASSWORD", "Admin123!")
    secret = os.getenv(f"{device_id.upper()}_SECRET", password)
    
    result = {
        "device_id": device_id,
        "status": "FAILED",
        "error": None,
        "config": None,
        "hostname": None,
        "version": None,
        "interfaces": [],
    }
    
    try:
        print(f"\n[*] Checking {device_id}...")
        
        # Use console transport
        router = CiscoIOSRouter(
            host=device["host"],
            username=username,
            password=password,
            secret=secret,
            device_id=device_id,
        )
        
        # Override to use console
        router._conn._get_connection_params = lambda: {
            "device_type": "cisco_ios",
            "host": device["console_host"],
            "port": device["console_port"],
            "username": username,
            "password": password,
            "secret": secret,
        }
        
        # Connect via console
        router._conn.connect()
        
        # Get configuration
        print(f"  [{device_id}] Getting hostname...")
        hostname = router.get_hostname()
        result["hostname"] = hostname
        
        print(f"  [{device_id}] Getting version...")
        version_info = router.get_version()
        result["version"] = version_info.get("version", "Unknown")[:100]
        
        print(f"  [{device_id}] Getting interfaces...")
        interfaces = router.get_interfaces()
        result["interfaces"] = []
        for intf in interfaces:
            result["interfaces"].append({
                "name": intf.name,
                "ip": str(intf.ip_address) if intf.ip_address else "No IP",
                "status": "UP" if intf.is_up else "DOWN",
            })
        
        print(f"  [{device_id}] Getting full config...")
        config_raw = router._conn.send_show("show running-config", use_textfsm=False)
        result["config"] = config_raw
        
        # Disconnect
        router._conn.disconnect()
        
        result["status"] = "SUCCESS"
        print(f"  [{device_id}] SUCCESS")
        
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = str(e)
        print(f"  [{device_id}] FAILED: {e}")
    
    return result


def main():
    """Main function."""
    print("=" * 80)
    print("  QUICK GNS3 CONFIGURATION CHECK")
    print("=" * 80)
    
    print("\nPerangkat yang diperiksa:")
    for device in DEVICES:
        print(f"  - {device['id']} (console: {device['console_host']}:{device['console_port']})")
    
    print("\n" + "=" * 80)
    
    # Check all devices
    results = []
    for device in DEVICES:
        result = get_device_config(device)
        results.append(result)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"configs/quick_check_{timestamp}.txt"
    os.makedirs("configs", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Configuration Check - {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        for result in results:
            f.write(f"[{result['device_id']}]\n")
            f.write(f"  Status: {result['status']}\n")
            if result['status'] == 'SUCCESS':
                f.write(f"  Hostname: {result['hostname']}\n")
                f.write(f"  Version: {result['version']}\n")
                f.write(f"  Interfaces:\n")
                for intf in result['interfaces']:
                    f.write(f"    - {intf['name']}: {intf['ip']} ({intf['status']})\n")
                f.write(f"\n  Full Config:\n")
                f.write("-" * 80 + "\n")
                f.write(result['config'])
                f.write("\n\n")
            else:
                f.write(f"  Error: {result['error']}\n")
            f.write("\n")
    
    # Print summary
    print("\n" + "=" * 80)
    print("  RINGKASAN KONFIGURASI")
    print("=" * 80)
    
    for result in results:
        print(f"\n  [{result['device_id']}]")
        if result['status'] == 'SUCCESS':
            print(f"    Status: ✓ SUCCESS")
            print(f"    Hostname: {result['hostname']}")
            print(f"    Version: {result['version'][:80]}")
            print(f"    Interfaces: {len(result['interfaces'])}")
            for intf in result['interfaces'][:5]:
                print(f"      - {intf['name']}: {intf['ip']} ({intf['status']})")
        else:
            print(f"    Status: ✗ FAILED")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print(f"  File tersimpan: {filename}")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"\n{success_count}/{len(results)} perangkat berhasil diperiksa")


if __name__ == "__main__":
    main()
