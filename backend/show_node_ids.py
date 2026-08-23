"""Ambil node_id & image semua node dari file proyek lokal."""
import json

d = json.load(open(r"C:\Users\mohfa\GNS3\projects\ai-netagent\ai-netagent.gns3",
                   encoding="utf-8"))
for n in d["topology"]["nodes"]:
    p = n.get("properties", {})
    print(f"{n['name']:<8} type={n['node_type']:<10} node_id={n['node_id']}"
          f" image={p.get('image', '-')}")
