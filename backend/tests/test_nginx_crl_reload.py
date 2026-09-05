from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from deploy.mtls.nginx_crl_reload import reload_if_changed, validate_crl


def _crl(path: Path, next_update: datetime) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-ca")])
    cert = (
        x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(1).not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    crl = x509.CertificateRevocationListBuilder().issuer_name(cert.subject).last_update(next_update - timedelta(hours=1)).next_update(next_update).sign(key, hashes.SHA256())
    path.write_bytes(crl.public_bytes(serialization.Encoding.PEM))


def test_reload_is_fail_closed_for_expired_crl():
    root = Path(tempfile.mkdtemp(prefix="nginx-crl-test-"))
    try:
        crl = root / "ca.crl"
        _crl(crl, datetime.now(timezone.utc) - timedelta(seconds=1))
        try:
            validate_crl(crl)
        except ValueError as exc:
            assert "expired" in str(exc)
        else:
            raise AssertionError("expired CRL must be rejected")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_reload_runs_config_test_and_reload_once():
    root = Path(tempfile.mkdtemp(prefix="nginx-crl-test-"))
    try:
        crl = root / "ca.crl"
        state = root / "crl.sha256"
        _crl(crl, datetime.now(timezone.utc) + timedelta(hours=1))
        with patch("deploy.mtls.nginx_crl_reload.subprocess.run") as run:
            assert reload_if_changed(crl_path=crl, hash_path=state, nginx_bin="nginx") == "RELOADED"
            assert [call.args[0] for call in run.call_args_list] == [["nginx", "-t"], ["nginx", "-s", "reload"]]
        with patch("deploy.mtls.nginx_crl_reload.subprocess.run") as run:
            assert reload_if_changed(crl_path=crl, hash_path=state, nginx_bin="nginx") == "UNCHANGED"
            run.assert_not_called()
    finally:
        shutil.rmtree(root, ignore_errors=True)
