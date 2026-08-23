# CSMS Live Frequency Monitoring Client

Production-ready Python client for **TCI CSMS Spectrum Monitoring** (TCP 3302/3303) with live frequency monitoring capability.

## ✅ What Works (Verified Live)

| Feature | Status | Details |
|---------|--------|---------|
| **Greeting handshake** | ✅ | `cmdVer=1, respVer=1` → 4-byte session token |
| **Protocol framing** | ✅ Fixed | Length-prefixed (no `\n` delimiter - caused 1-byte shift bug) |
| **Version tables** | ✅ Mapped | MAP1 (IsBodyCompressed) + MAP2 (version check) at `0x1ad5c00/0x18` |
| **RetrieveMeasurement** | ✅ Working | `type 27, sub 71002, cmdVer=1, respVer=2` → `sub=72002` response |
| **ScheduleMeasurement** | ✅ Working | `type 27, sub 71000, cmdVer=5, respVer=2` |
| **Live spectrum data** | ✅ Verified | 40KB response, float64 sweep data extracted |

## Quick Start

```python
from csms_client import CSMSClient
import struct, time

c = CSMSClient("192.168.162.20", timeout=30)
c.connect()
c.greeting()  # gets session token

# Schedule measurement (100-200 MHz, 1MHz step, 100kHz RBW, 100ms dwell)
c.schedule_measurement(start_freq=100e6, stop_freq=200e6, step_freq=1e6, 
                       rbw=100e3, dwell_ms=100, sweep_type=1)

import time
time.sleep(3)  # wait for sweep

# Poll for result (respVer=2 required for response subtype 72002)
for mid in range(5590, 5620):
    resp = c.retrieve_measurement(measure_id=mid)
    if resp and resp.subtype == 0x1C22:  # 72002 = SGetMeasRespV5
        if resp.body_len > 10000:
            # Found spectrum data! Parse float64 sweep...
            break
```

## Key Protocol Constants

| Message Type | Value | Purpose |
|-------------|-------|---------|
| `GREETING_REQ` | 8565 | Start session, get token |
| `GREETING_RES` | 8566 | Returns 4-byte session token |
| `MEASURE_CTRL` | 27 | Measurement control (schedule, retrieve, etc.) |
| `PAN_REQ` | 8563 | Panoramic sweep request |

| Subtype (type 27) | Value | Purpose | cmdVer | respVer |
|------------------|-------|---------|--------|---------|
| `SCHEDULE_MEASUREMENT` | 71000 | Schedule new sweep | 5 | 2 |
| `RETRIEVE_MEASUREMENT` | 71002 | Retrieve sweep data | 1 | **2** |
| `RETRIEVE_IQ_DATA` | 71017 | IQ data | 1 | 1 |

**Critical:** `respVer=2` required for response subtype `72002` (SGetMeasRespV5), otherwise returns "Send compressed messages unsupported (27,72002)".

## Frame Format (No `\n` Delimiter!)

```
[20-byte header][body bodyLen bytes]
  +0x00 u32 marker (echoed in response)
  +0x04 u32 field4 (usually 0)
  +0x08 u16 msgType
  +0x0A u8  cmdVer
  +0x0B u8  respVer  
  +0x0C u32 subtype
  +0x10 u32 bodyLen
```

**⚠️ No `\n` delimiter!** Server uses pure length-prefixed framing. Sending `\n` shifts subsequent messages by 1 byte → "invalid message type" errors.

## Version Tables (RAM at `0x1ad5c00`)

Two maps control protocol behavior:
- **MAP1** (IsBodyCompressed): `(msgType, subtype) → (cmdVer_min, respVer_min)` — determines if body is "compressed"
- **MAP2** (Version Check): `(msgType, subtype) → (cmdVer_cur, respVer_cur)` — max supported versions

## Files

| File | Purpose |
|------|---------|
| `csms_client.py` | Main client class (no `\n`, correct versions) |
| `test_final.py` | Complete end-to-end test |
| `csms-bridge-armv7` | ARMv7 bridge binary for deployment |
| `build.sh` | Cross-compile script (`arm-linux-gnueabihf`) |

## Requirements

- Python 3.x
- Network access to CSMS device (default `192.168.162.20:3302`)
- Standard library only (no external dependencies)

## Deployment (ARMv7 Target)

```bash
./build.sh          # produces csms-bridge-armv7
scp csms-bridge-armv7 user@device:/usr/local/bin/
ssh user@device 'chmod +x /usr/local/bin/csms-bridge-armv7 && /usr/local/bin/csms-bridge-armv7'
```

## Documentation

Full protocol analysis: `README.md` (this file) + `CSMSD_RE_FINDINGS.md` (deep technical notes)