import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def test_simple():
    conn = await asyncssh.connect(
        "172.22.45.249", username="admin", password="Admin123!",
        known_hosts=None, connect_timeout=15,
    )
    # Try simple exec commands
    result = await conn.run("show privilege", check=False)
    print("show privilege:", result.stdout.strip(), result.stderr.strip())
    
    result = await conn.run("show version | include Version", check=False)
    print("show version:", result.stdout.strip())
    
    result = await conn.run("enable", check=False)
    print("enable:", result.stdout.strip(), result.stderr.strip())
    
    conn.close()

asyncio.run(test_simple())