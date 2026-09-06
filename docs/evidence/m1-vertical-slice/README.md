# Milestone 1 — Vertical Slice Evidence

Proof that a Central client establishes an authenticated mTLS control session to
an enrolled Edge and executes one read-only capability against a live lab
device, returning a normalized structured result.

## Topology under test

```text
Central host (Windows, 172.21.0.1)
   |
   |  mTLS (TLS 1.3) outbound client -> Edge server
   v
Edge (Go ainet-edge, systemd on GNS3 VM 172.21.0.2, --control-listen 0.0.0.0:9443)
   |  edge-id=edge-001
   |  SSH (device.read.facts -> show version)
   v
R1 (Cisco IOSv, GigabitEthernet0/1 = 192.168.10.1/24)
```

## Evidence files

- `r1-facts-live-result-20260903.json` — full mTLS HELLO/READY/TASK run for
  `device.read.facts` against R1, including the normalized result.

## How the slice was exercised (protocol-level)

A Central-side mTLS client using `central.crt`/`central.key` (CLIENT_AUTH, signed
by the project dev CA) connected to the Edge and:

1. `POST /v1/control/hello` -> `200 WELCOME {session_id}` (Edge enrollment/auth)
2. `POST /v1/control/ready` -> `200 READY_ACK`
3. `POST /v1/control/task` with a `device.read.facts` envelope
   (`credential_ref=r1-lab`, `device_host=192.168.10.1`) -> `200` normalized result

The Edge resolved the `r1-lab` credential reference from its protected local
keystore, validated the pinned R1 SSH host key, ran `show version` over SSH, and
returned the normalized `vendor/platform/version/hostname` facts.

## Normalized result (subject)

| field | value |
|---|---|
| vendor | cisco |
| platform | ios |
| version | 15.6(2)T |
| hostname | R1 |
| uptime | 1 minute |
| image_file | flash0:/vios-adventerprisek9-m |

## Notes / limitations

- This run exercised the protocol client directly. Wiring the same dispatch
  through the FastAPI `POST /api/v1/tasks/capability` surface is tracked as the
  remaining API-integration step for Milestone 1.
- R1 `admin` SSH password was re-provisioned to the project `.env` value during
  this session because the prior stored secret did not match the lab device.
- Development-only PKI and lab credentials; no production claims.
