import paramiko
import time

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

def setup_priv15():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PW, timeout=30, allow_agent=False, look_for_keys=False)
    
    # Use invoke_shell for interactive session
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
    
    # enable
    out = send("enable\n", "Password:")
    out = send("Admin123!\n", "#")
    print("Enabled")
    
    # configure terminal
    out = send("configure terminal\n", "(config)#")
    
    # username admin privilege 15 secret Admin123!
    out = send("username admin privilege 15 secret Admin123!\n", "(config)#")
    print("User created")
    
    # aaa new-model
    out = send("aaa new-model\n", "(config)#")
    
    out = send("aaa authentication login default local\n", "(config)#")
    
    out = send("aaa authorization exec default local if-authenticated\n", "(config)#")
    
    out = send("line vty 0 4\n", "(config-line)#")
    
    out = send("login authentication default\n", "(config-line)#")
    
    out = send("transport input ssh\n", "(config-line)#")
    
    out = send("exit\n", "(config)#")
    
    out = send("end\n", "#")
    
    out = send("write memory\n", "#")
    print("Config saved")
    
    # verify
    out = send("show privilege\n", "#")
    print("Privilege output:", out)
    
    client.close()
    print("Done!")

if __name__ == "__main__":
    setup_priv15()