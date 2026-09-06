"""Fail-closed validation for release SBOM, scan, and signing evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    gap_path = root / "docs/evidence/release-readiness/sbom-gap-20260906.json"
    manifest_path = root / "docs/production/release-manifest.template.json"
    if not gap_path.exists():
        return [f"missing evidence: {gap_path}"]
    if not manifest_path.exists():
        return [f"missing release manifest: {manifest_path}"]

    gap = load_json(gap_path)
    manifest = load_json(manifest_path)
    if gap.get("secrets_logged") is not False:
        errors.append("SBOM evidence secret-safety flag is not false")

    for key in ("security_scan", "edge_security_scan"):
        scan = gap.get(key)
        if not isinstance(scan, dict):
            errors.append(f"missing {key}")
            continue
        if scan.get("status") != "PASS_FOR_SCANNED_HIGH_CRITICAL_SCOPE":
            errors.append(f"{key} is not a passing candidate scan")
        if scan.get("vulnerabilities") != []:
            errors.append(f"{key} contains vulnerability findings")
        artifact = scan.get("artifact")
        if not artifact or not (root / artifact).exists():
            errors.append(f"missing scan artifact for {key}")

    for item in gap.get("sbom_artifacts", []):
        if not isinstance(item, dict) or not item.get("path"):
            errors.append("malformed SBOM artifact entry")
            continue
        if not (root / item["path"]).exists():
            errors.append(f"missing SBOM artifact: {item['path']}")

    edge_artifact = gap.get("edge_artifact", {})
    if edge_artifact.get("status") != "SIGNED_RELEASE_ARTIFACT":
        errors.append("Edge artifact is not a signed release artifact")

    release = manifest.get("release", {})
    for key in ("version", "git_commit", "licensing_decision"):
        value = release.get(key)
        if not value or str(value).startswith("<CONFIGURE"):
            errors.append(f"release manifest {key} is not approved/configured")

    artifacts = manifest.get("artifacts", {})
    if str(artifacts.get("central_image", "")).startswith("<CONFIGURE"):
        errors.append("central image digest is not approved/configured")
    sbom = manifest.get("sbom", {})
    if str(sbom.get("sha256", "")).startswith("<CONFIGURE"):
        errors.append("SBOM hash is not approved/configured")
    if manifest.get("production_ready") is not True:
        errors.append("release manifest is not marked production_ready")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        print("RELEASE_EVIDENCE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RELEASE_EVIDENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
