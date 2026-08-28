# Summary of Changes - JSON Response Format for All Backend Endpoints

## Objective
Convert ALL backend endpoints (Cisco, MikroTik, Switch) to return structured JSON instead of raw CLI text for easier frontend data management.

## Follow-up Fix - Agent Chat History Persistence
The AI agent chat UI was stabilized after a follow-up regression where the previous assistant bubble could render empty and older history could disappear after refresh.

### What Was Fixed

- Backend session message storage now upserts by message ID instead of blindly appending duplicates.
- Frontend agent runtime now replays the stored session transcript back into the thread on reload.
- Assistant bubble rendering now falls back to persisted session text when runtime content is temporarily empty.
- Follow-up runs no longer wipe earlier messages when the session is refreshed.

### Validation

- `npm run lint` passed
- `npm run build` passed

## Frontend Follow-up
The device detail UI was updated after the backend normalization to make the frontend more operationally useful:

- Added vendor-aware device detail layouts for Cisco router, Cisco switch, and MikroTik router.
- Added a loading overlay and skeleton state when opening `device -> details`.
- Added toast notifications for success, failure, and timeout states.
- Rendered detail tabs and summary blocks as tables/cards instead of raw preformatted output where possible.

## Changes Made

### 1. Cisco Driver (`backend/app/drivers/cisco/driver.py`)
- **Added import**: `from .parser import IOSParser`
- **Updated all read methods** to use `IOSParser.parse_*` methods and return `{"data": parsed, "raw": raw}` format:
  - `identify()` - uses `IOSParser.parse_version()`
  - `get_facts()` - uses `IOSParser.parse_version()`
  - `get_interfaces()` - uses `IOSParser.parse_interfaces_brief()`
  - `get_interfaces_detail()` - uses `IOSParser.parse_interfaces_detail()`
  - `get_routes()` - uses `IOSParser.parse_routes()`
  - `get_arp()` - uses `IOSParser.parse_arp()`
  - `get_cpu_memory()` - uses `IOSParser.parse_cpu_memory()`
  - `get_acls()` - uses `IOSParser.parse_access_lists()`
  - `get_cdp_neighbors()` - uses `IOSParser.parse_cdp_neighbors()`
  - `get_nat_translations()` - uses `IOSParser.parse_nat_translations()`
  - `get_startup_config()` - returns `{"data": raw, "raw": raw}`
  - `get_logs()` - returns `{"data": raw, "raw": raw}`
  - `get_config()` - returns `{"data": raw, "raw": raw}`
  - `backup()` - returns `{"data": raw, "raw": raw}`
  - `ping_tool()` - returns parsed ping statistics with success_rate and loss_percent
  - `traceroute_tool()` - returns `{"data": raw, "raw": raw}`

### 2. Cisco Parser (`backend/app/drivers/cisco/parser.py`)
- **Already existed** with comprehensive parser methods:
  - `parse_interfaces()` - for TextFSM output
  - `parse_static_routes()` - for plain-text route output
  - `parse_cpu_memory()` - for CPU and memory statistics
  - `parse_interfaces_brief()` - for `show ip interface brief`
  - `parse_interfaces_detail()` - for `show interfaces`
  - `parse_routes()` - for `show ip route`
  - `parse_arp()` - for `show ip arp`
  - `parse_version()` - for `show version`
  - `parse_access_lists()` - for `show access-lists`
  - `parse_cdp_neighbors()` - for `show cdp neighbors detail`
  - `parse_nat_translations()` - for `show ip nat translation`

### 3. MikroTik Parser (`backend/app/drivers/mikrotik/parser.py`)
- **Newly created** with parser methods for MikroTik RouterOS:
  - `parse_identity()` - for `/system identity print`
  - `parse_resource()` - for `/system resource print`
  - `parse_interfaces()` - for `/interface print detail`
  - `parse_routes()` - for `/ip route print detail`
  - `parse_ip_addresses()` - for `/ip address print detail`
  - `parse_config()` - for `/export terse`
  - `parse_system_users()` - for `/user print detail`
  - `parse_dhcp_server()` - for `/ip dhcp-server print detail`

### 4. MikroTik Driver (`backend/app/drivers/mikrotik/driver.py`)
- **Added import**: `from .parser import MikroTikParser`
- **Updated all read methods** to use `MikroTikParser.parse_*` methods where applicable and return `{"data": parsed, "raw": raw}` format:
  - `identify()` - uses `MikroTikParser.parse_identity()` and `MikroTikParser.parse_resource()`
  - `get_facts()` - uses `MikroTikParser.parse_resource()`
  - `get_interfaces()` - uses `MikroTikParser.parse_interfaces()`
  - `get_routes()` - uses `MikroTikParser.parse_routes()`
  - `get_config()` - uses `MikroTikParser.parse_config()`
  - `get_ip_addresses()` - uses `MikroTikParser.parse_ip_addresses()`
  - `get_dhcp_server()` - uses `MikroTikParser.parse_dhcp_server()`
  - `get_system_users()` - uses `MikroTikParser.parse_system_users()`
  - `backup()` - uses `MikroTikParser.parse_config()`
  - **All other methods** - updated to return `{"data": raw, "raw": raw}` for consistency

### 5. Generic Driver (`backend/app/drivers/generic/driver.py`)
- **Updated methods** to return `{"data": raw, "raw": raw}` format:
  - `identify()` - returns `{"vendor": "unknown", "data": raw, "raw": raw}`
  - `get_facts()` - returns `{"vendor": "unknown", "data": raw, "raw": raw}`

### 6. Monitoring Endpoint (`backend/app/api/v1/endpoints/monitoring.py`)
- **Updated** to use parsed data from drivers when available:
  - Now checks for `"data"` key in driver responses and uses it if available
  - Falls back to `"raw"` key if parsed data is not available
  - Returns structured JSON with:
    - `cpu_memory` - parsed CPU and memory statistics
    - `interfaces` - parsed interface data
    - `routes` - parsed route data
    - `facts` - parsed device facts (version, uptime, etc.)
    - `health` - device health check

## Response Format

All endpoint responses now follow this structure:

```json
{
  "data": <parsed_structured_json>,
  "raw": "<original_cli_text>"
}
```

Where:
- `data` - Contains structured JSON parsed from CLI output (when parser is available)
- `raw` - Contains the original CLI text output (for debugging and fallback)

For methods without specific parsers (e.g., config backups, logs), both `data` and `raw` contain the same text value.

## Benefits

1. **Frontend-Friendly**: Structured JSON is easier to display in tables and UI components
2. **Consistent API**: All endpoints return the same response format
3. **Backward Compatible**: Raw CLI text is still available for debugging
4. **Extensible**: New parsers can be added without breaking existing clients
5. **Better Error Handling**: Frontend can detect and handle parsing failures gracefully

## Testing

All modules have been verified to import correctly:
- ✅ Cisco driver
- ✅ Cisco parser
- ✅ MikroTik driver
- ✅ MikroTik parser
- ✅ Generic driver
- ✅ Monitoring endpoint

## Next Steps

1. Test each endpoint with real devices to verify parsing accuracy
2. Add more specific parsers for additional commands as needed
3. Update frontend to use the structured `data` field instead of `raw`
4. Add validation for parsed data structures
