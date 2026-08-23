---
name: network-security
description: Defensive configuration audits and security reviews.
compatibility: OpenCode
---

# Network Security (Audit)

Use for security auditing of authorized devices.

## Audit Areas
- exposed management services (Telnet, HTTP, SNMP)
- SSH configuration (version, ciphers, key exchange)
- insecure protocols (SNMPv1/v2, FTP, HTTP)
- firewall/ACL posture
- unnecessary services
- weak or excessive access rules
- outdated software/version indicators
- risky routing/NAT
- management-plane exposure
- logging/monitoring posture
- user/AAA configuration

## Rules
- Default to read-only.
- Do not exploit vulnerabilities.
- Do not brute-force credentials.
- Do not bypass authentication.
- Report evidence and remediation steps.

## Output (per finding)
- severity (Critical/High/Medium/Low/Info)
- affected device
- evidence (exact tool output)
- explanation
- recommended remediation
- estimated impact
- verification method
