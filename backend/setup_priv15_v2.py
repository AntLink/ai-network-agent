import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def setup_priv15():
    conn = await asyncssh.connect(
        HOST, username=USER, password=PW,
        known_hosts=None, connect_timeout=10,
    )
    
    async with conn.create_process(term_type="dumb", term_size=(511, 24)) as proc:
        # drain initial
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if out.endswith(">") or out.endswith("#"): break
        print("Start:", out.strip())
        
        # enable
        proc.stdin.write("enable\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(20):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "Password:" in out or out.endswith("#"): break
        if "Password:" in out:
            proc.stdin.write("Admin123!\n")
            await asyncio.sleep(0.5)
            out = ""
            for _ in range(20):
                piece = await proc.stdout.read(1024)
                if not piece: break
                out += piece
                if out.endswith("#"): break
        print("Enabled:", out.endswith("#"))
        
        # configure terminal
        proc.stdin.write("configure terminal\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
        
        # set privilege 15 user
        proc.stdin.write("username admin privilege 15 secret Admin123!\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
        
        # aaa new-model
        proc.stdin.write("aaa new-model\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
            
        proc.stdin.write("aaa authentication login default local\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
            
        proc.stdin.write("aaa authorization exec default local if-authenticated\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
            
        proc.stdin.write("line vty 0 4\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config-line)#" in out: break
            
        proc.stdin.write("login authentication default\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config-line)#" in out: break
            
        proc.stdin.write("transport input ssh\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config-line)#" in out: break
            
        proc.stdin.write("exit\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "(config)#" in out: break
            
        proc.stdin.write("end\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if out.endswith("#"): break
        
        proc.stdin.write("write memory\n")
        await asyncio.sleep(1)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "#" in out: break
        
        # verify
        proc.stdin.write("show privilege\n")
        await asyncio.sleep(0.5)
        out = ""
        for _ in range(10):
            piece = await proc.stdout.read(1024)
            if not piece: break
            out += piece
            if "#" in out: break
        print("Privilege:", out.strip())
        
    conn.close()

async def main():
    await setup_priv15()

asyncio.run(main())