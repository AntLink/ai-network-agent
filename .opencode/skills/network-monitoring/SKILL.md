---
name: network-monitoring
description: Collect and present real‑time operational metrics from network devices.
compatibility: OpenCode
---

# Network Monitoring

Collect read‑only monitoring data for dashboards and alerts.

## Metrics Collected
- CPU utilization
- Memory usage
- Interface status, bandwidth, packet errors, packet drops
- Latency (via ping from device)
- Uptime
- Service status (SSH, HTTP, API, etc.)
- Temperature (if supported)

## Tools Used
- `device_get_monitoring` – fetches aggregated metrics.
- `device_get_interfaces` – detailed interface statistics.

## Schedule
- Monitoring is typically performed on a schedule (cron/job) but can be triggered on-demand via the `network-troubleshooter` or `network-auditor`.
