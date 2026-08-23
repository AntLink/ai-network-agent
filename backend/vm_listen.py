"""SSH ke GNS3 VM: lihat port konsol yang listening."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.40.30", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)

for cmd in [
    "ss -tln | head -50",
    "ps aux | grep -E 'vpcs|qemu|dynamips' | grep -v grep | awk '{print $11, $12, $13}'",
]:
    stdin, stdout, stderr = c.exec_command(cmd)
    print(f">> {cmd}")
    print(stdout.read().decode())
    err = stderr.read().decode().strip()
    if err:
        print("STDERR:", err)

c.close()