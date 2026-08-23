import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import asyncio
from app.transports.ssh import SSHTransport


async def main():
    transport = SSHTransport(host="192.168.162.20", username="root", password="815m1ll4h")
    result = await transport.run("hostname")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
