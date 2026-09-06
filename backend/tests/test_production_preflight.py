"""Milestone 4: production host preflight gate checker contract tests."""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PATH = REPO_ROOT / "deploy" / "production" / "preflight.py"

_spec = importlib.util.spec_from_file_location("ainet_preflight", PREFLIGHT_PATH)
assert _spec and _spec.loader
preflight = importlib.util.module_from_spec(_spec)
sys.modules["ainet_preflight"] = preflight
_spec.loader.exec_module(preflight)


@pytest.fixture
def pf_tmp():
    d = Path(tempfile.mkdtemp(prefix="ainet-pf-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)

DOMAIN = "example.antlinx.com"
MEM_OK = (
    "MemTotal:       8388608 kB\n"
    "MemFree:        4194304 kB\n"
    "SwapTotal:       524288 kB\n"
    "SwapFree:        524288 kB\n"
)
MEM_LOW = "MemTotal:       3145728 kB\nMemFree: 1048576 kB\nSwapTotal: 2097152 kB\nSwapFree: 0 kB\n"
SS_NGINX = "LISTEN 0 511 0.0.0.0:443 0.0.0.0:*    users:((\"nginx\",pid=1,fd=8))\n"


def _inputs(pf_tmp, **kw):
    manifest = pf_tmp / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "artifacts": {
                    "central_image": f"ghcr.io/antlink/ainet-api:v0.1.0@sha256:{'a' * 64}",
                    "edge_image": f"ghcr.io/antlink/ainet-edge:v0.1.0@sha256:{'b' * 64}",
                }
            }
        ),
        encoding="utf-8",
    )
    cert = pf_tmp / "cert.pem"
    cert.write_text("dummy", encoding="utf-8")
    policy = pf_tmp / "revocation-policy.md"
    policy.write_text("# Revocation policy\n", encoding="utf-8")
    defaults = dict(
        docker_bin="docker",
        openssl_bin="openssl",
        hostname=DOMAIN,
        tls_cert=str(cert),
        manifest_path=str(manifest),
        revocation_policy=str(policy),
        licensing_ref="LIC-2026-09-06-001-COMMERCIAL",
        ss_text=SS_NGINX,
        meminfo_text=MEM_OK,
    )
    defaults.update(kw)
    return preflight.PreflightInputs(**defaults)


def _full_pass_runner():
    def runner(args, timeout=20):
        if args[0] == "docker":
            if args[1] == "info":
                return (0, "")
            if args[1] == "ps":
                return (0, "nginx\nredis-stack\n")
            if args[1] == "manifest":
                return (0, "")
        if args[0] == "openssl":
            if "checkend" in args:
                return (0, "")
            return (0, f"DNS:{DOMAIN}")
        return (0, "")

    return runner


def test_load_manifest_missing_raises(pf_tmp):
    with pytest.raises(FileNotFoundError):
        preflight.load_manifest(str(pf_tmp / "nope.json"))


def test_load_manifest_no_artifacts_raises(pf_tmp):
    path = pf_tmp / "m.json"
    path.write_text(json.dumps({"release": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="artifacts"):
        preflight.load_manifest(str(path))


def test_image_refs_from_manifest():
    manifest = {
        "artifacts": {
            "central_image": "ghcr.io/antlink/ainet-api:v0.1.0@sha256:abcd",
            "edge_image": "ghcr.io/antlink/ainet-edge:v0.1.0@sha256:ef01",
        }
    }
    assert preflight.image_refs_from_manifest(manifest) == [
        "ghcr.io/antlink/ainet-api:v0.1.0@sha256:abcd",
        "ghcr.io/antlink/ainet-edge:v0.1.0@sha256:ef01",
    ]


def test_parse_image_ref_with_digest():
    registry, image, tag, digest = preflight.parse_image_ref(
        "ghcr.io/antlink/ainet-api:v0.1.0@sha256:abcd"
    )
    assert (registry, image, tag, digest) == (
        "ghcr.io",
        "antlink/ainet-api",
        "v0.1.0",
        "sha256:abcd",
    )


@pytest.mark.parametrize(
    "name,expected",
    [
        ("edge-control.antlinx.com", True),
        ("", False),
        ("with space.example.com", False),
        ("bad/name.com", False),
    ],
)
def test_hostname_valid(name, expected):
    assert preflight.hostname_valid(name) is expected


@pytest.mark.parametrize(
    "ref,expected",
    [
        ("LIC-2026-09-06-001-COMMERCIAL", True),
        ("", False),
        ("CC-2026-09-06-001-COMMERCIAL", False),
    ],
)
def test_licensing_ref_valid(ref, expected):
    assert preflight.licensing_ref_valid(ref) is expected


def test_listeners_from_ss():
    listeners = preflight.listeners_from_ss(
        "LISTEN 0 511 0.0.0.0:443 0.0.0.0:*    users:((\"nginx\",pid=1,fd=8))\n"
"LISTEN 0 4096 0.0.0.0:22 0.0.0.0:*    users:((\"sshd\",pid=2,fd=3))\n"
    )
    assert (443, "LISTEN", 'users:(("nginx",pid=1,fd=8))') in listeners
    assert (22, "LISTEN", 'users:(("sshd",pid=2,fd=3))') in listeners


def test_check_listeners_preserves_nginx_443():
    ok, msg, conflicts = preflight.check_listeners(SS_NGINX)
    assert ok is True
    assert conflicts == []
    assert "443" in msg
    assert "nginx" in msg


def test_check_listeners_conflict_on_ainet_port():
    text = SS_NGINX + "LISTEN 0 4096 0.0.0.0:8000 0.0.0.0:*    users:((\"java\",pid=9,fd=5))\n"
    ok, msg, conflicts = preflight.check_listeners(text)
    assert ok is False
    assert conflicts == [8000]


def test_memory_check_ok():
    status, msg = preflight.memory_check(MEM_OK)
    assert status == "PASS"
    assert "8388608" not in msg


def test_memory_check_low_warns():
    status, msg = preflight.memory_check(MEM_LOW)
    assert status == "WARN"


def test_memory_check_critical_fails():
    status, _ = preflight.memory_check("MemTotal:       1048576 kB\nMemFree: 0 kB\n")
    assert status == "FAIL"


def test_tls_cert_check_missing_fails(pf_tmp):
    status, msg = preflight.tls_cert_check(str(pf_tmp / "nope.pem"), DOMAIN, "openssl")
    assert status == "FAIL"
    assert "missing" in msg


def test_unreadable_container_inventory_fails_closed(monkeypatch):
    monkeypatch.setattr(preflight, "run_cmd", lambda *args, **kwargs: (1, ""))
    results = preflight.run_preflight(
        preflight.PreflightInputs(
            docker_bin="docker",
            openssl_bin="openssl",
            hostname="",
            tls_cert="",
            manifest_path="missing.json",
            revocation_policy="missing.md",
            licensing_ref="",
            ss_text=SS_NGINX,
            meminfo_text=MEM_OK,
        )
    )
    by_id = {gate["id"]: gate["status"] for gate in results["gates"]}
    assert by_id["no-existing-ainet"] == "FAIL"


def test_run_preflight_full_pass(monkeypatch, pf_tmp):
    monkeypatch.setattr(preflight, "run_cmd", _full_pass_runner())
    results = preflight.run_preflight(_inputs(pf_tmp))
    assert results["verdict"] == "READY"
    assert results["exit_code"] == 0


def test_run_preflight_not_ready_when_gates_missing(monkeypatch, pf_tmp):
    monkeypatch.setattr(preflight, "run_cmd", _fully_failing_runner())
    results = preflight.run_preflight(_inputs(pf_tmp, hostname="", licensing_ref=""))
    assert results["verdict"] == "NOT-READY"
    by_id = {g["id"]: g["status"] for g in results["gates"]}
    assert by_id["hostname-required"] == "FAIL"
    assert by_id["licensing-reference"] == "FAIL"
    assert by_id["docker-active"] == "FAIL"


def test_run_preflight_manifest_missing_blocks_registry(monkeypatch, pf_tmp):
    monkeypatch.setattr(preflight, "run_cmd", _full_pass_runner())
    results = preflight.run_preflight(
        _inputs(pf_tmp, manifest_path=str(pf_tmp / "missing.json"))
    )
    by_id = {g["id"]: g["status"] for g in results["gates"]}
    assert by_id["registry-feed-auth"] == "FAIL"
    assert results["verdict"] == "NOT-READY"


def test_run_preflight_registry_requires_immutable_digest(monkeypatch, pf_tmp):
    monkeypatch.setattr(preflight, "run_cmd", _full_pass_runner())
    manifest = pf_tmp / "tag-only.json"
    manifest.write_text(
        json.dumps({"artifacts": {"central_image": "ghcr.io/antlink/ainet-api:latest"}}),
        encoding="utf-8",
    )
    results = preflight.run_preflight(_inputs(pf_tmp, manifest_path=str(manifest)))
    by_id = {g["id"]: g["status"] for g in results["gates"]}
    assert by_id["registry-feed-auth"] == "FAIL"


def _fully_failing_runner():
    def runner(args, timeout=20):
        if args and args[-1] == "info":
            return (1, "")
        return (127, "")

    return runner
