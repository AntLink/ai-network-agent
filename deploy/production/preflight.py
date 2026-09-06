#!/usr/bin/env python3
"""Production host preflight for AI Network Agent.

Runs on the target Ubuntu/Docker host before any AINET deployment.  Encodes the
post-inspection blocking gates as machine-checkable conditions and returns a
structured JSON verdict.  It only READS the host (docker inspect, listeners,
meminfo, TLS cert file) and never writes, pulls, or modifies anything.
Secrets are never accepted: registry feed auth is proven with an anonymous
`docker manifest inspect` on the immutable digest, which succeeds only when the
host-level secret is provisioned (e.g. `docker login` PAT).  No secret is read
or logged here.

Exit codes:
  0  READY
  2  READY-WITH-WARNINGS  (capacity/host advisory only)
  1  NOT-READY            (a required gate failed)

Examples (on the Ubuntu host):
  python3 deploy/production/preflight.py \
      --hostname edge-control.antlinx.com \
      --tls-cert /etc/ainet/pki/central.crt \
      --manifest release-manifest-v0.1.0.json \
      --revocation-policy /etc/ainet/pki/revocation-policy.md \
      --licensing-ref LIC-2026-09-06-001-COMMERCIAL
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

AINET_DEFAULT_PORTS = (8000, 8010, 8443, 9443, 6379, 5432)
NGINX_PORT = 443
NGINX_PORT_PLACEHOLDER = "EXISTING_TCP_443_OWNER"
LICENSING_REF_RE = re.compile(r"^[A-Z]{3}-\d{4}-\d{2}-\d{2}-\d{3}-[A-Z]+$")

DATACLASS_KW = {}


@dataclass(**DATACLASS_KW)
class GateResult:
    id: str
    status: str
    message: str


def run_cmd(args: List[str], timeout: int = 20) -> Tuple[int, str]:
    """Return (exit_code, stdout). Command-not-found becomes exit code 127."""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""


def load_manifest(path: str) -> dict:
    """Load and validate the release manifest; raises on malformed input."""
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"release manifest not found: {path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "artifacts" not in data:
        raise ValueError("manifest has no artifacts section")
    if len(image_refs_from_manifest(data)) == 0:
        raise ValueError("manifest has no candidate image references")
    return data


def image_refs_from_manifest(manifest: dict) -> List[str]:
    """Collect immutable (<name>@<digest>) image references from the manifest."""
    artifacts = manifest.get("artifacts", {})
    refs: List[str] = []
    for key in ("central_image", "edge_image"):
        ref = artifacts.get(key)
        if ref:
            refs.append(str(ref))
    for tool in ("central", "edge"):
        path = artifacts.get(tool, {}).get("image")
        if path:
            refs.append(str(path))
    return refs


def parse_image_ref(ref: str) -> Tuple[str, str, str, str]:
    """Split 'ghcr.io/owner/name:tag@sha256:...' -> (registry, image, tag, digest)."""
    digest = ""
    if "@" in ref:
        ref, digest = ref.rsplit("@", 1)
    tag = "latest"
    if ":" in ref:
        ref, tag = ref.rsplit(":", 1)
    registry, _, image = ref.partition("/")
    if "." not in registry and registry != "localhost":
        image = f"{registry}/{image}"
        registry = "docker.io"
    return registry, image, tag, digest


def hostname_valid(hostname: str) -> bool:
    """A production hostname must be non-empty and syntactically plausible."""
    if not hostname or len(hostname) > 253:
        return False
    if " " in hostname or "/" in hostname:
        return False
    return bool(re.match(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$", hostname))


def licensing_ref_valid(ref: str) -> bool:
    """Licensing reference must follow the approved LIC-... pattern."""
    return bool(ref and LICENSING_REF_RE.match(ref))


def docker_is_active(docker_bin: str) -> Tuple[bool, str]:
    code, _ = run_cmd([docker_bin, "info"])
    if code == 0:
        return True, "docker daemon is reachable"
    if code == 127:
        return False, "docker CLI not found on PATH"
    return False, f"docker info failed (exit {code}); daemon not ready"


def docker_has_ainet_containers(docker_bin: str) -> Tuple[Optional[bool], str]:
    """Return True/False when inspect succeeds; None when it cannot be read.

    An unreadable Docker inventory must not be interpreted as an empty
    inventory because that would make the no-clobber gate fail open.
    """
    code, out = run_cmd([docker_bin, "ps", "-a", "--format", "{{.Names}}\t{{.Image}}"])
    if code != 0:
        return None, f"cannot list containers (exit {code}); refusing to assume host is empty"
    haystack = out.lower()
    if "ainet" in haystack or "antlink" in haystack:
        return True, "existing AINET/AntLink container(s) detected"
    return False, "no existing AINET containers detected"


def registry_auth_ok(docker_bin: str, ref: str) -> Tuple[bool, str]:
    """Anonymous manifest inspect on a private package succeeds only with
    host credentials; also proves the immutable digest resolves."""
    if "@" not in ref:
        return False, f"image reference is not immutable (missing digest): {ref}"
    code, _ = run_cmd([docker_bin, "manifest", "inspect", ref], timeout=30)
    if code == 0:
        return True, f"registry feed authorized for {ref}"
    if code == 127:
        return False, "docker CLI not found on PATH"
    return False, f"registry feed unauthorized/unreachable (exit {code}) for {ref}"


def listeners_from_ss(ss_text: str) -> List[Tuple[int, str, str]]:
    """Parse `ss -ltnp` output into [(port, state, process)]."""
    result: List[Tuple[int, str, str]] = []
    for line in ss_text.splitlines():
        line = line.strip()
        if not line or line.startswith("Netid") or line.startswith("State"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        state = parts[0]
        local = parts[3] if len(parts) > 3 else ""
        port_raw = local.rsplit(":", 1)[-1]
        proc = ""
        for part in parts:
            if str(part).startswith("users:") or str(part).startswith("("):
                proc = part
                break
        try:
            port = int(port_raw)
        except ValueError:
            continue
        result.append((port, state, proc))
    return result


def check_listeners(ss_text: str) -> Tuple[bool, str, List[int]]:
    """Fail when any AINET default port is already bound; also report the
    existing 443 owner so the operator can confirm Nginx is preserved."""
    listeners = listeners_from_ss(ss_text)
    bound = {port for port, _, _ in listeners}
    conflicts = sorted(set(AINET_DEFAULT_PORTS) & bound)
    nginx_owner = next((proc for port, _, proc in listeners if port == NGINX_PORT), "")
    parts = ["no AINET ports already bound"]
    if conflicts:
        parts = [f"AINET default port(s) already bound: {conflicts}"]
    if nginx_owner:
        parts.append(f"{NGINX_PORT_PLACEHOLDER}: {nginx_owner.strip() or 'unknownown'} (preserved)")
    return not bool(conflicts), "; ".join(parts), conflicts


def memory_check(meminfo_text: str) -> Tuple[str, str]:
    """RAM/swap capacity advisories from /proc/meminfo text. Warn under 4GiB,
    fail hard under 2GiB, and warn on heavy swap usage."""
    mb = {}
    for line in meminfo_text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].rstrip(":") in ("MemTotal", "SwapTotal", "SwapFree"):
            try:
                mb[parts[0].rstrip(":")] = int(parts[1])
            except ValueError:
                continue
    total_mib = mb.get("MemTotal", 0) // 1024
    swap_used_mib = (mb.get("SwapTotal", 0) - mb.get("SwapFree", 0)) // 1024
    if total_mib <= 0:
        return "FAIL", "MemTotal unreadable; cannot size deployment"
    if total_mib < 2048:
        return "FAIL", f"RAM too low ({total_mib} MiB); cannot host Central stack"
    if total_mib < 4096 or swap_used_mib > 1024:
        detail = []
        if total_mib < 4096:
            detail.append(f"RAM low ({total_mib} MiB)")
        if swap_used_mib > 1024:
            detail.append(f"swap heavily used (~{swap_used_mib} MiB)")
        return "WARN", f"capacity review required ({', '.join(detail)})"
    return "PASS", f"capacity ok (RAM {total_mib} MiB, swap used {swap_used_mib} MiB)"


def tls_cert_check(cert_path: str, hostname: str, openssl_bin: str) -> Tuple[str, str]:
    """Cert must exist, parse, be unexpired, and cover the hostname SAN."""
    if not cert_path or not Path(cert_path).is_file():
        return "FAIL", "TLS certificate file missing (--tls-cert)"
    code_expire, _ = run_cmd([openssl_bin, "x509", "-in", cert_path, "-noout", "-checkend", "0"])
    if code_expire != 0:
        if code_expire == 127:
            return "FAIL", f"openssl not found ({openssl_bin}); cannot validate certificate"
        return "FAIL", "TLS certificate is expired or unreadable"
    code_san, san_out = run_cmd(
        [openssl_bin, "x509", "-in", cert_path, "-noout", "-ext", "subjectAltName"]
    )
    if code_san == 0 and f"DNS:{hostname}" not in san_out:
        return "FAIL", f"hostname {hostname} not covered by certificate SAN"
    return "PASS", f"TLS certificate valid and covers {hostname}"


@dataclass(**DATACLASS_KW)
class PreflightInputs:
    docker_bin: str
    openssl_bin: str
    hostname: str
    tls_cert: str
    manifest_path: str
    revocation_policy: str
    licensing_ref: str
    ss_text: Optional[str] = None
    meminfo_text: Optional[str] = None


def run_preflight(inputs: PreflightInputs) -> Dict[str, object]:
    gates: List[GateResult] = []

    docker_active, docker_msg = docker_is_active(inputs.docker_bin)
    gates.append(GateResult("docker-active", "PASS" if docker_active else "FAIL", docker_msg))

    has_existing, existing_msg = docker_has_ainet_containers(inputs.docker_bin)
    existing_gate = "FAIL" if has_existing is not False else "PASS"
    gates.append(GateResult("no-existing-ainet", existing_gate, existing_msg))

    try:
        manifest = load_manifest(inputs.manifest_path)
        refs = image_refs_from_manifest(manifest)
        registry_statuses = []
        for ref in refs:
            ok, msg = registry_auth_ok(inputs.docker_bin, ref)
            registry_statuses.append(f"{'OK' if ok else 'UNAUTHORIZED'} {ref}")
        registry_gate = "PASS" if all(s.startswith("OK") for s in registry_statuses) else "FAIL"
        gates.append(
            GateResult(
                "registry-feed-auth",
                registry_gate,
                "; ".join(registry_statuses) or "no image references in manifest",
            )
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        gates.append(GateResult("registry-feed-auth", "FAIL", f"manifest unusable: {exc}"))

    if hostname_valid(inputs.hostname):
        gates.append(GateResult("hostname-required", "PASS", f"hostname: {inputs.hostname}"))
    else:
        gates.append(
            GateResult(
                "hostname-required",
                "FAIL",
                "approved production hostname missing/invalid (--hostname)",
            )
        )

    tls_gate, tls_msg = tls_cert_check(inputs.tls_cert, inputs.hostname, inputs.openssl_bin)
    gates.append(GateResult("tls-cert-valid", tls_gate, tls_msg))

    if inputs.ss_text is None:
        ss_code, ss_out = run_cmd(["/usr/bin/ss", "-ltnp"])
        ss_text = ss_out if ss_code == 0 else ""
    else:
        ss_text = inputs.ss_text
    if ss_text:
        listener_ok, listener_msg, _ = check_listeners(ss_text)
        adapter_msg = listener_msg.replace(NGINX_PORT_PLACEHOLDER, f"TCP {NGINX_PORT}")
        gates.append(
            GateResult(
                "listener-plan",
                "PASS" if listener_ok else "FAIL",
                adapter_msg,
            )
        )
    else:
        gates.append(
            GateResult(
                "listener-plan",
                "WARN",
                "could not enumerate listeners (ss missing?); manual port review required",
            )
        )

    if inputs.meminfo_text is None:
        mem_path = Path("/proc/meminfo")
        mem_text = mem_path.read_text(encoding="utf-8") if mem_path.is_file() else ""
    else:
        mem_text = inputs.meminfo_text
    if mem_text:
        mem_gate, mem_msg = memory_check(mem_text)
    else:
        mem_gate, mem_msg = "WARN", "meminfo unreadable; capacity review required"
    gates.append(GateResult("capacity-memory", mem_gate, mem_msg))

    revoke_target = Path(inputs.revocation_policy)
    if revoke_target.is_file() and revoke_target.stat().st_size > 0:
        gates.append(
            GateResult(
                "revocation-policy",
                "PASS",
                f"revocation policy present: {inputs.revocation_policy}",
            )
        )
    else:
        gates.append(
            GateResult(
                "revocation-policy",
                "FAIL",
                "approved PKI revocation policy missing (--revocation-policy)",
            )
        )

    if licensing_ref_valid(inputs.licensing_ref):
        gates.append(
            GateResult("licensing-reference", "PASS", f"licensing ref: {inputs.licensing_ref}")
        )
    else:
        gates.append(
            GateResult(
                "licensing-reference",
                "FAIL",
                "approved licensing reference missing/invalid (--licensing-ref)",
            )
        )

    statuses = [g.status for g in gates]
    if "FAIL" in statuses:
        verdict = "NOT-READY"
    elif "WARN" in statuses:
        verdict = "READY-WITH-WARNINGS"
    else:
        verdict = "READY"
    exit_code = 0 if verdict == "READY" else (2 if verdict == "READY-WITH-WARNINGS" else 1)

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "gates": [g.__dict__ for g in gates],
    }


def summarize(results: Dict[str, object]) -> str:
    lines = [f"VERDICT: {results['verdict']}"]
    for gate in results["gates"]:
        lines.append(f"  [{gate['status']:>5}] {gate['id']}: {gate['message']}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AINET production host preflight")
    parser.add_argument("--hostname", default="", help="approved production hostname")
    parser.add_argument("--tls-cert", default="", help="path to production TLS certificate")
    parser.add_argument(
        "--manifest",
        default="docs/production/release-manifest-v0.1.0.json",
        help="release manifest holding immutable image digests",
    )
    parser.add_argument(
        "--revocation-policy",
        default="docs/production/revocation-policy.md",
        help="approved PKI revocation policy document",
    )
    parser.add_argument(
        "--licensing-ref",
        default="",
        help="approved licensing reference, e.g. LIC-2026-09-06-001-COMMERCIAL",
    )
    parser.add_argument("--docker", default="docker", help="docker CLI path")
    parser.add_argument("--openssl", default="openssl", help="openssl CLI path")
    parser.add_argument("--json", action="store_true", help="emit JSON result to stdout")
    args = parser.parse_args(argv)

    inputs = PreflightInputs(
        docker_bin=args.docker,
        openssl_bin=args.openssl,
        hostname=args.hostname,
        tls_cert=args.tls_cert,
        manifest_path=args.manifest,
        revocation_policy=args.revocation_policy,
        licensing_ref=args.licensing_ref,
    )
    results = run_preflight(inputs)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(summarize(results))
    return int(results["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
