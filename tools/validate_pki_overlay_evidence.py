"""Fail-closed validator for PKI and private-overlay acceptance evidence."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    path = Path("docs/evidence/pki-overlay/zerotier-controller-ubuntu1-20260905.json")
    if not path.exists():
        print("PKI_OVERLAY_EVIDENCE=FAIL missing artifact")
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    deauth = data.get("deauthorization", {})
    cert = data.get("certificate_revocation", {})
    checks = {
        "controller": data.get("controller", {}).get("database_ready") is True,
        "overlay": data.get("overlay_connectivity", {}).get("status") == "PASS",
        "client_denial": deauth.get("client_denial_observed") is True,
        "central_revoke": cert.get("central_application_layer_status") == "PASS" and cert.get("hello_after_revoke_status") == 403,
        "tls_terminator": cert.get("production_terminator_integration") == "PASS",
    }
    if not all(checks.values()):
        missing = ",".join(name for name, passed in checks.items() if not passed)
        print(f"PKI_OVERLAY_EVIDENCE=FAIL incomplete:{missing}")
        return 1
    print("PKI_OVERLAY_EVIDENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
