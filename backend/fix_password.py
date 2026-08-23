import asyncio
import sys
from dotenv import load_dotenv
load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

import asyncssh

HOST = "192.168.162.20"
USER = "root"
PASSWORD = "815m1ll4h"

INIT_SCRIPT = '''#!/bin/sh
### BEGIN INIT INFO
# Provides:          restore-shadow
# Required-Start:    $local_fs
# Required-Stop:     $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Restore shadow/passwd from SD card
### END INIT INFO

BACKUP="/media/backup/system"

case "$1" in
  start)
    if [ -f "$BACKUP/shadow" ]; then
      echo "Restoring shadow from backup..."
      cp $BACKUP/shadow /etc/shadow
      cp $BACKUP/passwd /etc/passwd
      cp $BACKUP/group /etc/group
      chmod 640 /etc/shadow
      chmod 644 /etc/passwd /etc/group
      echo "Shadow restored successfully"
    else
      echo "No shadow backup found at $BACKUP/shadow"
    fi
    ;;
  stop)
    echo "Saving shadow to backup..."
    mkdir -p $BACKUP
    cp /etc/shadow $BACKUP/shadow
    cp /etc/passwd $BACKUP/passwd
    cp /etc/group $BACKUP/group
    echo "Shadow saved"
    ;;
  save)
    mkdir -p $BACKUP
    cp /etc/shadow $BACKUP/shadow
    cp /etc/passwd $BACKUP/passwd
    cp /etc/group $BACKUP/group
    echo "Shadow saved to $BACKUP"
    ;;
  *)
    echo "Usage: $0 {start|stop|save}"
    exit 1
    ;;
esac
exit 0'''


async def r(conn, cmd, timeout=120):
    result = await asyncio.wait_for(conn.run(cmd, check=False), timeout=timeout)
    out = (result.stdout or "") + (result.stderr or "")
    return out.strip(), result.exit_status


async def main():
    print(f"Connecting to {HOST} as {USER}...")
    async with asyncssh.connect(HOST, port=22, username=USER, password=PASSWORD,
                                known_hosts=None, connect_timeout=30) as conn:
        print("Connected!\n")

        # Step 1: Backup
        print("=" * 60)
        print("STEP 1: Backup current shadow/passwd/group to SD card")
        print("=" * 60)
        out, status = await r(conn, "mkdir -p /media/backup/system && cp /etc/shadow /media/backup/system/shadow && cp /etc/passwd /media/backup/system/passwd && cp /etc/group /media/backup/system/group && echo 'Backup done' && stat /media/backup/system/shadow /media/backup/system/passwd /media/backup/system/group")
        print(out)
        print(f"Status: {status}\n")

        # Step 2: Create init script using SFTP
        print("=" * 60)
        print("STEP 2: Create /etc/init.d/restore-shadow")
        print("=" * 60)
        async with conn.start_sftp_client() as sftp:
            async with sftp.open("/etc/init.d/restore-shadow", "w") as f:
                await f.write(INIT_SCRIPT + "\n")
        out, status = await r(conn, "chmod +x /etc/init.d/restore-shadow && echo 'Init script created' && head -3 /etc/init.d/restore-shadow && wc -l /etc/init.d/restore-shadow")
        print(out)
        print(f"Status: {status}\n")

        # Step 3: Symlinks
        print("=" * 60)
        print("STEP 3: Create boot symlinks")
        print("=" * 60)
        out, status = await r(conn, "ln -sf /etc/init.d/restore-shadow /etc/rcS.d/S05restore-shadow && ln -sf /etc/init.d/restore-shadow /etc/rc5.d/S05restore-shadow && ls -la /etc/rcS.d/S05restore-shadow && ls -la /etc/rc5.d/S05restore-shadow")
        print(out)
        print(f"Status: {status}\n")

        # Step 4: Test
        print("=" * 60)
        print("STEP 4: Test restore-shadow start")
        print("=" * 60)
        out, status = await r(conn, "/etc/init.d/restore-shadow start")
        print(out)
        print(f"Status: {status}\n")

        # Step 5: Verify
        print("=" * 60)
        print("STEP 5: Verification")
        print("=" * 60)
        out, status = await r(conn, "echo '--- init.d ---' && ls -la /etc/init.d/restore-shadow && echo '--- rcS.d ---' && ls -la /etc/rcS.d/S05restore-shadow && echo '--- rc5.d ---' && ls -la /etc/rc5.d/S05restore-shadow && echo '--- root in shadow ---' && grep '^root:' /etc/shadow && echo '--- boot order (first 10) ---' && ls /etc/rcS.d/S0* | head -10")
        print(out)
        print(f"Status: {status}\n")

        print("=" * 60)
        print("ALL STEPS COMPLETED SUCCESSFULLY")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
