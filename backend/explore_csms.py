import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings
settings.SSH_COMMAND_TIMEOUT = 120
settings.SSH_CONNECT_TIMEOUT = 30

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMANDS = {
    "System Identity": """cat /etc/hostname
cat /etc/productversion 2>/dev/null
cat /etc/product 2>/dev/null
uname -a
cat /proc/version
cat /etc/issue""",

    "CSMS Files": """find / -name "*csms*" -type f 2>/dev/null | head -30
ls -la /media/tci/csms/ 2>/dev/null
ls -la /media/tci/ 2>/dev/null
ls -la /media/TCI/ 2>/dev/null""",

    "CSMS Config Files": """find /media -name "*.conf" -o -name "*.cfg" -o -name "*.ini" 2>/dev/null | head -20
cat /media/tci/csms/*.conf 2>/dev/null | head -50
cat /media/TCI/*.conf 2>/dev/null | head -50""",

    "CSMS Services Running": """ps aux | grep -E "csms|TCI|tci" | grep -v grep""",

    "Network Connections": """netstat -tlnp 2>/dev/null | head -30
netstat -anp 2>/dev/null | grep -E "ESTABLISHED|LISTEN" | head -30""",

    "TCI Files": """ls -la /media/TCI/ 2>/dev/null
find /media/TCI -type f 2>/dev/null | head -30""",

    "GPS/NTP": """ntpq -p 2>/dev/null
cat /etc/ntp.conf 2>/dev/null | head -20
ls -la /dev/ttyPS* 2>/dev/null""",

    "Audio Files": """find /media -name "*.elf" -o -name "*.wav" -o -name "*.mp3" 2>/dev/null | head -20""",

    "HTTP/CGI": """ls -la /media/httpd/ 2>/dev/null
ls -la /media/httpd/cgi-bin/ 2>/dev/null
cat /media/httpd/index.html 2>/dev/null | head -30""",

    "Logs": """ls -la /var/log/ 2>/dev/null
tail -50 /var/log/messages 2>/dev/null | head -50""",

    "Cron Jobs": """crontab -l 2>/dev/null
ls -la /etc/cron* 2>/dev/null""",

    "Startup Scripts": """ls -la /etc/init.d/ | grep -E "tci|csms|audio|spectrum|gps" """,

    "Spectrum Monitor": """cat /media/tci/SpectrumMonitor 2>/dev/null | head -30""",

    "All ELF binaries": """find /media -name "*.elf" 2>/dev/null""",

    "System Properties": """cat /proc/cpuinfo | head -10
cat /proc/meminfo | head -5
df -h""",
}


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 60)
    print("  CSMS-SINGKAWANG SYSTEM EXPLORATION")
    print("=" * 60)

    for label, cmd in COMMANDS.items():
        print(f"\n{'=' * 60}")
        print(f"  {label}")
        print(f"{'=' * 60}")
        try:
            result = await transport.run(cmd)
            print(result)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'=' * 60}")
    print("  EXPLORATION COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
