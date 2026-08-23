import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def main():
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
        print("Initial prompt:", out.strip())
        # send enable
        proc.stdin.write("enable\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "Password:" in out or out.endswith("#"):
                break
        print("After enable:", out.strip())
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
            print("After password:", out.strip())
        # now in enable mode, configure enable secret
        proc.stdin.write("configure terminal\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("Config mode:", out.strip())
        proc.stdin.write("enable secret Admin123!\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "(config)#" in out:
                break
        print("After enable secret:", out.strip())
        proc.stdin.write("end\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if out.endswith("#"):
                break
        print("After end:", out.strip())
        proc.stdin.write("write memory\n")
        out = ""
        while True:
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "#" in out:
                break
        print("Write memory:", out.strip())
    conn.close()

asyncio.run(main())