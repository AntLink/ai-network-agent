# GNS3 Overlap Evidence

Required evidence: Edge A and Edge B reach separate lab devices that both use
`192.168.1.1`, with tenant-scoped routing and normalized `device.read.facts`
results.

Live evidence: `live-two-edge-proof-20260905.json` (`PASS`). Edge-001 reaches
IOSv1/R1 and Edge-B reaches IOSv2/R2 through separate LANs, despite the
identical management IP.
