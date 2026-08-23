import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 30
settings.SSH_CONNECT_TIMEOUT = 30

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMAND = r"""
# Step 1: Check all listening ports
echo "=== All Listening Ports ==="
netstat -tlnp 2>/dev/null
netstat -ulnp 2>/dev/null

# Step 2: Check csmsd file descriptors
echo ""
echo "=== csmsd File Descriptors ==="
CSMS_PID=$(pidof csmsd.elf)
if [ -n "$CSMS_PID" ]; then
  echo "PID: $CSMS_PID"
  ls -la /proc/$CSMS_PID/fd/ 2>/dev/null | head -30
  cat /proc/$CSMS_PID/net/tcp 2>/dev/null | head -10
  cat /proc/$CSMS_PID/net/udp 2>/dev/null | head -10
else
  echo "csmsd not running"
fi

# Step 3: Check csmsd logs
echo ""
echo "=== csmsd Logs ==="
tail -100 /var/volatile/log/messages 2>/dev/null | grep -i csms
cat /media/tci/csms/logs/*.log 2>/dev/null | tail -50

# Step 4: Check CSMSConfig for port settings
echo ""
echo "=== CSMSConfig.xml Port Settings ==="
grep -iE "port|scpi|listen|bind|37000|37001|5025|9999|10001" /media/tci/csms/etc/CSMSConfig.xml 2>/dev/null

# Step 5: Check if csmsd needs specific config
echo ""
echo "=== csmsd Command Line Args ==="
cat /proc/$CSMS_PID/cmdline 2>/dev/null | tr '\0' ' ' || echo "no cmdline"

# Step 6: Check for any error messages
echo ""
echo "=== csmsd Error Messages ==="
strings /media/tci/csms/bin/csmsd.elf | grep -iE "error|fail|cannot|unable" | head -20

# Step 7: Check license again
echo ""
echo "=== License Check ==="
cat /media/tci/csms/etc/CsmsLicense.lic 2>/dev/null | head -10

# Step 8: Check if there's a SCPI config
echo ""
echo "=== SCPI Config ==="
find /media/tci/csms -name "*scpi*" -o -name "*SCPI*" 2>/dev/null
grep -r "scpi\|5025" /media/tci/csms/etc/ 2>/dev/null

exit 0
"""


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  DEBUG: WHY csmsd.elf IS NOT OPENING SCPI PORTS ON 192.168.162.20")
    print("=" * 70)

    try:
        result = await transport.run(COMMAND)
        print(result if result.strip() else "(no output)")
    except Exception as e:
        print(f"ERROR: {e}")

    print("=" * 70)
    print("  DEBUG COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
