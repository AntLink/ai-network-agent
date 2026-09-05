import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env", override=True)
remote = f"{os.environ.get('GNS3_VM_USERNAME', 'gns3')}@172.21.0.2"
container = "2944b9611d72f2f257e02f9ea4fe6e88b1a64c020ec4318f94fd08d9db9e1254"
command = f"docker exec {container} /gns3/bin/busybox ip addr; echo __ROUTE__; docker exec {container} /gns3/bin/busybox ip route; echo __INSPECT__; docker inspect --format '{{{{json .HostConfig.NetworkMode}}}}|{{{{json .NetworkSettings.NetworkDisabled}}}}|{{{{json .NetworkSettings.EndpointID}}}}|{{{{json .HostConfig.Privileged}}}}|{{{{json .Config.Env}}}}|{{{{json .Config.Entrypoint}}}}|{{{{json .Config.Cmd}}}}|{{{{json .Mounts}}}}' {container}; echo __BRIDGE__; docker network inspect bridge --format '{{{{json .Containers}}}}'"
result = subprocess.run([r"C:\Program Files\PuTTY\plink.exe", "-batch", "-ssh", "-pw", os.environ.get("GNS3_VM_PASSWORD", ""), remote, command], capture_output=True, text=True)
print(result.stdout[-6000:])
if result.returncode:
    print(result.stderr[-1000:])
