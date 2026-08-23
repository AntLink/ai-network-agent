import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 30

    cmd = """grep -inE "port|3302|3303|3307|metrics|equip|vcp|realtime|rds|audio|listen|server" /media/tci/csms/etc/csmsGeneral.xml | head -60
echo '--- df ini ---'
grep -inE "port|3302|3303|3307" /media/tci/csms/etc/csmsDf.ini | head -30
true"""
    r = await t.run(cmd)
    print(r)


asyncio.run(main())
