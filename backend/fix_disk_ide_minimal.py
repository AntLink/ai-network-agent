"""Retry minimal PUT hda_disk_interface=ide lalu start kedua switch."""
import base64
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:3080/v2"
USER = "admin"
with open(r"C:\Users\mohfa\AppData\Roaming\GNS3\2.2\gns3_server.ini",
          encoding="utf-8") as f:
    PW = ""
    for line in f:
        if line.strip().startswith("password"):
            PW = line.split("=", 1)[1].strip()
TOKEN = base64.b64encode(f"{USER}:{PW}".encode()).decode()


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Basic " + TOKEN)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        print("   HTTP", e.code, e.read().decode(errors="replace")[:200])
        return None


PID = "a6967457-f60e-4752-be8f-6b66e925245c"
nodes = api("GET", f"/projects/{PID}/nodes")
sw = {n["name"]: n["node_id"] for n in nodes if n["name"] in ("SW1", "SW2")}

for name, nid in sw.items():
    print("===", name, "===")
    st = api("GET", f"/projects/{PID}/nodes/{nid}")
    cur = st["properties"].get("hda_disk_interface")
    status = st["status"]
    print("   iface:", cur, "| status:", status)
    if cur != "ide":
        if status != "stopped":
            api("POST", f"/projects/{PID}/nodes/{nid}/stop")
            for _ in range(45):
                time.sleep(2)
                s2 = api("GET", f"/projects/{PID}/nodes/{nid}")["status"]
                if s2 == "stopped":
                    break
        r = api("PUT", f"/projects/{PID}/nodes/{nid}",
                {"properties": {"hda_disk_interface": "ide"}})
        chk = api("GET", f"/projects/{PID}/nodes/{nid}")
        print("   iface sekarang:",
              chk["properties"].get("hda_disk_interface"))
    api("POST", f"/projects/{PID}/nodes/{nid}/start")
    print("   start dikirim")

print("")
print("=== menunggu started ===")
for _ in range(75):
    time.sleep(4)
    ns = api("GET", f"/projects/{PID}/nodes")
    stt = [n["status"] for n in ns if n["name"] in ("SW1", "SW2")]
    if all(s == "started" for s in stt):
        print("   kedua switch started")
        break
    print("   ", stt)

import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)
i, o, e = c.exec_command(
    "ps aux | grep qemu | grep -E ' -name SW[12] ' | "
    "grep -oE 'if=[a-z]+|-device [a-z0-9-]+' | sort | uniq -c",
    timeout=30)
print("")
print("=== qemu device check ===")
print(o.read().decode(errors="replace"))
c.close()