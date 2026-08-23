import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASSWORD = "815m1ll4h"

COMMANDS = [
    ("Check all init scripts for password/shadow references",
     'grep -r "shadow\\|passwd\\|password\\|chpasswd\\|usermod" /etc/init.d/ 2>/dev/null || echo "no matches in init.d"'),
    ("Check rcS.d boot scripts",
     'grep -r "shadow\\|passwd\\|password" /etc/rcS.d/ 2>/dev/null || echo "no matches in rcS.d"'),
    ("Check rc5.d boot scripts",
     'grep -r "shadow\\|passwd\\|password" /etc/rc5.d/ 2>/dev/null || echo "no matches in rc5.d"'),
    ("Check /etc/profile for password reset",
     'cat /etc/profile | grep -i "pass\\|shadow" || echo "no password refs in profile"'),
    ("Check /etc/inittab for password reset",
     'cat /etc/inittab | grep -i "pass\\|shadow" || echo "no password refs in inittab"'),
    ("Check if shadow is being copied from somewhere",
     'find / -name "shadow*" -type f 2>/dev/null | head -20'),
    ("Check /media for shadow backup",
     'find /media -name "shadow*" 2>/dev/null || echo "no shadow in /media"'),
    ("Check /etc/init.d/ for ALL scripts",
     "ls -la /etc/init.d/"),
    ("Check the pass.cgi script",
     "cat /media/httpd/cgi-bin/pass.cgi"),
    ("Check if there's a read-only rootfs remount",
     'grep -r "remount\\|ro," /etc/init.d/ 2>/dev/null | head -10 || echo "no remount found"'),
    ("Check dmesg for rootfs info",
     'dmesg | grep -i "root\\|readonly\\|remount\\|squash" | head -10'),
    ("Root hash in /etc/shadow",
     "grep ^root /etc/shadow"),
    ("Root hash in /etc/shadow- (backup)",
     "grep ^root /etc/shadow-"),
    ("stat /etc/shadow",
     "stat /etc/shadow"),
    ("stat /etc/shadow-",
     "stat /etc/shadow-"),
    ("Kernel cmdline",
     "cat /proc/cmdline"),
    ("All mounts",
     "cat /proc/mounts"),
    ("Block devices",
     "lsblk 2>/dev/null || echo no lsblk"),
    ("Uptime and last reboot",
     "uptime; echo; last reboot | head -5"),
    ("MTD partitions",
     "cat /proc/mtd"),
    ("PID 1 cmdline",
     'cat /proc/1/cmdline | tr "\\0" " "'),
    ("Init scripts in rc5.d",
     "ls -la /etc/rc5.d/"),
    ("S25tcistartup content",
     "cat /etc/rc5.d/S25tcistartup"),
    ("Shadow refs in all boot scripts",
     'grep -rn shadow /etc/rcS.d/ /etc/rc5.d/ /etc/init.d/ 2>/dev/null || echo "none"'),
    ("Check /etc/default/rcS",
     "cat /etc/default/rcS"),
    ("Check volatile config",
     "cat /etc/default/volatiles/00_core"),
    ("Check read-only-rootfs-hook",
     "cat /etc/init.d/read-only-rootfs-hook.sh"),
    ("Root filesystem type info",
     "df -Th /; echo; file -s /dev/mtdblock0 2>/dev/null || echo no file cmd"),
    ("Check if squashfs module loaded",
     "lsmod 2>/dev/null | grep squash || echo squashfs not loaded"),
    ("MTD block header check",
     "dd if=/dev/mtdblock0 bs=64 count=1 2>/dev/null | hexdump -C | head -4"),
    ("checkroot.sh content",
     "cat /etc/init.d/checkroot.sh"),
]


async def main():
    ssh = SSHTransport(HOST, USER, PASSWORD)

    combined = " ; echo '===END_OF_SECTION==='\n".join(cmd for _, cmd in COMMANDS)

    print(f"Connecting to {HOST}...")
    output = await ssh.run(combined)

    sections = output.split("===END_OF_SECTION===")
    for i, (label, _) in enumerate(COMMANDS):
        section = sections[i].strip() if i < len(sections) else "(no output)"
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"{'=' * 70}")
        print(section)


if __name__ == "__main__":
    asyncio.run(main())
