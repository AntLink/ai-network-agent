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

SCRIPT = r'''
echo "=== CSMS Frequency Data Analysis ==="

echo ""
echo "--- 1. Copy DB to local ---"
# Copy the database file to local machine for analysis
cp /media/tci/csms/data/csmsdb.db /tmp/csmsdb.db && ls -la /tmp/csmsdb.db

echo ""
echo "--- 2. Search for frequency patterns in DB ---"
strings /media/tci/csms/data/csmsdb.db | grep -E "[0-9]{3,6}" | head -50

echo ""
echo "--- 3. Check CSMS XML configs ---"
cat /media/tci/csms/etc/CSMSConfig.xml 2>/dev/null | head -200

echo ""
echo "--- 4. Check General config ---"
cat /media/tci/csms/etc/csmsGeneral.xml 2>/dev/null | head -200

echo ""
echo "--- 5. Antenna frequency ranges ---"
for f in /media/tci/csms/antenna*.txt; do
  echo "=== $f ==="
  cat $f 2>/dev/null | head -20
done

echo ""
echo "--- 6. ProcParams CSV ---"
cat /media/tci/csms/etc/ProcParamsV2.csv 2>/dev/null | head -50

echo ""
echo "--- 7. CSMS database table structure ---"
strings /media/tci/csms/data/csmsdb.db | grep -iE "CREATE|TABLE|freq|signal|spectrum|power|dBm|MHz" | head -50

echo ""
echo "--- 8. Check for frequency values in DB ---"
strings /media/tci/csms/data/csmsdb.db | grep -E "^[0-9]+\.[0-9]+$" | head -30

echo ""
echo "--- 9. Custom settings ---"
cat /media/tci/csms/etc/csmsCustomSettings.xml 2>/dev/null | head -100

echo ""
echo "--- 10. HF switch configs ---"
cat /media/tci/csms/hfswitch.txt 2>/dev/null
cat /media/tci/csms/ushfswitch.txt 2>/dev/null

exit 0
'''

OUT_FILE = "explore_frequency_output.txt"


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    lines = []

    def emit(text=""):
        print(text)
        lines.append(text)

    emit("=" * 60)
    emit("  CSMS FREQUENCY DATA ANALYSIS")
    emit("=" * 60)

    try:
        result = await transport.run(SCRIPT)
        emit(result)
    except Exception as e:
        emit(f"ERROR: {e}")

    emit()
    emit("=" * 60)
    emit("  EXPLORATION COMPLETE")
    emit("=" * 60)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nFull output saved to {OUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
