import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def setup_privilege_15():
    conn = await asyncssh.connect(
        HOST, username=USER, password=PW,
        known_hosts=None, connect_timeout=15,
    )
    async with conn.create_process(term_type="dumb", term_size=(511, 24)) as proc:
        # read initial prompt
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if out.endswith(">") or out.endswith("#"):
                break
        print("Initial:", out.strip())
        
        # enable
        proc.stdin.write("enable\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "Password:" in out or out.endswith("#"):
                break
        if "Password:" in out:
            proc.stdin.write("Admin123!\n")
            out = ""
            while True:
                piece = await proc.stdout.read(1024)
                if not piece:
                    break
                out += piece
                if out.endswith("#"):
                    break
        print("Enabled:", out.strip()[-50:])
        
        # configure terminal
        proc.stdin.write("configure terminal\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("Config mode:", out.strip()[-30:])
        
        # set username admin privilege 15
        proc.stdin.write("username admin privilege 15 secret Admin123!\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("User set:", out.strip()[-30:])
        
        # aaa new-model
        proc.stdin.write("aaa new-model\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("aaa new-model:", out.strip()[-30:])
        
        proc.stdin.write("aaa authentication login default local\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("aaa auth:", out.strip()[-30:])
        
        proc.stdin.write("aaa authorization exec default local if-authenticated\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("aaa authz:", out.strip()[-30:])
        
        proc.stdin.write("line vty 0 4\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config-line)#" in out:
                break
        print("line vty:", out.strip()[-30:])
        
        proc.stdin.write("login authentication default\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config-line)#" in out:
                break
        print("login auth:", out.strip()[-30:])
        
        proc.stdin.write("transport input ssh\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config-line)#" in out:
                break
        print("transport:", out.strip()[-30:])
        
        proc.stdin.write("exit\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("exit line:", out.strip()[-30:])
        
        proc.stdin.write("end\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if out.endswith("#"):
                break
        print("end:", out.strip()[-30:])
        
        proc.stdin.write("write memory\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "#" in out:
                break
        print("write mem:", out.strip()[-50:])
        
        # verify privilege
        proc.stdin.write("show privilege\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "#" in out:
                break
        print("Privilege:", out.strip())
        
    conn.close()

async def main():
    await setup_privilege_15()

asyncio.run(main())