import asyncio
import socket
from typing import Optional
from app.csms_monitor.config import settings

class SCPIClient:
    def __init__(self):
        self.host = settings.CSMS_HOST
        self.port = settings.CSMS_SCPI_PORT
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
    
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    async def disconnect(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
    
    async def send_command(self, command: str) -> str:
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return "ERROR: Not connected"
        
        try:
            self.writer.write(f"{command}\n".encode())
            await self.writer.drain()
            
            response = await asyncio.wait_for(
                self.reader.readline(),
                timeout=5.0
            )
            return response.decode().strip()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    async def identify(self) -> str:
        return await self.send_command("*IDN?")
    
    async def measure_frequency(self) -> str:
        return await self.send_command("MEAS:FREQ?")
    
    async def measure_power(self) -> str:
        return await self.send_command("MEAS:POW?")
    
    async def get_frequency_center(self) -> str:
        return await self.send_command("MEAS:FREQ:CENT?")
    
    async def get_frequency_span(self) -> str:
        return await self.send_command("MEAS:FREQ:SPAN?")
    
    async def set_sweep_start(self, freq_hz: int) -> str:
        return await self.send_command(f"SWEEP:START {freq_hz}")
    
    async def set_sweep_stop(self, freq_hz: int) -> str:
        return await self.send_command(f"SWEEP:STOP {freq_hz}")
    
    async def set_sweep_step(self, step_hz: int) -> str:
        return await self.send_command(f"SWEEP:STEP {step_hz}")
    
    async def get_sweep_data(self) -> list:
        response = await self.send_command("SWEEP:DATA?")
        try:
            data = [float(x) for x in response.split(",")]
            return data
        except:
            return []
    
    async def continuous_sweep(self, callback, interval: float = 0.1):
        while True:
            try:
                data = await self.get_sweep_data()
                if data:
                    await callback(data)
                await asyncio.sleep(interval)
            except Exception as e:
                break

scpi_client = SCPIClient()
