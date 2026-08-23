import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from app.transports.ssh import SSHTransport

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

HOST = "192.168.162.20"
USER = "root"
PASS = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")

COMMAND_TIMEOUT = 120


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    # Override timeouts by patching the instance
    # SSHTransport uses settings.SSH_COMMAND_TIMEOUT at call time, so we patch settings
    from app.core import config
    config.settings.SSH_COMMAND_TIMEOUT = COMMAND_TIMEOUT

    commands = [
        (
            "Step 1: Create persistent scripts folder on SD card",
            "mkdir -p /media/scripts && "
            "mkdir -p /media/scripts/init.d && "
            "mkdir -p /media/scripts/rcS.d && "
            "mkdir -p /media/scripts/rc5.d",
        ),
        (
            "Step 2: Create restore-shadow script on SD card",
            r"""cat > /media/scripts/init.d/restore-shadow << 'EOF1'
#!/bin/sh
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
      cp $BACKUP/shadow /etc/shadow
      cp $BACKUP/passwd /etc/passwd
      cp $BACKUP/group /etc/group
      chmod 640 /etc/shadow
      chmod 644 /etc/passwd /etc/group
      echo "Shadow restored"
    fi
    ;;
  stop)
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
    echo "Shadow saved"
    ;;
  *)
    echo "Usage: $0 {start|stop|save}"
    exit 1
    ;;
esac
exit 0
EOF1
chmod +x /media/scripts/init.d/restore-shadow""",
        ),
        (
            "Step 3: Create dns-setup script on SD card",
            r"""cat > /media/scripts/init.d/dns-setup << 'EOF2'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          dns-setup
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Setup DNS resolv.conf
### END INIT INFO

RESOLV_FILE="/etc/resolv.conf"

case "$1" in
  start)
    echo "nameserver 1.1.1.1" > $RESOLV_FILE
    echo "nameserver 8.8.8.8" >> $RESOLV_FILE
    echo "nameserver 192.168.162.1" >> $RESOLV_FILE
    echo "DNS configured"
    ;;
  *)
    echo "Usage: $0 start"
    exit 1
    ;;
esac
exit 0
EOF2
chmod +x /media/scripts/init.d/dns-setup""",
        ),
        (
            "Step 4: Create cloudflared script on SD card",
            r"""cat > /media/scripts/init.d/cloudflared << 'EOF3'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          cloudflared
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Cloudflare Tunnel
### END INIT INFO

CLOUDFLARED=/media/httpd/cgi-bin/cloudflared
PIDFILE=/var/run/cloudflared.pid
LOGFILE=/var/volatile/log/cloudflared.log

case "$1" in
  start)
    if [ -x "$CLOUDFLARED" ]; then
      $CLOUDFLARED start
      sleep 2
      echo "Cloudflared started"
    else
      echo "cloudflared not found"
      exit 1
    fi
    ;;
  stop)
    $CLOUDFLARED stop 2>/dev/null
    echo "Cloudflared stopped"
    ;;
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
  status)
    $CLOUDFLARED status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
exit 0
EOF3
chmod +x /media/scripts/init.d/cloudflared""",
        ),
        (
            "Step 5: Create MASTER boot script that copies everything from SD to /etc",
            r"""cat > /media/scripts/init.d/setup-boot << 'MASTEREOF'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          setup-boot
# Required-Start:    $local_fs
# Required-Stop:     $local_fs
# Default-Start:     S
# Default-Stop:
# Short-Description: Copy init scripts from SD card to /etc
### END INIT INFO

SCRIPTS_DIR="/media/scripts/init.d"

case "$1" in
  start)
    echo "=== Setting up boot scripts from SD card ==="

    for script in $SCRIPTS_DIR/*; do
      if [ -f "$script" ]; then
        name=$(basename $script)
        cp $script /etc/init.d/$name
        chmod +x /etc/init.d/$name
        echo "Copied: $name"
      fi
    done

    ln -sf /etc/init.d/restore-shadow /etc/rcS.d/S05restore-shadow
    ln -sf /etc/init.d/restore-shadow /etc/rc5.d/S05restore-shadow
    ln -sf /etc/init.d/dns-setup /etc/rcS.d/S10dns-setup
    ln -sf /etc/init.d/dns-setup /etc/rc5.d/S10dns-setup
    ln -sf /etc/init.d/cloudflared /etc/rcS.d/S99cloudflared
    ln -sf /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared

    echo "Boot scripts installed!"

    /etc/init.d/restore-shadow start
    /etc/init.d/dns-setup start

    echo "=== Boot setup complete ==="
    ;;
  *)
    echo "Usage: $0 start"
    exit 1
    ;;
esac
exit 0
MASTEREOF
chmod +x /media/scripts/init.d/setup-boot""",
        ),
        (
            "Step 6: Create symlink for setup-boot in rcS.d and /etc/init.d",
            "cp /media/scripts/init.d/setup-boot /etc/init.d/setup-boot && "
            "chmod +x /etc/init.d/setup-boot && "
            "ln -sf /etc/init.d/setup-boot /etc/rcS.d/S01setup-boot",
        ),
        (
            "Step 7: Run setup-boot now",
            "/etc/init.d/setup-boot start",
        ),
        (
            "Step 8: Verify everything",
            'echo ""\n'
            'echo "=== Verification ==="\n'
            'echo "DNS:"\n'
            'cat /etc/resolv.conf\n'
            'echo ""\n'
            'echo "Shadow (root line):"\n'
            'grep root /etc/shadow\n'
            'echo ""\n'
            'echo "Init scripts in /etc/init.d/:":\n'
            'ls -la /etc/init.d/restore-shadow /etc/init.d/dns-setup /etc/init.d/cloudflared /etc/init.d/setup-boot 2>/dev/null\n'
            'echo ""\n'
            'echo "Symlinks in rcS.d:"\n'
            'ls -la /etc/rcS.d/S0* /etc/rcS.d/S1* /etc/rcS.d/S9* 2>/dev/null\n'
            'echo ""\n'
            'echo "Symlinks in rc5.d:"\n'
            'ls -la /etc/rc5.d/S0* /etc/rc5.d/S1* /etc/rc5.d/S9* 2>/dev/null\n'
            'echo ""\n'
            'echo "Cloudflared process:"\n'
            'ps aux | grep cloudflared | grep -v grep\n'
            'echo ""\n'
            'echo "Scripts on SD card:"\n'
            'ls -la /media/scripts/init.d/',
        ),
    ]

    for label, cmd in commands:
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"{'=' * 70}")
        try:
            output = await transport.run(cmd)
            print(output if output.strip() else "(no output)")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
