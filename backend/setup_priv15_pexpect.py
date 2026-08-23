import pexpect
import sys

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

def setup_priv15():
    child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {USER}@{HOST}", timeout=30)
    child.logfile = sys.stdout.buffer
    
    child.expect("Password:")
    child.sendline(PW)
    child.expect(">")
    
    child.sendline("enable")
    child.expect("Password:")
    child.sendline(PW)
    child.expect("#")
    print("Enabled")
    
    child.sendline("configure terminal")
    child.expect("(config)#")
    
    child.sendline("username admin privilege 15 secret Admin123!")
    child.expect("(config)#")
    print("User created")
    
    child.sendline("aaa new-model")
    child.expect("(config)#")
    
    child.sendline("aaa authentication login default local")
    child.expect("(config)#")
    
    child.sendline("aaa authorization exec default local if-authenticated")
    child.expect("(config)#")
    
    child.sendline("line vty 0 4")
    child.expect("(config-line)#")
    
    child.sendline("login authentication default")
    child.expect("(config-line)#")
    
    child.sendline("transport input ssh")
    child.expect("(config-line)#")
    
    child.sendline("exit")
    child.expect("(config)#")
    
    child.sendline("end")
    child.expect("#")
    
    child.sendline("write memory")
    child.expect("#")
    print("Config saved")
    
    child.sendline("show privilege")
    child.expect("#")
    print(child.before.decode().strip())
    
    child.sendline("exit")
    child.expect(pexpect.EOF)
    
    print("Done!")

if __name__ == "__main__":
    setup_priv15()