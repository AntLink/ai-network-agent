#!/usr/bin/env python3
"""
Script untuk mengembalikan konfigurasi perangkat GNS3 ke keadaan semula.

Script ini akan menghapus semua konfigurasi yang telah ditambahkan selama testing
 dan mengembalikan perangkat ke keadaan default (factory reset).

Perangkat yang akan direset:
- cisco-iosvl2-sw1 (172.22.38.10)
- cisco-iosvl2-sw2 (172.22.38.11)
- cisco-iosv-r1 (172.22.38.12)
- cisco-iosv-r2 (172.22.38.13)

Cara penggunaan:
    python backend/restore_gns3_original_config.py

CATATAN: Script ini memerlukan koneksi ke perangkat via console (telnet).
         Pastikan GNS3 VM berjalan dan console ports tersedia.
"""

import sys
import os
import time
import socket
import re
from typing import Optional

sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

# VM GNS3 configuration
GNS3_VM_IP = "172.22.37.68"

# Console ports untuk masing-masing perangkat
CONSOLE_PORTS = {
    "cisco-iosvl2-sw1": 5002,
    "cisco-iosvl2-sw2": 5004,
    "cisco-iosv-r1": 5006,
    "cisco-iosv-r2": 5008,
}

# ESC character for telnet
ESC = chr(27)


def clean_text(txt: str) -> str:
    """Remove ANSI escape codes and control characters."""
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt.strip()


def recv_all(sock: socket.socket, wait: float = 1.5) -> str:
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


def send_cmd(sock: socket.socket, cmd: str, delay: float = 0.05) -> str:
    """Send command and wait for prompt."""
    for ch in cmd:
        sock.send(ch.encode())
        time.sleep(delay)
    sock.send(b"\r")
    time.sleep(0.5)
    return recv_all(sock, 2)


def wait_for_prompt(sock: socket.socket, timeout: float = 10.0) -> str:
    """Wait for router/switch prompt."""
    start = time.time()
    full_output = ""
    while time.time() - start < timeout:
        output = recv_all(sock, 0.5)
        full_output += output
        # Look for common prompts
        if re.search(r"[A-Za-z0-9().-]+[#>]", output):
            return full_output
        if "Password:" in output:
            return full_output
    return full_output


def login_to_console(device_id: str, port: int, username: str = "admin", password: str = "Admin123!") -> Optional[socket.socket]:
    """Login to device console via telnet."""
    try:
        sock = socket.create_connection((GNS3_VM_IP, port), timeout=10)
        sock.settimeout(0.5)
        
        # Wait for initial prompt
        output = wait_for_prompt(sock, 15)
        print(f"  [{device_id}] Connected, initial output: {output[:100]}")
        
        # Send enter to get prompt
        output = send_cmd(sock, "")
        
        # If we see "Press RETURN to get started", send enter
        if "Press RETURN" in output or "--More--" in output:
            output = send_cmd(sock, "")
        
        # Check if we need to login
        if "Username:" in output or "username:" in output:
            print(f"  [{device_id}] Logging in...")
            output = send_cmd(sock, username)
            if "Password:" in output:
                output = send_cmd(sock, password)
        
        # Wait for prompt
        output = wait_for_prompt(sock, 10)
        
        # Enable mode if needed
        if "#" not in output and "#" not in send_cmd(sock, "enable"):
            send_cmd(sock, password)
            wait_for_prompt(sock, 5)
        
        print(f"  [{device_id}] Login successful")
        return sock
        
    except Exception as e:
        print(f"  [{device_id}] ERROR: {e}")
        return None


def erase_startup_config(sock: socket.socket, device_id: str) -> bool:
    """Erase startup-config to reset device."""
    try:
        print(f"  [{device_id}] Erasing startup-config...")
        
        # Disable config confirmation prompts
        send_cmd(sock, "terminal length 0")
        time.sleep(0.5)
        
        # Erase startup-config
        output = send_cmd(sock, "write erase")
        print(f"  [{device_id}] write erase output: {output[:200]}")
        
        # Confirm if needed
        if "confirm" in output.lower() or "?" in output:
            send_cmd(sock, "")  # Send enter to confirm
            time.sleep(1)
        
        # Reload device
        print(f"  [{device_id}] Reloading device...")
        output = send_cmd(sock, "reload")
        
        # If asked to save, say no
        if "save" in output.lower():
            send_cmd(sock, "no")
        
        print(f"  [{device_id}] Device should be reloading...")
        return True
        
    except Exception as e:
        print(f"  [{device_id}] ERROR erasing config: {e}")
        return False


def factory_reset_via_rommon(sock: socket.socket, device_id: str) -> bool:
    """Factory reset via rommon (if device doesn't boot properly)."""
    try:
        print(f"  [{device_id}] Attempting rommon reset...")
        # This would need to be done manually or via console break
        # For now, just document the procedure
        print(f"  [{device_id}] NOTE: Rommon reset requires manual intervention")
        print(f"  [{device_id}]       1. Break boot sequence (Ctrl+Break)")
        print(f"  [{device_id}]       2. confreg 0x2142")
        print(f"  [{device_id}]       3. reset")
        return False
    except Exception as e:
        print(f"  [{device_id}] ERROR: {e}")
        return False


def main():
    """Main function to restore all GNS3 devices."""
    print("=" * 70)
    print("  GNS3 DEVICE CONFIGURATION RESTORE")
    print("  Mengembalikan konfigurasi ke keadaan semula (factory reset)")
    print("=" * 70)
    print()
    
    # Get credentials from environment
    devices = [
        ("cisco-iosvl2-sw1", CONSOLE_PORTS["cisco-iosvl2-sw1"]),
        ("cisco-iosvl2-sw2", CONSOLE_PORTS["cisco-iosvl2-sw2"]),
        ("cisco-iosv-r1", CONSOLE_PORTS["cisco-iosv-r1"]),
        ("cisco-iosv-r2", CONSOLE_PORTS["cisco-iosv-r2"]),
    ]
    
    print("Daftar perangkat yang akan direset:")
    for device_id, port in devices:
        username = os.getenv(f"{device_id.upper()}_USERNAME", "admin")
        password = os.getenv(f"{device_id.upper()}_PASSWORD", "Admin123!")
        print(f"  - {device_id} (console port {port})")
        print(f"    Username: {username}, Password: {'*' * len(password)}")
    print()
    
    print("CATATAN PENTING:")
    print("  1. Pastikan GNS3 VM berjalan (172.22.37.68)")
    print("  2. Perangkat akan di-reload (restart)")
    print("  3. Konfigurasi akan hilang dan kembali ke default")
    print("  4. Anda perlu mengkonfigurasi ulang perangkat setelah ini")
    print()
    
    # Confirm with user
    response = input("Lanjutkan reset? (y/N): ").strip().lower()
    if response != 'y':
        print("Reset dibatalkan.")
        return
    
    print()
    print("Memulai proses reset...")
    print()
    
    # Reset each device
    results = {}
    for device_id, port in devices:
        print(f"[{device_id}]")
        username = os.getenv(f"{device_id.upper()}_USERNAME", "admin")
        password = os.getenv(f"{device_id.upper()}_PASSWORD", "Admin123!")
        
        try:
            sock = login_to_console(device_id, port, username, password)
            if sock:
                success = erase_startup_config(sock, device_id)
                results[device_id] = "SUCCESS" if success else "FAILED"
                sock.close()
            else:
                results[device_id] = "CONNECTION_FAILED"
        except Exception as e:
            print(f"  [{device_id}] ERROR: {e}")
            results[device_id] = "ERROR"
        
        print()
    
    # Print summary
    print("=" * 70)
    print("  RINGKASAN RESET")
    print("=" * 70)
    for device_id, status in results.items():
        print(f"  {device_id}: {status}")
    print()
    
    # Notes for user
    print("Langkah selanjutnya:")
    print("  1. Tunggu semua perangkat selesai reboot")
    print("  2. Login ke masing-masing perangkat")
    print("  3. Lakukan initial configuration:")
    print("     - hostname")
    print("     - enable secret")
    print("     - interface configurations")
    print("     - etc.")
    print()
    print("  Atau jalankan script setup ulang:")
    print("    backend/phase1_recovery.py")
    print("    backend/phase2_verify.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
