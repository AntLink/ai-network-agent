# JSON Response Format - Complete Documentation

## Overview

All API endpoints in this project now return structured JSON responses. This ensures that frontend applications can easily parse and display the data without needing to parse raw CLI text.

## Response Structure

### Standard Format for Read Operations (GET)

All read-only endpoints (GET requests) that retrieve data from devices return responses in the following format:

```json
{
  "data": <structured_or_parsed_data>,
  "raw": "raw_cli_output_text"
}
```

- `data`: Contains the parsed/structured data (dict, list, or string)
- `raw`: Contains the raw CLI output as a string (for debugging/troubleshooting)

### Standard Format for Write Operations (POST, DELETE, etc.)

All write operations that configure devices return responses in the following format:

```json
{
  "status": "applied" | "ok" | "saved" | "error",
  "output": "command_output_text"
}
```

- `status`: Indicates the operation result
- `output`: Contains the CLI output from the configuration commands

### Error Format

When errors occur, endpoints return:

```json
{
  "status": "error",
  "error": "error_message_string",
  "device_id": "device_identifier"
}
```

## Device-Specific Endpoints

### MikroTik Devices

All endpoints under `/api/v1/mikrotik/` return structured JSON:

- **Health**: `/api/v1/mikrotik/{device_id}/health`
  - Returns device reachability, SSH banner, and structured resource data
  - Resource data includes: uptime, version, CPU load, memory usage, etc.
  
- **Facts**: `/api/v1/mikrotik/{device_id}/facts`
  - Returns parsed system resource information
  
- **Interfaces**: `/api/v1/mikrotik/{device_id}/resources/interfaces`
  - Returns parsed interface data (name, type, status, etc.)
  
- **All other get_* endpoints**: Return `{"data": ..., "raw": ...}` format

### Cisco Devices (IOS, IOS-XE, etc.)

All endpoints under `/api/v1/cisco/` return structured JSON:

- **Facts**: `/api/v1/cisco/{device_id}/resources/version`
  - Returns show version output in structured format
  
- **Interfaces**: `/api/v1/cisco/{device_id}/resources/interfaces`
  - Returns interface information
  
- **All get_* methods**: Return `{"data": ..., "raw": ...}` format
  
- **Configuration methods**: Return `{"status": "applied", "output": ...}` format

### Generic Devices

Generic SSH devices return:
- `identify()`: `{"vendor": "unknown", "data": raw, "raw": raw}`
- `get_facts()`: `{"vendor": "unknown", "data": raw, "raw": raw}`

## Monitoring Endpoint

The monitoring endpoint `/api/v1/monitoring/{device_id}` aggregates data from multiple driver methods:

```json
{
  "device_id": "string",
  "hostname": "string",
  "vendor": "cisco" | "mikrotik" | "unknown",
  "management_address": "string",
  "cpu_memory": { ... },          // From get_cpu_memory()
  "interfaces": [ ... ],         // From get_interfaces()
  "health": { ... },             // From health()
  "routes": [ ... ],             // From get_routes()
  "facts": { ... }              // From get_facts()
}
```

If a driver method returns `{"data": ..., "raw": ...}`, the monitoring endpoint uses the `data` field.
If a driver method returns `{"raw": ...}` (legacy), the monitoring endpoint uses the `raw` field and adds a `_raw` suffix to the key.

## Parsers

### MikroTik Parser (`backend/app/drivers/mikrotik/parser.py`)

Parses RouterOS CLI output into structured JSON:

- `parse_identity()`: Parses `/system identity print`
- `parse_resource()`: Parses `/system resource print` (uptime, version, CPU, memory, etc.)
- `parse_interfaces()`: Parses `/interface print detail`
- `parse_routes()`: Parses `/ip route print`
- `parse_ip_addresses()`: Parses `/ip address print`
- `parse_dhcp_server()`: Parses `/ip dhcp-server print`
- And many more...

### Cisco Parser (`backend/app/drivers/cisco/parser.py`)

Parses Cisco IOS CLI output:

- `parse_interfaces()`: Parses `show ip interface brief` (TextFSM format)
- `parse_static_routes()`: Parses `show ip route static`
- `parse_cpu_memory()`: Parses `show processes cpu` and `show memory`

## Frontend Integration

Frontend applications (React, etc.) can now:

1. **Display structured data**: Use the `data` field for rendering tables, charts, etc.
2. **Show raw output**: Use the `raw` field for debug mode or text display
3. **Handle errors**: Check for `status: "error"` in responses
4. **Expect consistent format**: All endpoints follow the same pattern

### Example Frontend Code

```javascript
// Fetch device health
const response = await fetch('/api/v1/monitoring/cisco-iosv-r1');
const data = await response.json();

// Access structured data
console.log(data.health.reachable); // boolean
console.log(data.health.resource.data.uptime); // "12h30m15s"
console.log(data.health.resource.raw); // Raw CLI output

// Display in React
function DeviceHealth({ deviceId }) {
  const { data, error } = useHealthQuery(deviceId);
  
  if (error) return <div>Error: {error}</div>;
  if (!data) return <div>Loading...</div>;
  
  return (
    <div>
      <h2>{data.hostname}</h2>
      <p>Uptime: {data.health?.resource?.data?.uptime}</p>
      <p>CPU: {data.cpu_memory?.data?.cpu?.['5sec']}</p>
    </div>
  );
}
```

## Testing

To test JSON responses:

```bash
# Test MikroTik health endpoint
curl http://localhost:8000/api/v1/mikrotik/mikrotik-chr-mk-1/health

# Test Cisco monitoring endpoint
curl http://localhost:8000/api/v1/monitoring/cisco-iosv-r1

# Test device list
curl http://localhost:8000/api/v1/devices
```

All responses should be valid JSON with Content-Type: application/json header.

## Backward Compatibility

The response format is backward compatible:
- Existing code that reads the `raw` field will continue to work
- New code can use the `data` field for structured access
- The monitoring endpoint handles both formats (with and without `data` key)

## Future Enhancements

- Add more parsers for additional CLI commands
- Improve error handling and validation
- Add OpenAPI schema definitions for better documentation
