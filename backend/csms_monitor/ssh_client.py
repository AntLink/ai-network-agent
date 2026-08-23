import asyncio
from typing import Optional
from app.csms_monitor.config import settings

class SSHClient:
    def __init__(self):
        self.host = settings.CSMS_HOST
        self.port = settings.CSMS_SSH_PORT
        self.username = settings.CSMS_SSH_USER
        self.password = settings.CSMS_SSH_PASS
        self.connection = None
    
    async def connect(self):
        try:
            import asyncssh
            self.connection = await asyncssh.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                known_hosts=None
            )
            return True
        except Exception as e:
            return False
    
    async def disconnect(self):
        if self.connection:
            self.connection.close()
        self.connection = None
    
    async def run_command(self, command: str) -> str:
        if not self.connection:
            await self.connect()
        
        if not self.connection:
            return "ERROR: Not connected"
        
        try:
            result = await asyncio.wait_for(
                self.connection.run(command, check=False),
                timeout=10.0
            )
            return result.stdout
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    async def get_system_info(self) -> dict:
        info = {}
        
        # Hostname
        info["hostname"] = (await self.run_command("hostname")).strip()
        
        # Uptime
        info["uptime"] = (await self.run_command("uptime")).strip()
        
        # CPU info
        info["cpu"] = (await self.run_command("cat /proc/stat | head -1")).strip()
        
        # Memory info
        info["memory"] = (await self.run_command("cat /proc/meminfo | head -5")).strip()
        
        # Network
        info["network"] = (await self.run_command("cat /proc/net/dev")).strip()
        
        # Disk
        info["disk"] = (await self.run_command("df -h /")).strip()
        
        return info
    
    async def get_services(self) -> dict:
        services = {}
        
        # csmsd status
        csmsd = await self.run_command("ps aux | grep csmsd.elf | grep -v grep")
        services["csmsd"] = "running" if csmsd.strip() else "stopped"
        
        # csmsAudio status
        csms_audio = await self.run_command("ps aux | grep csmsAudio.elf | grep -v grep")
        services["csmsAudio"] = "running" if csms_audio.strip() else "stopped"
        
        # SendIP status
        sendip = await self.run_command("ps aux | grep SendIP.elf | grep -v grep")
        services["sendIP"] = "running" if sendip.strip() else "stopped"
        
        # gpsd status
        gpsd = await self.run_command("ps aux | grep gpsd | grep -v grep")
        services["gpsd"] = "running" if gpsd.strip() else "stopped"
        
        # ntpd status
        ntpd = await self.run_command("ps aux | grep ntpd | grep -v grep")
        services["ntpd"] = "running" if ntpd.strip() else "stopped"
        
        return services
    
    async def start_csmsd(self) -> str:
        return await self.run_command("/media/tci/csms/bin/csmsd.elf &")
    
    async def stop_csmsd(self) -> str:
        return await self.run_command("killall csmsd.elf")
    
    async def get_logs(self, lines: int = 50) -> str:
        return await self.run_command(f"tail -{lines} /var/volatile/log/messages")

ssh_client = SSHClient()
