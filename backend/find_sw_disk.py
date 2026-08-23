"""Temukan file disk qcow2 milik SW1 & SW2 di GNS3 VM."""
import json
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(errors="replace").strip()


projs = run("ls /opt/gns3/projects/")
print("projects:", projs.replace("\n", ", "))

target = None
for proj in projs.split():
    out = run("ls /opt/gns3/projects/" + proj + "/*.gns3 2>/dev/null")
    if out:
        target = out.splitlines()[0]
        break

print("file proyek:", target)
data = json.loads(run("cat '" + target + "'"))
for n in data["topology"]["nodes"]:
    props = n.get("properties", {})
    print(f"  {n['name']:<8} node_id={n['node_id']} image={props.get('image','')}")
c.close()