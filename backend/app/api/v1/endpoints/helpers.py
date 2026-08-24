"""Shared response helpers for write (POST/DELETE/PATCH) endpoints.

Normalizes driver results into a consistent JSON shape so the frontend
gets stable fields instead of raw/empty CLI output:

    {
      "status": "applied",          # applied | deleted | saved | committed | ok | failed
      "operation": "create_vlan",   # driver method name
      "success": true,
      "output": ""                  # raw device output (usually empty for config ops)
    }
"""


def write_response(result, operation: str | None = None, default_status: str = "applied") -> dict:
    """Build a consistent JSON response for a write operation."""
    if isinstance(result, dict):
        status = result.get("status") or default_status
        output = result.get("output", "")
    elif result is None:
        status = default_status
        output = ""
    else:
        status = default_status
        output = str(result)

    success = status in ("applied", "deleted", "saved", "committed", "ok", "OK")

    return {
        "status": status,
        "operation": operation or "",
        "success": success,
        "output": output,
    }