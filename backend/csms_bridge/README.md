# csms-bridge

A lightweight Go HTTP bridge for passive CSMS spectrum monitoring. It taps device
traffic via `AF_PACKET` (no port binding, no interference with `csmsd`), reassembles
TCP streams for the CSMS protocols, decodes float sweeps, and exposes live spectrum
data over REST. Designed to run on ARMv7 embedded devices.

## Endpoints

| Method | Path                | Description                                          |
|--------|---------------------|------------------------------------------------------|
| GET    | `/health`           | Service liveness check                               |
| GET    | `/segments`         | Shared-memory segments discovered on the host        |
| GET    | `/spectrum`         | Decoded sweep from shared memory (legacy)            |
| GET    | `/spectrum/raw`     | Raw shared-memory bytes (octet-stream)               |
| GET    | `/spectrum/live`    | Latest captured packets/frames with decoded points   |
| GET    | `/spectrum/raw/udp` | Raw captured payloads as hex/text/binary (`?format=`)|
| GET    | `/spectrum/raw/live`| Alias of `/spectrum/raw/udp`                         |
| GET    | `/spectrum/status`  | Packet rate, last source, decode confidence          |

All responses are JSON with CORS headers enabled (`*`).

## Packet tap

The bridge sniffs the interface in promiscuous-raw mode (`AF_PACKET`, `ETH_P_ALL`) and
filters on these ports:

| Port | Proto | Protocol                  |
|------|-------|---------------------------|
| 18331| UDP   | spectrum datagram         |
| 5060 | UDP   | RTP audio (`csmsAudio`)   |
| 3302 | TCP   | SSmsMsg (CMetricsNet)     |
| 3303 | TCP   | SSmsMsg (VCP)             |
| 3307 | TCP   | CRealtimeNet (realtime)   |

UDP datagrams are captured whole. TCP payloads are reassembled into complete
application frames before decoding:

- `3307` CRealtimeNet: `[12B header][body]`, `bodyLen` u32 LE at offset 8.
- `3302/3303` SSmsMsg: `[20B header][body][0x0a]`, `bodyLen` u32 LE at offset 16.

## Running locally

Requires Go 1.21+.

```bash
go run .
```

The server listens on port **8080**.

Example:

```bash
curl http://localhost:8080/health
```

## Cross-compiling for ARMv7

```bash
chmod +x build.sh
./build.sh
```

This produces `csms-bridge-armv7`, a static Linux/ARM binary suitable for deployment on ARMv7 targets (e.g., Raspberry Pi, industrial gateways).

Deploy and run on the target:

```bash
scp csms-bridge-armv7 user@device:/usr/local/bin/
ssh user@device 'chmod +x /usr/local/bin/csms-bridge-armv7 && /usr/local/bin/csms-bridge-armv7'
```

## Testing

The TCP reassembler is covered by unit tests (`tcp_reasm_test.go`). On the Linux
target or any machine with Go installed:

```bash
go test -v tcp_reasm.go tcp_reasm_test.go
```

## Notes

- GPS/NTP/system handlers are still mocked; the spectrum endpoints are the live path.
- No external dependencies — standard library only.
- The SysV shared-memory readers in `main.go` are Linux-only (`SYS_SHMAT`/`SYS_SHMGET`),
  so `go test ./...` must run on Linux (or use the file-list form above).
