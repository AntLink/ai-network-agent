import asyncio
import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

async def send_cmd(proc, cmd, wait_for="#", timeout=10):
    proc.stdin.write(cmd + "\n")
    out = ""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        piece = await proc.stdout.read(1024)
        if not piece:
            break
        out += piece
        if wait_for in out:
            break
    return out

async def config_ipsec_r1():
    conn = await asyncssh.connect(
        "172.22.45.249", username="admin", password="Admin123!",
        known_hosts=None, connect_timeout=15,
    )
    async with conn.create_process(term_type="dumb", term_size=(511, 24)) as proc:
        # get to prompt
        await asyncio.sleep(1)
        # enable
        out = await send_cmd(proc, "enable", wait_for="Password:")
        out += await send_cmd(proc, "Admin123!", wait_for="#")
        # configure terminal
        await send_cmd(proc, "configure terminal", wait_for="(config)#")
        # crypto isakmp policy
        await send_cmd(proc, "crypto isakmp policy 10", wait_for="(config-isakmp)#")
        await send_cmd(proc, "encr aes 256", wait_for="(config-isakmp)#")
        await send_cmd(proc, "hash sha", wait_for="(config-isakmp)#")
        await send_cmd(proc, "authentication pre-share", wait_for="(config-isakmp)#")
        await send_cmd(proc, "group 14", wait_for="(config-isakmp)#")
        await send_cmd(proc, "lifetime 86400", wait_for="(config-isakmp)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        # isakmp key
        await send_cmd(proc, "crypto isakmp key VPNKey123 address 172.22.36.184", wait_for="(config)#")
        # transform set
        await send_cmd(proc, "crypto ipsec transform-set TS esp-aes 256 esp-sha-hmac", wait_for="(cfg-trans)#")
        await send_cmd(proc, "mode tunnel", wait_for="(cfg-trans)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        # access list
        await send_cmd(proc, "access-list 100 permit ip 172.22.32.0 0.0.15.255 172.22.32.0 0.0.15.255", wait_for="(config)#")
        # crypto map
        await send_cmd(proc, "crypto map VPNMAP 10 ipsec-isakmp", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "set peer 172.22.36.184", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "set transform-set TS", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "match address 100", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        # apply to interface
        await send_cmd(proc, "interface GigabitEthernet0/0", wait_for="(config-if)#")
        await send_cmd(proc, "crypto map VPNMAP", wait_for="(config-if)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        await send_cmd(proc, "end", wait_for="#")
        await send_cmd(proc, "write memory", wait_for="#")
        print("R1 IPsec config done")

async def config_ipsec_r2():
    conn = await asyncssh.connect(
        "172.22.36.184", username="admin", password="Admin123!",
        known_hosts=None, connect_timeout=15,
    )
    async with conn.create_process(term_type="dumb", term_size=(511, 24)) as proc:
        await asyncio.sleep(1)
        await send_cmd(proc, "enable", wait_for="Password:")
        await send_cmd(proc, "Admin123!", wait_for="#")
        await send_cmd(proc, "configure terminal", wait_for="(config)#")
        await send_cmd(proc, "crypto isakmp policy 10", wait_for="(config-isakmp)#")
        await send_cmd(proc, "encr aes 256", wait_for="(config-isakmp)#")
        await send_cmd(proc, "hash sha", wait_for="(config-isakmp)#")
        await send_cmd(proc, "authentication pre-share", wait_for="(config-isakmp)#")
        await send_cmd(proc, "group 14", wait_for="(config-isakmp)#")
        await send_cmd(proc, "lifetime 86400", wait_for="(config-isakmp)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        await send_cmd(proc, "crypto isakmp key VPNKey123 address 172.22.45.249", wait_for="(config)#")
        await send_cmd(proc, "crypto ipsec transform-set TS esp-aes 256 esp-sha-hmac", wait_for="(cfg-trans)#")
        await send_cmd(proc, "mode tunnel", wait_for="(cfg-trans)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        await send_cmd(proc, "access-list 100 permit ip 172.22.32.0 0.0.15.255 172.22.32.0 0.0.15.255", wait_for="(config)#")
        await send_cmd(proc, "crypto map VPNMAP 10 ipsec-isakmp", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "set peer 172.22.45.249", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "set transform-set TS", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "match address 100", wait_for="(config-crypto-map)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        await send_cmd(proc, "interface GigabitEthernet0/0", wait_for="(config-if)#")
        await send_cmd(proc, "crypto map VPNMAP", wait_for="(config-if)#")
        await send_cmd(proc, "exit", wait_for="(config)#")
        await send_cmd(proc, "end", wait_for="#")
        await send_cmd(proc, "write memory", wait_for="#")
        print("R2 IPsec config done")

async def main():
    await config_ipsec_r1()
    await config_ipsec_r2()
    print("Both routers configured")

asyncio.run(main())