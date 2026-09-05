import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env", override=True)
project = "353d6f0d-2f10-4e2d-85e6-8e0ce2380412"
node = "84057c48-c0a0-4c36-80ad-1785a59ba42f"
vm_user = os.environ.get("GNS3_VM_USERNAME", "gns3")
vm_password = os.environ.get("GNS3_VM_PASSWORD", "")
remote = f"{vm_user}@172.21.0.2"
plink = r"C:\Program Files\PuTTY\plink.exe"
pscp = r"C:\Program Files\PuTTY\pscp.exe"
local_pki = root / "tmp" / "edge-live-pki"
remote_dir = f"/opt/gns3/projects/{project}/project-files/docker/{node}/runtime"
container_dir = "/gns3volumes/runtime"
host_key = "192.168.10.1 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCZXWC3EB4Vik7gZuShpSKZ2e0ZeKE1Gm1CXEwwmfwQJRsIjomAaAr8MHdutPodHPnLaTrqjWUQ1z6zShPBlX107SdCUIveSutwYV++SJdrkK9FxyrW87b09RBMWUlZY5d+5UjMpIngcyD5S2Y0CRIsTMwtpGI28aOVkgUEtcLjSN+LiiT7ZYa0vzxo/kR18VhP8wNu0DEVJyGHnD0Ct0XCEBrjV7xSIIIJVY9O3p1TGhzjX27CG7vgHUFGykvDrFz7yUl1Bt7VID0HVVHSOeoup9VyKjfTJCUfey1loKYEG53Wbmop26ESvuQlOkbS35YMojOEyODT1YXJaOeLjEjb"

def run_remote(command: str) -> None:
    result = subprocess.run([plink, "-batch", "-ssh", "-pw", vm_password, remote, command], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("GNS3 VM staging command failed")

run_remote(f"mkdir -p {remote_dir} && chmod 700 {remote_dir}")
for name in ("ca.crt", "edge-001.crt", "edge-001.key"):
    result = subprocess.run([pscp, "-batch", "-pw", vm_password, str(local_pki / name), f"{remote}:{remote_dir}/{name}"], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("GNS3 VM certificate staging failed")

with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
    json.dump({"r1-lab": {"username": os.environ.get("CISCO_ROUTER_USERNAME", "admin"), "password": os.environ.get("CISCO_ROUTER_PASSWORD", ""), "host_key": host_key}}, handle)
    keystore = Path(handle.name)
try:
    result = subprocess.run([pscp, "-batch", "-pw", vm_password, str(keystore), f"{remote}:{remote_dir}/keystore.json"], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("GNS3 VM keystore staging failed")
finally:
    keystore.unlink(missing_ok=True)

run_remote(f"chmod 600 {remote_dir}/ca.crt {remote_dir}/edge-001.crt {remote_dir}/edge-001.key {remote_dir}/keystore.json")

props = {
    "extra_volumes": ["/runtime"],
    "start_command": f"/ainet-edge --control-listen 0.0.0.0:9443 --edge-id edge-001 --ca-file {container_dir}/ca.crt --cert-file {container_dir}/edge-001.crt --key-file {container_dir}/edge-001.key --keystore-file {container_dir}/keystore.json",
}
data = json.dumps({"properties": props}).encode()
request = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/gns3/projects/{project}/nodes/{node}/properties",
    data=data,
    method="POST",
    headers={"Content-Type": "application/json", "X-Approved-By": "mohfa"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    response.read()
print("edge2_runtime_provisioned=PASS")
