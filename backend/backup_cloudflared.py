import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from app.transports.ssh import SSHTransport
from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 120

BACKUP_SCRIPT = r"""
echo '--- Step 1: Create cloudflared backup folder ---'
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/media/backup/cloudflared"
mkdir -p "$BACKUP_DIR"
echo "TIMESTAMP=$TIMESTAMP"
echo "BACKUP_DIR=$BACKUP_DIR"

echo ''
echo '--- Step 2: Copy cloudflared files ---'
cp /media/httpd/cgi-bin/cloudflared "$BACKUP_DIR/cloudflared-script" && echo "cloudflared-script: OK" || echo "cloudflared-script: FAIL"
cp /media/httpd/cgi-bin/cloudflared-linux-arm "$BACKUP_DIR/cloudflared-linux-arm" && echo "cloudflared-linux-arm: OK" || echo "cloudflared-linux-arm: FAIL"
chmod +x "$BACKUP_DIR/cloudflared-script"
chmod +x "$BACKUP_DIR/cloudflared-linux-arm"

echo ''
echo '--- Step 3: Backup init.d wrapper ---'
cp /etc/init.d/cloudflared "$BACKUP_DIR/cloudflared-initd" && echo "cloudflared-initd: OK" || echo "cloudflared-initd: FAIL"
chmod +x "$BACKUP_DIR/cloudflared-initd"

echo ''
echo '--- Step 4: Create compressed archive ---'
cd /media/backup
tar czf "cloudflared-${TIMESTAMP}.tar.gz" -C cloudflared .
ls -lh "/media/backup/cloudflared-${TIMESTAMP}.tar.gz"

echo ''
echo '--- Step 5: Create restore script ---'
printf '#!/bin/sh\nBACKUP_DIR="/media/backup/cloudflared"\nTARGET_DIR="/media/httpd/cgi-bin"\necho "=== Restoring cloudflared ==="\n/etc/init.d/cloudflared stop 2>/dev/null\nsleep 1\necho "Restoring binary..."\ncp "$BACKUP_DIR/cloudflared-linux-arm" "$TARGET_DIR/cloudflared-linux-arm"\nchmod +x "$TARGET_DIR/cloudflared-linux-arm"\necho "Restoring script..."\ncp "$BACKUP_DIR/cloudflared-script" "$TARGET_DIR/cloudflared"\nchmod +x "$TARGET_DIR/cloudflared"\necho "Restoring init.d..."\ncp "$BACKUP_DIR/cloudflared-initd" /etc/init.d/cloudflared\nchmod +x /etc/init.d/cloudflared\necho "Starting cloudflared..."\n/etc/init.d/cloudflared start\nsleep 3\necho ""\necho "=== Verify ==="\n/etc/init.d/cloudflared status\nps aux | grep cloudflared\necho ""\necho "Restore complete!"\n' > "$BACKUP_DIR/restore.sh"
chmod +x "$BACKUP_DIR/restore.sh"
echo "restore.sh created: OK"

echo ''
echo '--- Step 6: Verify backup ---'
echo "=== Backup directory contents ==="
ls -lah "$BACKUP_DIR/"

echo ''
echo "=== File sizes ==="
ls -l "$BACKUP_DIR/"

echo ''
echo "=== Archive ==="
ls -lh "/media/backup/cloudflared-${TIMESTAMP}.tar.gz"

echo ''
echo "=== Script content (first 5 lines) ==="
head -5 "$BACKUP_DIR/cloudflared-script"
echo "..."

echo ''
echo "=== To restore run: /media/backup/cloudflared/restore.sh ==="
echo '--- DONE ---'
""".strip()


async def main():
    transport = SSHTransport(
        host="192.168.162.20",
        username="root",
        password="815m1ll4h",
    )

    print("=" * 60)
    print("Cloudflared Backup Script")
    print("Target: 192.168.162.20 (root)")
    print("=" * 60)
    print()

    print("[1/1] Connecting and running backup...")
    print("-" * 60)
    try:
        output = await transport.run(BACKUP_SCRIPT)
        print(output)
        print("-" * 60)
        print("SUCCESS: Backup completed.")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
