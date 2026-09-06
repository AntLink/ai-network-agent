import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
cmd = "sed -n '145,195p' /home/gns3/.venv/gns3server-venv/lib/python3.14/site-packages/gns3server/handlers/api/controller/template_handler.py; sed -n '560,610p' /home/gns3/.venv/gns3server-venv/lib/python3.14/site-packages/gns3server/controller/project.py"
r = subprocess.run([
    r"C:\\Program Files\\PuTTY\\plink.exe", "-batch", "-ssh", "-pw",
    os.getenv("GNS3_VM_PASSWORD", ""),
    f"{os.getenv('GNS3_VM_USERNAME','gns3')}@172.21.0.2", cmd,
], capture_output=True, text=True)
print(r.stdout, end="")
print(r.stderr[:500], end="")
