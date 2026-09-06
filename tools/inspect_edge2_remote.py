import json
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env", override=True)
remote = f"{os.environ.get('GNS3_VM_USERNAME', 'gns3')}@172.21.0.2"
container = "2944b9611d72f2f257e02f9ea4fe6e88b1a64c020ec4318f94fd08d9db9e1254"
cmd = f"docker inspect --format '{{{{json .State}}}}|{{{{json .NetworkSettings}}}}' {container}; echo __LOG__; docker logs --tail 40 {container}; echo __IMAGES__; docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}}'"
result = subprocess.run([r"C:\Program Files\PuTTY\plink.exe", "-batch", "-ssh", "-pw", os.environ.get("GNS3_VM_PASSWORD", ""), remote, cmd], capture_output=True, text=True)
if result.returncode:
    raise SystemExit("docker inspect failed")
if "; echo __LOG__; " not in result.stdout:
    print(result.stdout[-5000:])
    raise SystemExit("unexpected remote inspect output")
first, rest = result.stdout.strip().split("; echo __LOG__; ", 1)
state_text, network_text = first.split("|", 1)
logs, images = rest.split("; echo __IMAGES__; ", 1)
print(json.dumps({"state": json.loads(state_text), "network": json.loads(network_text), "logs": logs[-2000:], "images": images.splitlines()}, separators=(",", ":")))
