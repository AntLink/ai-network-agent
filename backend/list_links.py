"""Daftar SEMUA link aktual dari GNS3 controller API."""
import base64
import json
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


def api(path):
    req = urllib.request.Request(BASE + path)
    req.add_header("Authorization", "Basic " + TOKEN)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


PID = "a6967457-f60e-4752-be8f-6b66e925245c"
nodes = {n["node_id"]: n["name"] for n in api(f"/projects/{PID}/nodes")}
links = api(f"/projects/{PID}/links")

print(f"Total link: {len(links)}\n")
for lk in sorted(links, key=lambda x: x["link_id"]):
    ends = []
    for e in sorted(lk["nodes"], key=lambda x: x.get("adapter_number", 0)):
        name = nodes.get(e["node_id"], "?")
        ends.append(f"{name}:adapter{e['adapter_number']}"
                    f"/port{e['port_number']}")
    susp = ""
    ids = [e["node_id"] for e in lk["nodes"]]
    names = [nodes.get(i, "?") for i in ids]
    if ("SW1" in names or "SW2" in names) and any(
            n.startswith(("Cloud", "NAT")) for n in names):
        susp = "   <<< KE CLOUD!"
    print(" | ".join(ends) + susp)

print("")
print("--- port map per node ---")
for nid, name in nodes.items():
    nd = api(f"/projects/{PID}/nodes/{nid}")
    props = nd.get("properties", {})
    print(f"{name:<8} adapters={nd.get('ports', [])[:0] or ''}"
          f"type={nd['node_type'][:12]}")