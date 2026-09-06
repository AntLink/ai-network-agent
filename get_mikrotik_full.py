#!/usr/bin/env python3
"""
Mengambil Informasi lengkap dari MikroTik Router (MT1)
Dengan handling untuk CLI MikroTik
"""

import paramiko
import time


def run_mikrotik_cmd(shell, cmd, wait=3):
    """Jalankan command pada MikroTik"""
    shell.send(cmd + '\n')
    time.sleep(wait)
    output = ""
    while shell.recv_ready():
        output += shell.recv(65535).decode('utf-8', errors='ignore')
        time.sleep(0.5)
    return output


def test_mikrotik():
    """Eksplorasi konfigurasi MikroTik"""
    print("=" * 50)
    print("🔍 Eksplorasi MikroTik Router (MT1)")
    print("=" * 50)
    
    try:
        # Koneksi SSH
        print("📡 Menghubungkan ke MT1...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname="172.22.134.144",
            port=2203,
            username="admin",
            password="admin",
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        print("✅ Terhubung!")
        
        # Buat shell session
        shell = client.invoke_shell()
        time.sleep(3)
        
        # Test berbagai command
        commands = [
            "/system identity print",
            "/ip address print detail",
            "/ip route print detail",
            "/interface print",
            "/ip route print",
            "/ip address print"
        ]
        
        for cmd in commands:
            print(f"\n📤 Command: {cmd}")
            output = run_mikrotik_cmd(shell, cmd, wait=3)
            print(f"Output:\n{output}")
        
        # Tutup
        shell.close()
        client.close()
        
        print("\n✅ Selesai!")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_mikrotik()