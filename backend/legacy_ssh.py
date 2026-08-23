"""Helper SSH legacy untuk IOSv lama (ssh-rsa/DH-group14-sha1)."""
import time
import paramiko


def connect_legacy(ip, user="admin", pw="Admin123!", timeout=20):
    """Coba paramiko standar; jika gagal KEX, paksa algoritma legacy."""
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(ip, username=user, password=pw, timeout=timeout,
                  allow_agent=False, look_for_keys=False)
        return c
    except Exception as e:
        print(f"  [i] standar gagal ({type(e).__name__}), coba legacy...")
        t = paramiko.Transport((ip, 22))
        so = t.get_security_options()
        so.key_types = ["ssh-rsa"]
        so.kex = ["diffie-hellman-group14-sha1",
                  "diffie-hellman-group1-sha1"]
        t.connect(username=user, password=pw)
        ch = t.open_session(timeout=timeout)
        ch.invoke_shell()
        time.sleep(2)
        while ch.recv_ready():
            ch.recv(65535)

        class LegacyShell:
            def __init__(self, chan):
                self.chan = chan

            def send(self, data):
                if isinstance(data, str):
                    data = data.encode()
                self.chan.send(data)

            def recv_ready(self):
                return self.chan.recv_ready()

            def recv(self, n):
                return self.chan.recv(n)

        sh = LegacyShell(ch)
        sh._transport = t
        return sh


def shell_send(sh, cmd, wait=3):
    sh.send(cmd + "\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.25)
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print("  [" + ("X" if bad else " ") + "] " + cmd)
    return out