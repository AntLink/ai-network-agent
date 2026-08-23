"""Fix disk interface SW1/SW2 sata->ide via GNS3 controller API (localhost)."""
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


ver = api("GET", "/version")
print("controller:", ver.get("version"))

projs = api("GET", "/projects")
proj = None
for p in projs:
    print("project:", p["name"], p["project_id"][:8], p.get("status"))
    if "ai" in p["name"].lower() or "netagent" in p["name"].lower():
        proj = p
if proj is None:
    raise SystemExit("project tidak ditemukan")
PID = proj["project_id"]
if proj.get("status") != "opened":
    api("POST", f"/projects/{PID}/open")
    time.sleep(2)

nodes = api("GET", f"/projects/{PID}/nodes")
sw = {n["name"]: n for n in nodes if n["name"] in ("SW1", "SW2")}

for name in ("SW1", "SW2"):
    node = sw[name]
    nid = node["node_id"]
    print("")
    print("===", name, "| iface:",
          node["properties"].get("hda_disk_interface"),
          "| status:", node["status"], "===")
    if node["status"] != "stopped":
        api("POST", f"/projects/{PID}/nodes/{nid}/stop")
        for _ in range(45):
            time.sleep(2)
            st = api("GET", f"/projects/{PID}/nodes/{nid}")["status"]
            if st == "stopped":
                break
        print(" [ ] stopped:", st)

    props = dict(node["properties"])
    props["hda_disk_interface"] = "ide"
    body = {k: v for k, v in node.items() if k not in ("status",)}
    body["properties"] = props
    api("PUT", f"/projects/{PID}/nodes/{nid}", body)
    chk = api("GET", f"/projects/{PID}/nodes/{nid}")
    print(" [ ] iface baru:", chk["properties"].get("hda_disk_interface"))
    api("POST", f"/projects/{PID}/nodes/{nid}/start")
    print(" [ ] start dikirim")

print("")
print("=== menunggu started ===")
for _ in range(60):
    time.sleep(4)
    ns = api("GET", f"/projects/{PID}/nodes")
    st = [n["status"] for n in ns if n["name"] in ("SW1", "SW2")]
    if all(s == "started" for s in st):
        print("   kedua switch started")
        break
print("")
print(">>> TUNGGU BOOT IOS ±3 MENIT SEBELUM KONFIGURASI <<<")