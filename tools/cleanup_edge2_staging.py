import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env", override=True)
remote = f"{os.environ.get('GNS3_VM_USERNAME', 'gns3')}@172.21.0.2"
target = "/opt/gns3/projects/353d6f0d-2f10-4e2d-85e6-8e0ce2380412/project-files/docker/84057c48-c0a0-4c36-80ad-1785a59ba42f/runtime"
result = subprocess.run([r"C:\Program Files\PuTTY\plink.exe", "-batch", "-ssh", "-pw", os.environ.get("GNS3_VM_PASSWORD", ""), remote, f"rm -rf -- {target}"], capture_output=True, text=True)
if result.returncode:
    raise SystemExit("cleanup failed")
print("edge2_staging_cleanup=PASS")
