import asyncio

import asyncssh

OUT = open("cf_cfg_diff_out.txt", "w", encoding="utf-8", errors="replace")


async def main():
    conn = await asyncssh.connect(
        "192.168.162.20", username="root", password="815m1ll4h",
        known_hosts=None, connect_timeout=20)
    async with conn:
        cmd = r"""BK=/media/backup/configs/20260820-191015
echo "=== bandingkan backup vs kondisi sekarang ==="
cmp_file() {
  src="$BK/$1"; dst="$2"
  if [ ! -f "$dst" ]; then echo "MISSING  $2"; return; fi
  if ! diff -q "$src" "$dst" >/dev/null 2>&1; then echo "DIFFER   $2"; else echo "SAME     $2"; fi
}
cmp_file hostname.txt        /etc/hostname
cmp_file hosts.txt           /etc/hosts
cmp_file resolv.conf.txt     /etc/resolv.conf
cmp_file interfaces.txt      /etc/network/interfaces
cmp_file fstab.txt           /etc/fstab
cmp_file inittab.txt         /etc/inittab
cmp_file passwd.txt          /etc/passwd
cmp_file group.txt           /etc/group
cmp_file ntp.conf.txt        /etc/ntp.conf
cmp_file profile.txt         /etc/profile
cmp_file init.d/cloudflared.txt /etc/init.d/cloudflared
cmp_file init.d/dns-setup.txt   /etc/init.d/dns-setup
[ -f /etc/network/if-pre-up.d/fix-dns ] && echo "EXISTS   fix-dns" || echo "MISSING  fix-dns"

echo ""
echo "=== isi interfaces sekarang ==="
cat /etc/network/interfaces
echo "=== isi fix-dns (jika ada) ==="
cat /etc/network/if-pre-up.d/fix-dns 2>/dev/null || echo "(tidak ada)"
echo "=== isi dns-setup ==="
head -20 /etc/init.d/dns-setup 2>/dev/null || echo "(tidak ada)"
true"""
        r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=40)
        OUT.write(r.stdout or "")
    OUT.close()
    print("written")


asyncio.run(main())
