"""Restart SW1+R1 dan SW2+R2 via API untuk rebuild socket link."""
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
TARGETS = ["SW1", "R1", "SW2", "R2"]

print("[1] STOP semua target...")
for name in TARGETS:
    api("POST", f"/projects/{PID}/nodes/{nodes[name]}/stop")
for _ in range(60):
    time.sleep(3)
    ns = api("GET", f"/projects/{PID}/nodes")
    st = [n["status"] for n in ns if n["name"] in TARGETS]
    if all(s == "stopped" for s in st):
        break
print("    status:", st)

print("[2] START semua target...")
for name in TARGETS:
    api("POST", f"/projects/{PID}/nodes/{nodes[name]}/start")
print("[3] menunggu started...")
for _ in range(90):
    time.sleep(4)
    ns = api("GET", f"/projects/{PID}/nodes")
    st = {n["name"]: n["status"] for n in ns}
    cur = [st.get(n) for n in TARGETS]
    print("   ", cur, end="\r")
    if all(s == "started" for s in cur):
        print("")
        break

print("")
print(">>> Semua node started. Tunggu boot IOS ±4 menit.")
print(">>> Setelah itu jalankan ulang verifikasi end-to-end.")