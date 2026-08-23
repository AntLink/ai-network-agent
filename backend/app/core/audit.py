import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_DIR / "audit.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
audit_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
audit_logger.addHandler(console_handler)


def log_event(
    device_id: str,
    action: str,
    command: str,
    result: str = "",
    user: str = "system",
    status: str | None = None,
    duration_ms: int | None = None,
    error: str | None = None,
):
    """Audit event.

    Example output:
    23:47:39 | cisco-iosv-r1 | EXEC | show version | OK | 571 ms | user=system
    23:47:40 | cisco-iosv-r1 | CONFIG | hostname R2 | FAIL | 612 ms | ERROR: ... | user=system
    """
    msg = f"{device_id} | {action} | {command} | user={user}"
    if status:
        msg += f" | {status}"
    if duration_ms is not None:
        msg += f" | {duration_ms} ms"
    if error:
        msg += f" | ERROR: {error[:300]}"
    elif result:
        msg += f" | {result[:200]}"
    audit_logger.info(msg)
