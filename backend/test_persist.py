import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")

from app.transports.ssh import SSHTransport

COMMANDS = r"""
echo "===== /proc/mounts =====" && \
cat /proc/mounts && \
echo "" && \
echo "===== df -h =====" && \
df -h && \
echo "" && \
echo "===== mount =====" && \
mount && \
echo "" && \
echo "===== /etc/fstab =====" && \
cat /etc/fstab && \
echo "" && \
echo "===== ls -la /etc/init.d/cloudflared =====" && \
ls -la /etc/init.d/cloudflared && \
echo "" && \
echo "===== /proc/cmdline =====" && \
cat /proc/cmdline && \
echo "" && \
echo "===== dmesg root/squash/jffs/ubi/ubifs/ro =====" && \
dmesg | grep -iE "root|squash|jffs|ubi|ubifs|read-only|ro," | head -20
"""


async def main():
    transport = SSHTransport(
        host="192.168.162.20",
        username="root",
        password="815m1ll4h",
    )

    print("Connecting to 192.168.162.20 ...")
    try:
        output = await transport.run(COMMANDS)
        print(output)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    lines = output.splitlines()

    # 1. What filesystem type is / mounted on?
    root_fs = "UNKNOWN"
    for line in lines:
        if line.strip().startswith("/") and " / " in line:
            parts = line.split()
            root_dev = parts[0]
            root_fstype = parts[2] if len(parts) > 2 else "?"
            root_fs = root_fstype
            print(f"\n1) Root filesystem device: {root_dev}")
            print(f"   Root filesystem type:   {root_fstype}")
            if "squashfs" in root_fstype:
                print("   -> squashfs = READ-ONLY compressed image (cannot write)")
            elif "jffs2" in root_fstype or "ubifs" in root_fstype or "ext4" in root_fstype:
                print(f"   -> {root_fstype} = WRITABLE filesystem")
            else:
                print(f"   -> {root_fstype} (check manually)")
            break

    # 2. Is /etc on the same filesystem or separate?
    etc_same = False
    for line in lines:
        if line.strip().startswith("/") and " /etc " in line:
            etc_dev = line.split()[0]
            print(f"\n2) /etc is a separate mount: {etc_dev}")
            etc_same = False
            break
        if line.strip().startswith("/") and " / " in line:
            # /etc is on root (no separate mount entry for /etc)
            etc_same = True

    if etc_same:
        print(f"\n2) /etc is on the SAME filesystem as / (root)")
        if "squashfs" in root_fs:
            print("   -> /etc is READ-ONLY (part of squashfs image)")
        else:
            print("   -> /etc is writable")

    # 3. Will /etc/init.d/cloudflared survive a reboot?
    print("\n3) Will /etc/init.d/cloudflared survive a reboot?")
    cloudflared_exists = False
    for line in lines:
        if "cloudflared" in line and ("/etc/init.d" in line or "init.d/cloudflared" in line):
            cloudflared_exists = True
            print(f"   Found: {line.strip()}")
            break

    if "squashfs" in root_fs and etc_same:
        if cloudflared_exists:
            print("   -> Present NOW, but rootfs is squashfs (read-only).")
            print("      The init.d script was injected into the squashfs image.")
            print("      It WILL persist only if the squashfs image is not")
            print("      regenerated from the original factory image on update.")
            print("      On a normal reboot (same image), it WILL survive.")
            print("      On a firmware reflash, it will be LOST.")
        else:
            print("   -> NOT FOUND in /etc/init.d/")
            print("      It was never created or was cleaned up.")
    elif etc_same and "squashfs" not in root_fs:
        print("   -> /etc is writable. File will survive reboots.")
    else:
        print("   -> Check /etc mount details above.")


if __name__ == "__main__":
    asyncio.run(main())
