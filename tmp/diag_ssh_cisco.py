import asyncio
import socket

import asyncssh

HOST = "172.22.45.249"
PASSWORD = "Admin123!"


def get_banner() -> str:
    s = socket.create_connection((HOST, 22), timeout=5)
    try:
        return s.recv(512).decode(errors="replace").strip()
    finally:
        s.close()


async def try_login(user: str) -> str:
    try:
        conn = await asyncio.wait_for(
            asyncssh.connect(
                HOST,
                username=user,
                password=PASSWORD,
                known_hosts=None,
                connect_timeout=10,
            ),
            timeout=15,
        )
    except asyncssh.PermissionDenied as e:
        return f"AUTH DENIED ({e.reason})"
    except asyncssh.KeyExchangeFailed as e:
        return f"KEX FAILED: {e}"
    except asyncssh.DisconnectError as e:
        return f"DISCONNECTED code={e.code}: {e.reason}"
    except OSError as e:
        return f"NETWORK: {e}"
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    try:
        res = await conn.run("show version | i Version", check=False)
        out = ((res.stdout or "") + (res.stderr or "")).strip().splitlines()
        return "LOGIN OK -> " + (" | ".join(out[:3]) if out else "(no output)")
    finally:
        conn.close()


async def main() -> None:
    print("SSH BANNER:", get_banner())
    for u in ["admin", "cisco", "root"]:
        print(f"user={u:<6}:", await try_login(u))


asyncio.run(main())
