#!/usr/bin/env python3
"""
Script untuk memeriksa konfigurasi SEMUA perangkat GNS3.

Script ini akan:
1. Terhubung ke masing-masing perangkat via console
2. Menjalankan 'show running-config'
3. Menyimpan konfigurasi ke file
4. Menampilkan ringkasan

Perangkat yang akan diperiksa:
- cisco-iosvl2-sw1 (console port 5002)
- cisco-iosvl2-sw2 (console port 5004)
- cisco-iosv-r1 (console port 5006)
- cisco-iosv-r2 (console port 5008)

Cara penggunaan:
    cd backend
    python check_all_gns3_configs.py

Output:
- Terminal: Ringkasan konfigurasi
- File: configs/<device_id>_<timestamp>.txt (full config)
"""

import sys
import os
import time
import socket
import re
from datetime import datetime

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

# VM GNS3 configuration
GNS3_VM_IP = "172.22.37.68"

# Console ports
CONSOLE_PORTS = {
    "cisco-iosvl2-sw1": 5002,
    "cisco-iosvl2-sw2": 5004,
    "cisco-iosv-r1": 5006,
    "cisco-iosv-r2": 5008,
}

# ESC character
ESC = chr(27)

# Output directory
OUTPUT_DIR = "configs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_text(txt: str) -> str:
    """Remove ANSI escape codes and control characters."""
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


def recv_all(sock: socket.socket, wait: float = 2.0) -> str:
    """Receive all data from socket."""
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = sock.recv(65535)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return clean_text(buf.decode(errors="replace"))


def send_cmd(sock: socket.socket, cmd: str, delay: float = 0.02) -> str:
    """Send command character by character."""
    for ch in cmd:
        sock.send(ch.encode())
        time.sleep(delay)
    sock.send(b"\r")
    time.sleep(0.5)
    return recv_all(sock, 3)


def get_full_config(sock: socket.socket, device_id: str) -> str:
    """Get full running-config from device."""
    print(f"  [{device_id}] Getting full configuration...")
    
    # Disable paging
    send_cmd(sock, "terminal length 0")
    time.sleep(0.5)
    
    # Send show running-config
    print(f"  [{device_id}] Sending 'show running-config'...")
    send_cmd(sock, "show running-config")
    
    # Wait and collect output
    full_config = ""
    start_time = time.time()
    while time.time() - start_time < 15:  # Max 15 seconds
        output = recv_all(sock, 1.0)
        if not output:
            break
        full_config += output
        
        # Check if we've reached the end (prompt returned)
        if re.search(r"[A-Za-z0-9().-]+[#>]", output):
            break
    
    return full_config


def extract_key_info(config: str, device_id: str) -> dict:
    """Extract key information from configuration."""
    info = {
        "device_id": device_id,
        "hostname": "Unknown",
        "version": "Unknown",
        "interfaces": [],
        "vlans": [],
        "routes": [],
        "enable_secret": "Unset",
        "username": "None",
    }
    
    try:
        # Extract hostname
        hostname_match = re.search(r"^hostname\s+(\S+)", config, re.M)
        if hostname_match:
            info["hostname"] = hostname_match.group(1)
        
        # Extract version
        version_match = re.search(r"Cisco IOS Software.*Version\s+(\S+)", config)
        if version_match:
            info["version"] = version_match.group(1)
        
        # Extract interfaces with IPs
        interface_matches = re.finditer(
            r"^interface\s+(\S+)\s*\n(.*?)(?=^interface|^router|^line|^!|\Z)",
            config, re.M | re.S
        )
        for match in interface_matches:
            intf_name = match.group(1)
            intf_config = match.group(2)
            
            ip_match = re.search(r"ip address\s+(\S+)\s+(\S+)", intf_config)
            ip = ip_match.group(1) if ip_match else "No IP"
            mask = ip_match.group(2) if ip_match else ""
            
            status = "up" if "no shutdown" in intf_config else "down"
            
            info["interfaces"].append({
                "name": intf_name,
                "ip": ip,
                "mask": mask,
                "status": status,
            })
        
        # Extract VLANs
        vlan_matches = re.finditer(r"^vlan\s+(\d+)\s*\n(.*?)(?=^vlan|^!|\Z)", config, re.M | re.S)
        for match in vlan_matches:
            vlan_id = match.group(1)
            vlan_config = match.group(2)
            name_match = re.search(r"name\s+(\S+)", vlan_config)
            name = name_match.group(1) if name_match else "Unnamed"
            info["vlans"].append({"id": vlan_id, "name": name})
        
        # Extract static routes
        route_matches = re.finditer(
            r"ip route\s+(\S+)\s+(\S+)\s+(\S+)", config
        )
        for match in route_matches:
            info["routes"].append({
                "network": match.group(1),
                "mask": match.group(2),
                "gateway": match.group(3),
            })
        
        # Extract enable secret
        if re.search(r"enable secret\s+\S+", config):
            info["enable_secret"] = "Set"
        
        # Extract local users
        user_matches = re.findall(r"username\s+(\S+)", config)
        if user_matches:
            info["username"] = ", ".join(user_matches[:5])  # First 5 users
        
    except Exception as e:
        print(f"  [{device_id}] Error extracting info: {e}")
    
    return info


def login_and_get_config(device_id: str, port: int) -> dict:
    """Login to device and get configuration."""
    username = os.getenv(f"{device_id.upper()}_USERNAME", "admin")
    password = os.getenv(f"{device_id.upper()}_PASSWORD", "Admin123!")
    
    result = {
        "device_id": device_id,
        "port": port,
        "status": "FAILED",
        "error": None,
        "config": None,
        "info": None,
    }
    
    try:
        print(f"\n[*] Connecting to {device_id} (port {port})...")
        sock = socket.create_connection((GNS3_VM_IP, port), timeout=10)
        sock.settimeout(0.5)
        
        # Wait for initial prompt
        print(f"  [{device_id}] Connected, waiting for prompt...")
        output = recv_all(sock, 3)
        
        # Send enter
        output = send_cmd(sock, "")
        
        # Handle initial boot dialog if present
        if "Press RETURN" in output or "--More--" in output:
            output = send_cmd(sock, "")
        
        # Login if needed
        if "Username:" in output or "username:" in output:
            print(f"  [{device_id}] Logging in as {username}...")
            output = send_cmd(sock, username)
            if "Password:" in output:
                output = send_cmd(sock, password)
            
            # Wait for prompt
            output = recv_all(sock, 2)
        
        # Enter enable mode
        if "#" not in output:
            print(f"  [{device_id}] Entering enable mode...")
            output = send_cmd(sock, "enable")
            if "Password:" in output:
                output = send_cmd(sock, password)
            
            # Wait for enable prompt
            output = recv_all(sock, 2)
        
        # Get full configuration
        full_config = get_full_config(sock, device_id)
        
        # Extract key info
        info = extract_key_info(full_config, device_id)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{OUTPUT_DIR}/{device_id}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<!> Configuration captured at: {datetime.now()}\n")
            f.write(f"<!> Device: {device_id}\n")
            f.write(f"<!> Port: {port}\n")
            f.write("=" * 80 + "\n")
            f.write(full_config)
        
        sock.close()
        
        result["status"] = "SUCCESS"
        result["config"] = full_config
        result["info"] = info
        result["file"] = filename
        
        print(f"  [{device_id}] SUCCESS - Config saved to {filename}")
        
    except Exception as e:
        result["status"] = "FAILED"
        result["error"] = str(e)
        print(f"  [{device_id}] FAILED: {e}")
    
    return result


def print_summary(results: list) -> None:
    """Print summary of all configurations."""
    print("\n" + "=" * 80)
    print("  RINGKASAN KONFIGURASI SEMUA PERANGKAT")
    print("=" * 80)
    
    for result in results:
        if result["status"] != "SUCCESS":
            print(f"\n  [{result['device_id']}]")
            print(f"    Status: {result['status']}")
            print(f"    Error: {result['error']}")
            continue
        
        info = result["info"]
        print(f"\n  [{info['device_id']}]")
        print(f"    Hostname: {info['hostname']}")
        print(f"    Version: {info['version']}")
        print(f"    Enable Secret: {info['enable_secret']}")
        print(f"    Users: {info['username']}")
        
        print(f"    Interfaces ({len(info['interfaces'])}):")
        for intf in info["interfaces"][:5]:  # Show first 5
            print(f"      - {intf['name']}: {intf['ip']}/{intf['mask']} ({intf['status']})")
        if len(info["interfaces"]) > 5:
            print(f"      ... and {len(info['interfaces']) - 5} more")
        
        if info["vlans"]:
            print(f"    VLANs ({len(info['vlans'])}):")
            for vlan in info["vlans"]:
                print(f"      - VLAN {vlan['id']}: {vlan['name']}")
        
        if info["routes"]:
            print(f"    Static Routes ({len(info['routes'])}):")
            for route in info["routes"][:5]:
                print(f"      - {route['network']}/{route['mask']} -> {route['gateway']}")
            if len(info["routes"]) > 5:
                print(f"      ... and {len(info['routes']) - 5} more")
    
    print("\n" + "=" * 80)


def main():
    """Main function."""
    print("=" * 80)
    print("  GNS3 CONFIGURATION CHECKER")
    print("  Memeriksa konfigurasi SEMUA perangkat")
    print("=" * 80)
    
    devices = [
        ("cisco-iosvl2-sw1", CONSOLE_PORTS["cisco-iosvl2-sw1"]),
        ("cisco-iosvl2-sw2", CONSOLE_PORTS["cisco-iosvl2-sw2"]),
        ("cisco-iosv-r1", CONSOLE_PORTS["cisco-iosv-r1"]),
        ("cisco-iosv-r2", CONSOLE_PORTS["cisco-iosv-r2"]),
    ]
    
    print("\nDaftar perangkat:")
    for device_id, port in devices:
        print(f"  - {device_id} (console port {port})")
    
    print("\n" + "=" * 80)
    print("  MEMULAI PEMERIKSAAN")
    print("=" * 80)
    
    # Check all devices
    results = []
    for device_id, port in devices:
        result = login_and_get_config(device_id, port)
        results.append(result)
    
    # Print summary
    print_summary(results)
    
    # Print file locations
    print("\n" + "=" * 80)
    print("  FILE KONFIGURASI TERSIMPAN")
    print("=" * 80)
    for result in results:
        if result["status"] == "SUCCESS" and "file" in result:
            print(f"  {result['device_id']}: {result['file']}")
    print("=" * 80)
    
    # Final message
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    print(f"\nKesimpulan: {success_count}/{len(results)} perangkat berhasil diperiksa")
    
    if success_count == len(results):
        print("✓ SEMUA KONFIGURASI BERHASIL DIPERIKSA")
    else:
        print("✗ Ada perangkat yang gagal diperiksa")


if __name__ == "__main__":
    main()
