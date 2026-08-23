import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

import asyncssh

CONFIG_BLOCK = r'''
# ============================================================
# === Config auto-restore (2026-08-21)                     ===
# === Pulihkan konfigurasi HANYA JIKA FILE HILANG           ===
# === (tidak menimpa perubahan yang disengaja)              ===
# ============================================================
CFG_BAK="/media/backup/configs"
LATEST_CFG=$(ls -1d "$CFG_BAK"/2* 2>/dev/null | sort | tail -1)

cfg_restore() {
    src="$1"; dst="$2"
    if [ ! -f "$dst" ] && [ -f "$src" ]; then
        cp "$src" "$dst"
        chmod 644 "$dst" 2>/dev/null
        echo "config restored: $dst"
        logger -t cfg-restore "restored $dst"
    fi
}

if [ -n "$LATEST_CFG" ]; then
    cfg_restore "$LATEST_CFG/hostname.txt"   /etc/hostname
    cfg_restore "$LATEST_CFG/hosts.txt"      /etc/hosts
    cfg_restore "$LATEST_CFG/fstab.txt"      /etc/fstab
    cfg_restore "$LATEST_CFG/inittab.txt"    /etc/inittab
    cfg_restore "$LATEST_CFG/passwd.txt"     /etc/passwd
    cfg_restore "$LATEST_CFG/group.txt"      /etc/group
    cfg_restore "$LATEST_CFG/profile.txt"    /etc/profile
    cfg_restore "$LATEST_CFG/interfaces.txt" /etc/network/interfaces
    cfg_restore "$LATEST_CFG/init.d/dns-setup.txt" /etc/init.d/dns-setup
fi

# fix-dns: isi ulang resolv.conf SEBELUM interface naik
# (tanpa ini, DHCP menimpa resolv.conf -> DNS rusak -> tunnel putus)
if [ ! -f /etc/network/if-pre-up.d/fix-dns ]; then
    mkdir -p /etc/network/if-pre-up.d
    printf '#!/bin/sh\n: > /etc/resolv.conf\nfor ns in 1.1.1.1 8.8.8.8 192.168.162.1; do echo "nameserver $ns" >> /etc/resolv.conf; done\n' \
        > /etc/network/if-pre-up.d/fix-dns
    chmod 755 /etc/network/if-pre-up.d/fix-dns
    echo "config restored: /etc/network/if-pre-up.d/fix-dns"
    logger -t cfg-restore "restored fix-dns hook"
fi
# === end config block ===
'''


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)

    async with conn:
        # 1) tarik versi terkini (yang sudah ada blok cloudflared)
        async with conn.start_sftp_client() as sftp:
            await sftp.get("/media/TCI/ifplugdnet.sh",
                           r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\ifplugdnet.sh.v2")
        original = open(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\ifplugdnet.sh.v2",
                        encoding="utf-8", errors="replace").read()

        if "Config auto-restore" in original:
            print("!! blok config sudah ada - batal")
            return

        # 2) sisipkan blok SEBELUM baris 'ifdown -a'
        marker = "ifdown -a"
        idx = original.find(marker)
        if idx == -1:
            print("!! marker ifdown tidak ditemukan")
            return
        new_content = original[:idx] + CONFIG_BLOCK.lstrip("\n") + "\n" + original[idx:]

        local_new = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\ifplugdnet.sh.new2"
        open(local_new, "w", encoding="utf-8", newline="\n").write(new_content)

        # 3) upload + validasi + install
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_new, "/tmp/ifplugdnet_v3.sh")

        cmd = r"""sh -n /tmp/ifplugdnet_v3.sh && echo SYNTAX_OK || { echo SYNTAX_FAIL; exit 1; }
cp -p /media/TCI/ifplugdnet.sh /media/TCI/ifplugdnet.sh.bak2-$(date +%Y%m%d-%H%M)
install -m 755 /tmp/ifplugdnet_v3.sh /media/TCI/ifplugdnet.sh
echo INSTALLED
grep -n -E "Config auto-restore|ifdown|cloudflared auto|S99csmsd" /media/TCI/ifplugdnet.sh"""
        r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=30)
        print(r.stdout)


asyncio.run(main())
