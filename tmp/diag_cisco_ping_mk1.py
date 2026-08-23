import asyncio

import asyncssh

HOST = "172.22.45.249"
USERNAME = "admin"
PASSWORD = "Admin123!"

COMMANDS = [
    "ping 172.22.37.62 repeat 4 timeout 2",
    "traceroute 172.22.37.62 numeric timeout 2 probe 2",
]


async def main() -> None:
    for cmd in COMMANDS:
        try:
            async with asyncssh.connect(
                HOST,
                username=USERNAME,
                password=PASSWORD,
                known_hosts=None,
                connect_timeout=10,
            ) as conn:
                res = await asyncio.wait_for(conn.run(cmd, check=False), timeout=60)
                print(f"\n=== {cmd} ===")
                out = ((res.stdout or "") + (res.stderr or "")).strip()
                print(out if out else "(no output)")
        except Exception as e:
            print(f"\n=== {cmd} ===\nERROR {type(e).__name__}: {e}")
        await asyncio.sleep(1)


asyncio.run(main())
