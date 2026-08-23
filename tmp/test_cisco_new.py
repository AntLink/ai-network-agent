import asyncio
import asyncssh

HOST = "172.22.36.184"
USERNAME = "admin"
PASSWORD = "Admin123!"

async def test_connect():
    try:
        async with asyncssh.connect(
            HOST, username=USERNAME, password=PASSWORD,
            known_hosts=None, connect_timeout=15,
        ) as conn:
            print("CONNECTED!")
            res = await conn.run("show version", check=False)
            print(res.stdout[:500])
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

asyncio.run(test_connect())