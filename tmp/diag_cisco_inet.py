import asyncio

import asyncssh

HOST = "172.22.45.249"
USERNAME = "admin"
PASSWORD = "Admin123!"

COMMANDS = [
    "show ip route",
    "ping 8.8.8.8 repeat 3 timeout 2",
    "ping 1.1.1.1 repeat 3 timeout 2",
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
                res = await asyncio.wait_for(conn.run(cmd, check=False), timeout=40)
                print(f"\n=== {cmd} ===")
                out = ((res.stdout or "") + (res.stderr or "")).strip()
                print(out if out else "(no output)")
        except Exception as e:
            print(f"\n=== {cmd} ===\nERROR {type(e).__name__}: {e}")
        await asyncio.sleep(1)


asyncio.run(main())
