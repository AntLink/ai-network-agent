import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

LOCAL_BACKUP = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\ifplugdnet.sh.orig"

CLOUDFLARED_BLOCK = r'''
# ============================================================
# === Cloudflared auto-restore & auto-start (2026-08-21)  ===
# === Pastikan tunnel Cloudflare selalu jalan setelah      ===
# === restart: restore dari /media/backup bila file hilang ===
# ============================================================
CF_BAK="/media/backup/cloudflared"
CF_DIR="/media/httpd/cgi-bin"
CF_RESTORED=0

if [ ! -x "$CF_DIR/cloudflared-linux-arm" ] && [ -f "$CF_BAK/cloudflared-linux-arm" ]; then
    cp "$CF_BAK/cloudflared-linux-arm" "$CF_DIR/cloudflared-linux-arm" \
        && chmod +x "$CF_DIR/cloudflared-linux-arm" && CF_RESTORED=1
fi
if [ ! -f "$CF_DIR/cloudflared" ] && [ -f "$CF_BAK/cloudflared-script" ]; then
    cp "$CF_BAK/cloudflared-script" "$CF_DIR/cloudflared" \
        && chmod +x "$CF_DIR/cloudflared" && CF_RESTORED=1
fi
if [ ! -f "/etc/init.d/cloudflared" ] && [ -f "$CF_BAK/cloudflared-initd" ]; then
    cp "$CF_BAK/cloudflared-initd" /etc/init.d/cloudflared \
        && chmod +x /etc/init.d/cloudflared && CF_RESTORED=1
fi
if [ ! -e /etc/rc5.d/S99cloudflared ] && [ -f /etc/init.d/cloudflared ]; then
    ln -sf /etc/init.d/cloudflared /etc/rc5.d/S99cloudflared
    CF_RESTORED=1
fi
if [ "$CF_RESTORED" = "1" ]; then
    echo "cloudflared: restored missing files from backup"
    logger -t cf-restore "cloudflared files restored from /media/backup"
fi

# start tunnel jika belum berjalan
sleep 2
if ! pidof cloudflared-linux-arm >/dev/null 2>&1; then
    /etc/rc5.d/S99cloudflared start
    echo "cloudflared: started"
    logger -t cf-restore "cloudflared started"
else
    echo "cloudflared: already running (pid $(pidof cloudflared-linux-arm))"
fi
# === end cloudflared block ===
'''


async def main():
    import asyncssh

    conn = await asyncssh.connect(
        "192.168.162.20",
        username="root",
        password="815m1ll4h",
        known_hosts=None,
        connect_timeout=20,
    )

    async with conn:
        # backup lokal
        async with conn.start_sftp_client() as sftp:
            await sftp.get("/media/TCI/ifplugdnet.sh", LOCAL_BACKUP)
        print(f"[1] backup lokal: {LOCAL_BACKUP}")

        original = open(LOCAL_BACKUP, "r", encoding="utf-8", errors="replace").read()
        if "Cloudflared auto-restore" in original:
            print("!! blok sudah ada di file - tidak menambah lagi")
            return

        new_content = original.rstrip("\n") + "\n" + CLOUDFLARED_BLOCK
        local_new = LOCAL_BACKUP.replace(".orig", ".new")
        open(local_new, "w", encoding="utf-8", newline="\n").write(new_content)

        # 2) upload sebagai .new
        async with conn.start_sftp_client() as sftp:
            await sftp.put(local_new, "/tmp/ifplugdnet.sh.new")
        print("[2] uploaded /tmp/ifplugdnet.sh.new")

        # 3) validasi sintaks + install dengan backup di device
        cmd = r"""sh -n /tmp/ifplugdnet.sh.new && echo SYNTAX_OK || { echo SYNTAX_FAIL; exit 1; }
cp -p /media/TCI/ifplugdnet.sh /media/TCI/ifplugdnet.sh.bak-$(date +%Y%m%d)
install -m 755 /tmp/ifplugdnet.sh.new /media/TCI/ifplugdnet.sh
echo INSTALLED
tail -5 /media/TCI/ifplugdnet.sh
ls -la /media/TCI/ifplugdnet.sh*"""
        r = await asyncio.wait_for(conn.run(cmd, check=False), timeout=30)
        print(f"[3] install:\n{r.stdout}")

    print("DONE")


asyncio.run(main())
