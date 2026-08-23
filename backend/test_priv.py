import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def test_basic():
    conn = await asyncssh.connect(
        HOST, username=USER, password=PW,
        known_hosts=None, connect_timeout=15,
    )
    async with conn.create_process(term_type="dumb", term_size=(511, 24)) as proc:
        # read initial prompt
        out = ""
        for _ in range(20):
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if out.endswith(">") or out.endswith("#"):
                break
        print("Initial:", repr(out.strip()))
        
        # try enable
        proc.stdin.write("enable\n")
        out = ""
        for _ in range(30):
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "Password:" in out or out.endswith("#"):
                break
        print("After enable:", repr(out.strip()))
        if "Password:" in out:
            proc.stdin.write("Admin123!\n")
            out = ""
            for _ in range(30):
                piece = await proc.stdout.read(1024)
                if not piece:
                    break
                out += piece
                if out.endswith("#"):
                    break
            print("After password:", repr(out.strip()[-50:]))
        
        # test command
        proc.stdin.write("show privilege\n")
        out = ""
        for _ in range(30):
            piece = await proc.stdout.read(1024)
            if not piece:
                break
            out += piece
            if "#" in out:
                break
        print("Privilege:", repr(out.strip()))
        
    conn.close()

async def main():
    await test_basic()

asyncio.run(main())