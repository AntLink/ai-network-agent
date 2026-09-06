"""Fail-closed validator for the captured GNS3 overlap acceptance artifact."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    path = Path("docs/evidence/gns3-overlap/live-two-edge-proof-20260905.json")
    if not path.exists():
        print("GNS3_OVERLAP_EVIDENCE=FAIL missing artifact")
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", {})
    required_edges = ("edge_a", "edge_b")
    if data.get("status") != "PASS" or any(results.get(edge, {}).get("status") != "SUCCEEDED" for edge in required_edges):
        print("GNS3_OVERLAP_EVIDENCE=FAIL incomplete result")
        return 1
    if any(results[edge].get("management_ip") != "192.168.1.1" for edge in required_edges):
        print("GNS3_OVERLAP_EVIDENCE=FAIL management IP mismatch")
        return 1
    print("GNS3_OVERLAP_EVIDENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
