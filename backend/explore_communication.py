import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

# Add backend to path so app.transports.ssh can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USERNAME = "root"
PASSWORD = "815m1ll4h"
COMMAND_TIMEOUT = 120


EXPLORATION_COMMANDS = [
    # 1. All Network Connections
    """echo "=========================================="
echo "  CSMS COMMUNICATION ARCHITECTURE"
echo "=========================================="

echo ""
echo "=== 1. All Network Connections ==="
netstat -tlnp 2>/dev/null
echo ""
echo "=== Active Connections ==="
netstat -anp 2>/dev/null | grep -E "ESTABLISHED|SYN" | head -30""",

    # 2. CGI Scripts
    """echo ""
echo "=== 2. CGI Scripts (Web Interface) ==="
ls -la /media/httpd/cgi-bin/
echo ""
echo "=== CGI Script Contents ==="
for f in /media/httpd/cgi-bin/*.cgi; do
  echo "--- $f ---"
  head -30 $f 2>/dev/null
  echo ""
done""",

    # 3. CSMS Configuration
    """echo ""
echo "=== 3. CSMS Configuration ==="
find /media/tci/csms -type f 2>/dev/null
echo ""
cat /media/tci/csms/*.conf 2>/dev/null
cat /media/tci/csms/*.txt 2>/dev/null | head -100""",

    # 4. TCI Configuration
    """echo ""
echo "=== 4. TCI Configuration ==="
ls -la /media/TCI/ 2>/dev/null
cat /media/TCI/*.conf 2>/dev/null
cat /media/TCI/*.txt 2>/dev/null | head -100""",

    # 5. Antenna Configuration
    """echo ""
echo "=== 5. Antenna Configuration ==="
find /media -name "*antenna*" -o -name "*ant*" 2>/dev/null | head -20
cat /media/tci/csms/antenna*.txt 2>/dev/null | head -50
cat /media/TCI/antenna*.txt 2>/dev/null | head -50""",

    # 6. HF Switch Configuration
    """echo ""
echo "=== 6. HF Switch Configuration ==="
cat /media/tci/csms/hfswitch.txt 2>/dev/null
cat /media/tci/csms/hfswitchlf.txt 2>/dev/null
cat /media/TCI/hfswitch*.txt 2>/dev/null""",

    # 7. GPS Configuration
    """echo ""
echo "=== 7. GPS Configuration ==="
cat /etc/ntp.conf 2>/dev/null
ls -la /dev/ttyPS* 2>/dev/null
cat /media/TCI/gps*.txt 2>/dev/null | head -30""",

    # 8. Database
    """echo ""
echo "=== 8. Database ==="
find /media -name "*.db" 2>/dev/null
ls -la /media/tci/csms/*.db 2>/dev/null""",

    # 9. SendIP Configuration
    """echo ""
echo "=== 9. SendIP Configuration ==="
find /media -name "*SendIP*" -o -name "*sendip*" 2>/dev/null
cat /media/TCI/SendIP* 2>/dev/null | head -30""",

    # 10. Web Interface HTML
    """echo ""
echo "=== 10. Web Interface HTML ==="
cat /media/httpd/index.html 2>/dev/null | head -50
find /media/httpd -name "*.html" 2>/dev/null""",

    # 11. FPGA Configuration
    """echo ""
echo "=== 11. FPGA Configuration ==="
find /media -name "*.jbc" -o -name "*.bit" 2>/dev/null
cat /media/httpd/cgi-bin/zynqdownload.cgi 2>/dev/null | head -50""",

    # 12. Port Scanning from Inside
    """echo ""
echo "=== 12. Port Scanning from Inside ==="
netstat -tlnp 2>/dev/null | awk '{print $4}' | sort -u""",

    # 13. CSMS Daemon Log
    """echo ""
echo "=== 13. CSMS Daemon Log ==="
cat /var/volatile/log/csmsd.log 2>/dev/null | tail -50
cat /var/log/messages 2>/dev/null | grep -i "csms\\|tci\\|gps\\|audio" | tail -30""",

    # 14. SpectrumMonitor Script
    """echo ""
echo "=== 14. SpectrumMonitor Script ==="
cat /media/tci/SpectrumMonitor 2>/dev/null""",

    # 15. Init Scripts for CSMS
    """echo ""
echo "=== 15. Init Scripts for CSMS ==="
ls -la /etc/init.d/ | grep -E "tci|csms|spectrum"
cat /etc/init.d/S25tcistartup 2>/dev/null || cat /etc/rcS.d/S25* 2>/dev/null | head -30
cat /etc/init.d/S99csmsd 2>/dev/null || cat /etc/rcS.d/S99* 2>/dev/null | head -30""",

    # 16. Binary Details
    """echo ""
echo "=== 16. Binary Details ==="
file /media/tci/csms/csmsd.elf 2>/dev/null
file /media/tci/csms/csmsAudio.elf 2>/dev/null
file /media/TCI/SendIP.elf 2>/dev/null""",
]


async def main():
    print(f"[+] Connecting to {HOST} as {USERNAME}...")
    ssh = SSHTransport(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
    )

    # Override command timeout for this session
    from app.core import config as cfg_mod
    original_timeout = cfg_mod.settings.SSH_COMMAND_TIMEOUT
    cfg_mod.settings.SSH_COMMAND_TIMEOUT = COMMAND_TIMEOUT

    try:
        # Single command to run everything in one session for efficiency
        combined_script = "\n\n".join(EXPLORATION_COMMANDS)
        print(f"[+] Running combined exploration script (timeout={COMMAND_TIMEOUT}s per command)...")
        output = await ssh.run(combined_script)
        print("\n" + output)
    except Exception as e:
        print(f"\n[!] SSH Error: {e}")
        # Try running commands individually
        print("\n[+] Falling back to individual command execution...")
        for i, cmd in enumerate(EXPLORATION_COMMANDS, 1):
            section = cmd.split('\n')[0] if '\n' in cmd else cmd
            print(f"\n{'='*60}")
            print(f"  SECTION {i}")
            print(f"{'='*60}")
            try:
                output = await ssh.run(cmd)
                print(output)
            except Exception as e2:
                print(f"[!] Error in section {i}: {e2}")
    finally:
        cfg_mod.settings.SSH_COMMAND_TIMEOUT = original_timeout
        print("\n[+] Exploration complete.")


if __name__ == "__main__":
    asyncio.run(main())
