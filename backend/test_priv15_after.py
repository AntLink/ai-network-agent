import paramiko
import time

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

def test_priv():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PW, timeout=30, allow_agent=False, look_for_keys=False)
    
    shell = client.invoke_shell()
    time.sleep(1)
    output = shell.recv(65535).decode()
    print("Initial:", output.strip())
    
    def send(cmd, expect_str, timeout=5):
        shell.send(cmd + "\n")
        start = time.time()
        buf = ""
        while time.time() - start < timeout:
            if shell.recv_ready():
                buf += shell.recv(65535).decode()
            if expect_str in buf:
                return buf
            time.sleep(0.1)
        return buf
    
    out = send("show privilege\n", "#")
    print("Privilege:", out)
    
    client.close()

if __name__ == "__main__":
    test_priv()