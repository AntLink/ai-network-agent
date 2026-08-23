"""Buka project GNS3 lalu jalankan fix disk interface."""
import json
import time
import urllib.request

BASE = "http://172.22.37.68/v2"
PID = "a6967457-f60e-4752-be8f-6b66e925245c"


def api(method, path, body=None, expect_err=False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        if expect_err:
            return {"_err": e.code}
        raise


projs = api("GET", "/projects")
opened = [p for p in projs if p["project_id"] == PID]
print("project:", opened[0]["name"] if opened else "?",
      "| status:", opened[0].get("status") if opened else "-")
if not opened or opened[0].get("status") != "opened":
    print(">> membuka project...")
    api("POST", f"/projects/{PID}/open")
    print("   terbuka")

nodes = api("GET", f"/projects/{PID}/nodes")
sw = {}
for n in nodes:
    if n["name"] in ("SW1", "SW2"):
        sw[n["name"]] = n
        print(n["name"], n["node_id"],
              "iface:", n["properties"].get("hda_disk_interface"),
              "status:", n["status"])

for name in ("SW1", "SW2"):
    node = sw[name]
    nid = node["node_id"]
    print("")
    print("===", name, "===")
    api("POST", f"/projects/{PID}/nodes/{nid}/stop")
    for _ in range(45):
        time.sleep(2)
        st = api("GET", f"/projects/{PID}/nodes/{nid}")["status"]
        if st == "stopped":
            break
    print(" [ ] status:", st)

    props = dict(node["properties"])
    props["hda_disk_interface"] = "ide"
    body = {k: v for k, v in node.items() if k != "status"}
    body["properties"] = props
    api("PUT", f"/projects/{PID}/nodes/{nid}", body)
    chk = api("GET", f"/projects/{PID}/nodes/{nid}")
    print(" [ ] iface sekarang:",
          chk["properties"].get("hda_disk_interface"))
    api("POST", f"/projects/{PID}/nodes/{nid}/start")
    print(" [ ] start dikirim")

print("")
print("=== menunggu start... ===")
for _ in range(60):
    time.sleep(4)
    allnodes = api("GET", f"/projects/{PID}/nodes")
    running = [n["status"] for n in allnodes if n["name"] in ("SW1", "SW2")]
    if all(s == "started" for s in running):
        print("   kedua switch: started")
        break
    print("   status:", running)

print("")
print("=== verifikasi qemu cmdline (harus if=ide) ===")
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)
i, o, e = c.exec_command(
    "ps aux | grep qemu | grep -E 'SW1|SW2' | "
    "grep -o 'if=[a-z]*' | sort | uniq -c", timeout=30)
print(o.read().decode(errors="replace"))
c.close()
print("=== SELESAI - tunggu boot IOS ~3 menit ===")