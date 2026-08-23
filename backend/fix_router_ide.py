"""Ubah disk interface R1/R2 sata->ide via controller API."""
import base64
import json
import time
import urllib.request

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
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw.strip() else {}


PID = "a6967457-f60e-4752-be8f-6b66e925245c"
nodes = {n["name"]: n["node_id"]
         for n in api("GET", f"/projects/{PID}/nodes")}

for name in ("R1", "R2"):
    nid = nodes[name]
    print("===", name, "===")
    st = api("GET", f"/projects/{PID}/nodes/{nid}")
    print("   iface:", st["properties"].get("hda_disk_interface"),
          "| status:", st["status"])
    if st["status"] != "stopped":
        api("POST", f"/projects/{PID}/nodes/{nid}/stop")
        for _ in range(45):
            time.sleep(3)
            s2 = api("GET", f"/projects/{PID}/nodes/{nid}")["status"]
            if s2 == "stopped":
                break
        print("   stopped")
    api("PUT", f"/projects/{PID}/nodes/{nid}",
        {"properties": {"hda_disk_interface": "ide"}})
    chk = api("GET", f"/projects/{PID}/nodes/{nid}")
    print("   iface sekarang:",
          chk["properties"].get("hda_disk_interface"))
    api("POST", f"/projects/{PID}/nodes/{nid}/start")
    print("   start dikirim")

print("")
print("[i] menunggu started...")
for _ in range(90):
    time.sleep(4)
    ns = api("GET", f"/projects/{PID}/nodes")
    stt = [n["status"] for n in ns if n["name"] in ("R1", "R2")]
    if all(s == "started" for s in stt):
        print("   R1 & R2 started - tunggu boot ±4 menit")
        break
print("   ", stt)

# verifikasi qemu pakai ide
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)
i, o, e = c.exec_command(
    "ps aux | grep qemu | grep -E ' -name R[12] ' | "
    "grep -oE 'if=[a-z]+' | sort | uniq -c", timeout=30)
print("")
print("qemu R1/R2 disk:", o.read().decode(errors="replace").strip())
c.close()