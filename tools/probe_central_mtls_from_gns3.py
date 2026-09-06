import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env")
password = os.getenv("GNS3_VM_PASSWORD", "")
user = os.getenv("GNS3_VM_USERNAME", "gns3")
plink = r"C:\Program Files\PuTTY\plink.exe"
pscp = r"C:\Program Files\PuTTY\pscp.exe"
remote = f"{user}@172.21.0.2"
remote_dir = "/tmp/ainet-edge-live-pki"
files = [root / "tmp" / "edge-live-pki" / name for name in ("ca.crt", "edge-001.crt", "edge-001.key")]

mkdir = subprocess.run([plink, "-batch", "-ssh", "-pw", password, remote, f"mkdir -p {remote_dir}"], capture_output=True, text=True)
if mkdir.returncode:
    raise SystemExit(mkdir.stderr[:500])
for source in files:
    result = subprocess.run([pscp, "-batch", "-pw", password, str(source), f"{remote}:{remote_dir}/"], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stderr[:500])
command = (
    f"curl --silent --show-error --fail --max-time 15 --cacert {remote_dir}/ca.crt "
    f"--cert {remote_dir}/edge-001.crt --key {remote_dir}/edge-001.key "
    "-H 'Content-Type: application/json' -H 'X-Client-Edge-ID: edge-001' "
    "-d '{\"edge_id\":\"edge-001\",\"edge_version\":\"m1\",\"min_protocol_version\":1,\"max_protocol_version\":1,\"driver_capability_version\":1,\"capabilities\":[\"device.read.facts\"],\"boot_id\":\"gns3-live\"}' "
    "https://172.21.0.1:8443/api/v1/control/hello"
)
result = subprocess.run([plink, "-batch", "-ssh", "-pw", password, remote, command], capture_output=True, text=True)
print("central_mtls_from_gns3_vm=PASS" if result.returncode == 0 else "central_mtls_from_gns3_vm=FAIL")
print(result.stdout[-1000:])
if result.returncode:
    print(result.stderr[-500:])
