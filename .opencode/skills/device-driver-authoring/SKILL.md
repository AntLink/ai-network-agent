---
name: device-driver-authoring
description: Guidelines for creating new vendor drivers.
compatibility: OpenCode
---

# Device Driver Authoring

Use when adding a new vendor/platform.

## Driver Requirements
A driver must:
- implement the common `device_identify` logic.
- declare supported transports (SSH, API, NETCONF).
- declare capabilities.
- map vendor‑specific commands to standardized tool inputs (e.g., `device_get_facts`, `device_get_config`).
- return **structured JSON** for every method (see Response Format below).

## Mandatory Response Format (2026-08-24)

Every driver method MUST return structured JSON, never raw CLI text.

### READ methods
```python
{
    "data": <parsed_structured_data>,   # list or dict, parsed from CLI
    "raw": "<original_cli_text>"        # always kept for debugging
}
```
Parsers live in `backend/app/drivers/<vendor>/parser.py` as `@staticmethod`.
Add a parser for each `get_*` method (interfaces, routes, vlans, facts, ...).

### WRITE methods (POST/DELETE/PATCH)
Normalize via `write_response()` helper from `app/api/v1/endpoints/helpers.py`:
```python
from app.api.v1.endpoints.helpers import write_response
...
return write_response(output, operation="create_vlan")
# -> {"status": "applied", "operation": "create_vlan", "success": True, "output": ""}
```
Endpoints MUST return the driver result directly (no double-wrap).

### Rules
1. Never return bare strings / raw text as the response body.
2. `data` = parsed structure; `raw` = original CLI (both present).
3. Write endpoints: use `write_response()`, never nest driver dict inside `output`.
4. Parser must be robust: skip header lines, banners, flag legends.

## Naming Convention
- Skill name format: `vendor-platform` (e.g., `arista-eos`, `huawei-vrp`).
- Place in `.opencode/skills/<name>/SKILL.md`.

## Checklist
1. Identify vendor/platform.
2. Define capabilities.
3. Add identification regex/pattern to `device_identify` tool.
4. Map commands:
   - `get_facts`: `show version` / `display version` / `system show`.
   - `get_config`: `show running-config` / `display current-configuration`.
   - `get_interfaces`: `show interfaces` / `display interface`.
   - `get_routes`: `show ip route` / `display ip routing-table`.
5. Define risk classifications for changes.
6. Add tests with mock outputs.

## Refactoring Best Practices (Cisco Driver Example - 2026-08-24)

### When to Extract Common Logic
Extract shared utilities into a `base.py` module when:
- Same logic appears in 2+ driver files
- Credential management, IP parsing, or device identification
- Constants used across multiple files

### Code Structure Pattern
```
vendor-driver/
├── __init__.py          # High-level API
├── base.py             # Common utilities (NEW)
│   ├── get_credentials()
│   ├── prefix_to_mask()
│   ├── route_target()
│   └── extract_hostname()
├── driver.py           # Async driver
├── netmiko_driver.py   # Sync Netmiko driver
├── connection.py       # Connection wrapper
└── cli.py              # CLI parsing & error handling
```

### Single Source of Truth
- **Credential management**: Centralize in one function (e.g., `get_credentials()`)
- **Priority hierarchy**: Device-specific > Global > Defaults
- **Environment variables**: Use consistent naming patterns (`{DEVICE_ID}_USERNAME`)

### Avoid Code Duplication
**Before (BAD):**
```python
# In driver.py
from app.drivers.cisco.driver import CiscoDriver
    def _get_credentials(self) -> tuple:
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
        secret = os.getenv(f"{prefix}_SECRET", os.getenv("NETWORK_SECRET", password))
        return username, password, secret

# In netmiko_driver.py
class NetmikoCiscoDriver:
    def _get_connection_params(self):
        # DUPLICATE CREDENTIAL LOGIC!
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
        secret = os.getenv(f"{prefix}_SECRET", os.getenv("NETWORK_SECRET", password))
        return {...}
```

**After (GOOD):**
```python
# In base.py
from .base import get_credentials

def get_credentials(device: dict) -> Tuple[str, str, str]:
    """Single source of truth for credential management."""
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD", ""))
    secret = os.getenv(f"{prefix}_SECRET", os.getenv("NETWORK_SECRET", password))
    return username, password, secret

# In driver.py, netmiko_driver.py, connection.py
from .base import get_credentials

username, password, secret = get_credentials(self.device)
```

### Backward Compatibility
- **Don't change external API** - Keep method signatures the same
- **Use internal refactoring** - Move logic, don't change interfaces
- **Test thoroughly** - Verify all imports and functionality work

### API Response Format Standardization
**All driver methods MUST return structured JSON in this format:**

```python
{
    "data": <parsed_structured_data>,  # Required: parsed JSON or raw text
    "raw": "<original_cli_output>"      # Required: original CLI text
}
```

**Implementation Guidelines:**
1. **Create parser module**: Each vendor should have a `parser.py` with static methods
2. **Use parser in driver**: Call parser methods in driver's read operations
3. **Always include raw**: Even if parsing fails, include original text in `raw` field
4. **Graceful fallback**: If parsing fails, set `data = raw` to maintain consistency

**Example Pattern:**
```python
# In parser.py
class VendorParser:
    @staticmethod
    def parse_version(raw_text: str) -> Dict[str, Any]:
        # Parse CLI output into structured data
        return {"version": "15.6(3)M2", "model": "IOSv", ...}

# In driver.py
from .parser import VendorParser

async def get_facts(self) -> dict:
    raw = await self._exec("show version")
    parsed = VendorParser.parse_version(raw)
    return {"data": parsed, "raw": raw}
```

### Testing Requirements
- **Import tests**: Verify all modules can be imported
- **Utility tests**: Test each shared function
- **Integration tests**: Test drivers work together
- **Live tests**: Test with real devices (if available)
- **Parser tests**: Test each parser with sample CLI output
