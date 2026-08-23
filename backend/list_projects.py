"""List isi direktori proyek di VM + cari file .gns3."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(errors="replace").strip()


for p in ["78ba841c-362f-47e9-aadd-a03911b60916",
          "a6967457-f60e-4752-be8f-6b66e925245c",
          "bc2acafc-817a-4840-a0cc-aba9c3ec29db"]:
    print("===", p[:8], "===")
    print(run("ls /opt/gns3/projects/" + p + "/ | head -12"))
    g = run("find /opt/gns3/projects/" + p +
            " -maxdepth 1 -name '*.gns3' -o -maxdepth 1 -name '*.gns3project'"
            " 2>/dev/null")
    if g:
        print(">>> file:", g)
c.close()