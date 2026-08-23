"""
Explore data sources on the embedded CSMS Linux system (192.168.162.20)
for building a custom monitoring application.
Output is saved to explore_data_sources_output.txt
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from app.transports.ssh import SSHTransport
from app.core import config as cfg_mod

load_dotenv(Path(__file__).parent / ".env")

cfg_mod.settings.SSH_CONNECT_TIMEOUT = 30
cfg_mod.settings.SSH_COMMAND_TIMEOUT = 30

HOST = "192.168.162.20"
USER = os.getenv("LINUX_EMBEDDED_USERNAME", "root")
PASS = os.getenv("LINUX_EMBEDDED_PASSWORD", "815m1ll4h")
OUTPUT_FILE = Path(__file__).parent / "explore_data_sources_output.txt"

EXPLORATION_COMMANDS = [
    # 1. SQLite Database Structure
    ("1a. DB files in /media/tci/csms/data",
     "ls -la /media/tci/csms/data/*.db 2>/dev/null || echo no_db_files"),

    ("1b. Database Tables",
     'sqlite3 /media/tci/csms/data/csmsdb.db ".tables" 2>/dev/null || echo sqlite3_not_available'),

    ("1c. Table Schema",
     'sqlite3 /media/tci/csms/data/csmsdb.db ".schema" 2>/dev/null | head -100 || echo schema_unavailable'),

    ("1d. All table names via sqlite_master",
     'sqlite3 /media/tci/csms/data/csmsdb.db "SELECT name FROM sqlite_master WHERE type=\'table\';" 2>/dev/null || echo query_failed'),

    ("1e. Sample events",
     'sqlite3 /media/tci/csms/data/csmsdb.db "SELECT * FROM events LIMIT 5;" 2>/dev/null || echo no_events_table'),

    ("1f. Sample signals",
     'sqlite3 /media/tci/csms/data/csmsdb.db "SELECT * FROM signals LIMIT 5;" 2>/dev/null || echo no_signals_table'),

    ("1g. DB dump first 50 lines",
     'sqlite3 /media/tci/csms/data/csmsdb.db ".dump" 2>/dev/null | head -50 || echo dump_failed'),

    # 2. GPS Data
    ("2a. GPS data",
     "timeout 3 gpsd -x 1 localhost 2>/dev/null | head -20 || echo gpsd_failed"),

    ("2b. GPS socket check",
     "timeout 3 sh -c 'echo \"?VERSION;\" | nc localhost 2947' 2>/dev/null || echo gpsd_socket_failed"),

    # 3. CSMS API/Socket
    ("3a. CSMS socket files",
     'find /var/run -name "*csms*" 2>/dev/null; find /tmp -name "*csms*" 2>/dev/null; ls -la /var/run/*.sock 2>/dev/null || echo no_sockets'),

    # 4. System Monitoring
    ("4a. /proc/stat (CPU)",
     "head -5 /proc/stat"),

    ("4b. /proc/meminfo",
     "head -10 /proc/meminfo"),

    ("4c. /proc/net/dev (network)",
     "cat /proc/net/dev"),

    ("4d. /proc/diskstats",
     "head -10 /proc/diskstats"),

    ("4e. Temperature sensors",
     "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null || echo no_thermal_zones"),

    # 5. Log Files
    ("5a. /var/volatile/log/",
     "ls -la /var/volatile/log/ 2>/dev/null || echo dir_not_found"),

    ("5b. csmsd.log tail",
     "tail -20 /var/volatile/log/csmsd.log 2>/dev/null || echo csmsd_log_not_found"),

    ("5c. /var/log/",
     "ls -la /var/log/"),

    # 6. Process List
    ("6. Process list",
     "ps aux"),

    # 7. Hardware Interfaces
    ("7. Hardware interfaces",
     "ls -la /dev/ttyPS* 2>/dev/null; ls -la /dev/i2c* 2>/dev/null; ls -la /dev/spi* 2>/dev/null; ls -la /dev/gpio* 2>/dev/null; echo done"),

    # 8. FPGA Status
    ("8. FPGA status",
     'cat /proc/iomem 2>/dev/null | grep -i "fpga\\|zynq" | head -10; ls -la /dev/fpga* 2>/dev/null || echo no_fpga_device'),

    # 9. Available interpreters
    ("9. Available interpreters",
     "which python 2>/dev/null || which python3 2>/dev/null || echo no_python; which perl 2>/dev/null || echo no_perl; which php 2>/dev/null || echo no_php"),

    # 10. CSMS XML Config
    ("10. CSMS XML Config",
     "cat /media/tci/csms/config/CSMSConfig.xml 2>/dev/null | head -100 || echo config_not_found"),

    # 11. Uptime / general
    ("11. Uptime and disk usage",
     "uptime; df -h 2>/dev/null"),

    # 12. Full list of /media/tci/csms/
    ("12. CSMS directory tree",
     "find /media/tci/csms/ -maxdepth 3 -type f 2>/dev/null | head -50 || echo tree_failed"),
]


async def explore():
    transport = SSHTransport(host=HOST, username=USER, password=PASS)
    lines = []
    lines.append(f"Connecting to {HOST} as {USER} ...")
    lines.append("=" * 70)

    for label, cmd in EXPLORATION_COMMANDS:
        lines.append("")
        lines.append("-" * 70)
        lines.append(f">>> {label}")
        lines.append("-" * 70)
        try:
            output = await transport.run(cmd)
            lines.append(output if output else "(no output)")
        except Exception as e:
            lines.append(f"ERROR: {e}")

    lines.append("")
    lines.append("=" * 70)
    lines.append("Exploration complete.")

    result = "\n".join(lines)
    OUTPUT_FILE.write_text(result, encoding="utf-8")
    print(f"Output saved to {OUTPUT_FILE}")
    print(f"Total sections: {len(EXPLORATION_COMMANDS)}")


if __name__ == "__main__":
    asyncio.run(explore())
