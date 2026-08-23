"""Diagnosa menyeluruh GNS3 VM."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.40.30", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)

cmds = [
    ("SEMUA PROSES (non-system)", "ps aux --sort=-%mem | awk '$11 !~ /^\\[/ {print $11, $12, $13}' | head -30"),
    ("DOCKER", "sudo docker ps 2>/dev/null || docker ps 2>/dev/null || echo 'no docker'"),
    ("TCP LISTEN", "ss -tlnp | head -30"),
    ("UDP LISTEN", "ss -ulnp | head -30"),
]
for label, cmd in cmds:
    stdin, stdout, stderr = c.exec_command(cmd)
    print(f"===== {label} =====")
    print(stdout.read().decode())

c.close()