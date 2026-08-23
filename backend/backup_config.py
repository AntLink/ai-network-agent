"""
Backup configuration script for the embedded Linux system at 192.168.162.20.
Creates a timestamped backup of system configs to /media/backup on the SD card.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from app.transports.ssh import SSHTransport

load_dotenv(Path(__file__).parent / ".env")

HOST = "192.168.162.20"
USER = "root"
PASSWORD = "815m1ll4h"

STEP_LABELS = {
    "dirs": "Step 1: Create backup folder on SD card",
    "timestamp": "Step 2: Create timestamped backup directory",
    "backup": "Step 3: Backup all important configs",
    "archive": "Step 4: Create tar.gz archive",
    "list_backups": "Step 5: List available backups and archives",
    "restore_script": "Step 6: Create restore script",
    "summary": "Step 7: Print backup summary",
}


def print_step(label: str, output: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(output.strip())


async def main() -> None:
    transport = SSHTransport(HOST, USER, PASSWORD)

    try:
        # --- Step 1: Create backup directories ---
        out = await transport.run(
            "mkdir -p /media/backup/configs /media/backup/scripts /media/backup/logs && "
            "echo 'Backup directories created' && "
            "ls -la /media/backup/"
        )
        print_step(STEP_LABELS["dirs"], out)

        # --- Step 2: Create timestamped backup directory ---
        out = await transport.run(
            "TIMESTAMP=$(date +%Y%m%d-%H%M%S) && "
            "BACKUP_DIR=/media/backup/configs/$TIMESTAMP && "
            "mkdir -p $BACKUP_DIR && "
            "echo \"TIMESTAMP=$TIMESTAMP\" && "
            "echo \"BACKUP_DIR=$BACKUP_DIR\""
        )
        print_step(STEP_LABELS["timestamp"], out)

        # Parse timestamp from output
        timestamp = ""
        for line in out.strip().splitlines():
            if line.startswith("TIMESTAMP="):
                timestamp = line.split("=", 1)[1].strip()
        if not timestamp:
            print("ERROR: Could not parse timestamp from output")
            sys.exit(1)

        backup_dir = f"/media/backup/configs/{timestamp}"
        print(f"  Using timestamp: {timestamp}")

        # --- Step 3: Backup configs ---
        cmds = [
            # Network configs
            f"cp /etc/hostname {backup_dir}/hostname.txt 2>/dev/null || echo 'no hostname'",
            f"cp /etc/hosts {backup_dir}/hosts.txt 2>/dev/null || echo 'no hosts'",
            f"cp /etc/resolv.conf {backup_dir}/resolv.conf.txt 2>/dev/null || echo 'no resolv.conf'",
            f"cp /etc/network/interfaces {backup_dir}/interfaces.txt 2>/dev/null || echo 'no interfaces'",
            f"cp /etc/fstab {backup_dir}/fstab.txt 2>/dev/null || echo 'no fstab'",
            # System configs
            f"cp /etc/inittab {backup_dir}/inittab.txt 2>/dev/null || echo 'no inittab'",
            f"cp /etc/passwd {backup_dir}/passwd.txt 2>/dev/null || echo 'no passwd'",
            f"cp /etc/group {backup_dir}/group.txt 2>/dev/null || echo 'no group'",
            f"cp /etc/ntp.conf {backup_dir}/ntp.conf.txt 2>/dev/null || echo 'no ntp.conf'",
            f"cp /etc/profile {backup_dir}/profile.txt 2>/dev/null || echo 'no profile'",
            # SSH configs
            f"mkdir -p {backup_dir}/ssh",
            f"cp /etc/ssh/sshd_config {backup_dir}/ssh/sshd_config.txt 2>/dev/null || echo 'no sshd_config'",
            # Init scripts
            f"mkdir -p {backup_dir}/init.d",
            f"cp /etc/init.d/cloudflared {backup_dir}/init.d/cloudflared.txt 2>/dev/null || echo 'no cloudflared init'",
            f"cp /etc/init.d/dns-setup {backup_dir}/init.d/dns-setup.txt 2>/dev/null || echo 'no dns-setup init'",
            # Network scripts
            f"mkdir -p {backup_dir}/network",
            f"cp /etc/network/if-pre-up.d/fix-dns {backup_dir}/network/fix-dns.txt 2>/dev/null || echo 'no fix-dns'",
            # List what was backed up
            f"echo '=== Files in backup directory ===' && ls -laR {backup_dir}/",
        ]
        out = await transport.run(" && ".join(cmds))
        print_step(STEP_LABELS["backup"], out)

        # --- Step 4: Create tar.gz archive ---
        out = await transport.run(
            f"cd /media/backup/configs && "
            f"tar czf /media/backup/configs-{timestamp}.tar.gz {timestamp}/ && "
            f"echo 'Archive created:' && ls -la /media/backup/configs-{timestamp}.tar.gz"
        )
        print_step(STEP_LABELS["archive"], out)

        # --- Step 5: List backups ---
        out = await transport.run(
            "echo '=== Available backup directories ===' && "
            "ls -la /media/backup/configs/ && "
            "echo '' && "
            "echo '=== Backup archives ===' && "
            "ls -la /media/backup/*.tar.gz 2>/dev/null || echo 'no archives'"
        )
        print_step(STEP_LABELS["list_backups"], out)

        # --- Step 6: Create restore script ---
        restore_script = r"""#!/bin/sh
# Restore configuration from backup
# Usage: /media/backup/restore.sh <timestamp>
# Example: /media/backup/restore.sh 20260821-185400

if [ -z "$1" ]; then
    echo "Usage: $0 <timestamp>"
    echo "Available backups:"
    ls /media/backup/configs/
    exit 1
fi

BACKUP_DIR="/media/backup/configs/$1"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup not found: $BACKUP_DIR"
    exit 1
fi

echo "Restoring from: $BACKUP_DIR"

# Restore files
cp $BACKUP_DIR/hostname.txt /etc/hostname 2>/dev/null
cp $BACKUP_DIR/hosts.txt /etc/hosts 2>/dev/null
cp $BACKUP_DIR/resolv.conf.txt /etc/resolv.conf 2>/dev/null
cp $BACKUP_DIR/interfaces.txt /etc/network/interfaces 2>/dev/null
cp $BACKUP_DIR/fstab.txt /etc/fstab 2>/dev/null
cp $BACKUP_DIR/inittab.txt /etc/inittab 2>/dev/null
cp $BACKUP_DIR/passwd.txt /etc/passwd 2>/dev/null
cp $BACKUP_DIR/group.txt /etc/group 2>/dev/null
cp $BACKUP_DIR/ntp.conf.txt /etc/ntp.conf 2>/dev/null
cp $BACKUP_DIR/profile.txt /etc/profile 2>/dev/null

# Restore init scripts
cp $BACKUP_DIR/init.d/cloudflared.txt /etc/init.d/cloudflared 2>/dev/null
chmod +x /etc/init.d/cloudflared 2>/dev/null
cp $BACKUP_DIR/init.d/dns-setup.txt /etc/init.d/dns-setup 2>/dev/null
chmod +x /etc/init.d/dns-setup 2>/dev/null

# Restore network scripts
cp $BACKUP_DIR/network/fix-dns.txt /etc/network/if-pre-up.d/fix-dns 2>/dev/null
chmod +x /etc/network/if-pre-up.d/fix-dns 2>/dev/null

echo "Restore complete! Run: /etc/init.d/cloudflared restart"
"""

        # Write the restore script on the device using a heredoc
        # Escape single quotes in the script for the outer shell
        escaped = restore_script.replace("'", "'\\''")
        out = await transport.run(
            f"cat > /media/backup/restore.sh << 'RESTOREEOF'\n{restore_script}RESTOREEOF\n"
            "chmod +x /media/backup/restore.sh && "
            "echo 'Restore script created and made executable' && "
            "ls -la /media/backup/restore.sh"
        )
        print_step(STEP_LABELS["restore_script"], out)

        # --- Step 7: Summary ---
        out = await transport.run(
            f"echo '=== Backup Summary ===' && "
            f"echo 'Backup folder:   /media/backup/configs/{timestamp}' && "
            f"echo 'Backup archive:  /media/backup/configs-{timestamp}.tar.gz' && "
            f"echo 'Restore script:  /media/backup/restore.sh' && "
            f"echo '' && "
            f"echo 'Files backed up:' && "
            f"ls -la {backup_dir}/"
        )
        print_step(STEP_LABELS["summary"], out)

        print(f"\n{'='*60}")
        print(f"  BACKUP COMPLETE")
        print(f"{'='*60}")
        print(f"  To restore: ssh {USER}@{HOST} '/media/backup/restore.sh {timestamp}'")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
