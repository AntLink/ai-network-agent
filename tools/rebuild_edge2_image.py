import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env", override=True)
vm_user = os.environ.get("GNS3_VM_USERNAME", "gns3")
vm_password = os.environ.get("GNS3_VM_PASSWORD", "")
remote = f"{vm_user}@172.21.0.2"
plink = r"C:\Program Files\PuTTY\plink.exe"
pscp = r"C:\Program Files\PuTTY\pscp.exe"
build_dir = "/tmp/ainet-edge-build"
local_bin = root / "tmp" / "ainet-edge-linux"
local_bin.parent.mkdir(exist_ok=True)
subprocess.run(["go", "build", "-o", str(local_bin), "./cmd/ainet-edge"], cwd=root / "edge", check=True)
subprocess.run([plink, "-batch", "-ssh", "-pw", vm_password, remote, f"rm -rf {build_dir} && mkdir -p {build_dir}"], check=True, capture_output=True, text=True)
for source in (local_bin, root / "edge" / "Dockerfile"):
    result = subprocess.run([pscp, "-batch", "-pw", vm_password, str(source), f"{remote}:{build_dir}/"], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("edge build staging failed")
result = subprocess.run([plink, "-batch", "-ssh", "-pw", vm_password, remote, f"docker build --tag ainet-edge:lab {build_dir}"], capture_output=True, text=True)
if result.returncode:
    print(result.stdout[-1000:])
    print(result.stderr[-1000:])
    raise SystemExit("remote edge image build failed")
print("edge_image_rebuild=PASS")
