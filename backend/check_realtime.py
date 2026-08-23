import asyncio
import sys

from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

from app.core.config import settings  # noqa: E402
from app.transports.ssh import SSHTransport  # noqa: E402

settings.SSH_COMMAND_TIMEOUT = 30

HOST = "192.168.162.20"
USERNAME = "root"
PASSWORD = "815m1ll4h"
LOG_PATH = r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\realtime_out.txt"

_log_fh = open(LOG_PATH, "w", encoding="utf-8")


def out(text: str = "") -> None:
    print(text)
    _log_fh.write(text + "\n")
    _log_fh.flush()

COMMANDS = {
    "Command 1: Find all Unix sockets": r"""
find /var/run /tmp /media -type s 2>/dev/null
ls -la /var/run/*.sock 2>/dev/null
ls -la /tmp/*.sock 2>/dev/null
""",
    "Command 2: Find all FIFOs": r"""
find /tmp /var/run /media -type p 2>/dev/null
ls -la /tmp/*.fifo 2>/dev/null
""",
    "Command 3: Check shared memory": r"""
ls -la /dev/shm/ 2>/dev/null
(timeout 5 ipcs -m 2>/dev/null || echo "ipcs not available")
""",
    "Command 4: Check csmsd.elf network connections": r"""
ps aux | grep csms
netstat -tlnp 2>/dev/null | grep -E "csms|SendIP|127.0.0"
netstat -ulnp 2>/dev/null | grep -E "csms|SendIP"
netstat -anp 2>/dev/null | grep -E "csms|SendIP" | head -20
""",
    "Command 5: Check SendIP.elf network usage": r"""
ps aux | grep SendIP
strings /media/TCI/SendIP.elf 2>/dev/null | grep -iE "udp|tcp|port|connect|bind|socket|send|recv" | head -30
""",
    "Command 6: Check csmsd.elf for API/socket strings": r"""
strings /media/tci/csms/bin/csmsd.elf 2>/dev/null | grep -iE "socket|connect|bind|listen|accept|api|port|udp|tcp" | head -40
""",
    "Command 7: Check if csmsd has any hidden ports": r"""
netstat -tlnp 2>/dev/null
netstat -ulnp 2>/dev/null
""",
    "Command 8: Check /proc for csmsd file descriptors": r"""
CSMS_PID=$(pidof csmsd.elf 2>/dev/null)
if [ -n "$CSMS_PID" ]; then
  echo "csmsd PID: $CSMS_PID"
  ls -la /proc/$CSMS_PID/fd/ 2>/dev/null | head -30
  cat /proc/$CSMS_PID/net/tcp 2>/dev/null | head -10
  cat /proc/$CSMS_PID/net/udp 2>/dev/null | head -10
else
  echo "csmsd.elf not running"
fi
""",
    "Command 9: Check SendIP file descriptors": r"""
SENDIP_PID=$(pidof SendIP.elf 2>/dev/null)
if [ -n "$SENDIP_PID" ]; then
  echo "SendIP PID: $SENDIP_PID"
  ls -la /proc/$SENDIP_PID/fd/ 2>/dev/null | head -30
  cat /proc/$SENDIP_PID/net/tcp 2>/dev/null | head -10
  cat /proc/$SENDIP_PID/net/udp 2>/dev/null | head -10
else
  echo "SendIP.elf not running"
fi
""",
    "Command 10: Check for any data pipes between processes": r"""
ls -la /proc/*/fd 2>/dev/null | grep pipe | head -20
""",
    "Command 11: Check GPS data format": r"""
timeout 3 sh -c 'echo "?VERSION;" | nc localhost 2947' 2>/dev/null
timeout 3 sh -c 'echo "?DEVICES;" | nc localhost 2947' 2>/dev/null
timeout 3 sh -c 'echo "?WATCH={\"enable\":true};" | nc localhost 2947' 2>/dev/null
""",
    "Command 12: Check if there's a TCI protocol port": r"""
strings /media/tci/csms/bin/csmsd.elf 2>/dev/null | grep -E "^[0-9]{4,5}$" | head -10
strings /media/TCI/SendIP.elf 2>/dev/null | grep -E "^[0-9]{4,5}$" | head -10
""",
}


async def main() -> None:
    transport = SSHTransport(host=HOST, username=USERNAME, password=PASSWORD)
    for label, command in COMMANDS.items():
        out("=" * 70)
        out(f">>> {label}")
        out("-" * 70)
        # Normalize exit status: BusyBox ls/find/grep return non-zero on no
        # match, and SSHTransport raises (discarding stdout) in that case.
        script = command.strip() + "\ntrue"
        try:
            output = await transport.run(script)
            out(output if output.strip() else "(no output)")
        except asyncio.TimeoutError:
            out("[ERROR] command timed out after 30s")
        except Exception as exc:
            msg = str(exc).strip()
            out(f"[ERROR] {msg if msg else type(exc).__name__}")
    out("=" * 70)
    _log_fh.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
