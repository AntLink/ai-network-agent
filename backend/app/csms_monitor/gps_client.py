from typing import Optional

import httpx

from app.csms_monitor.config import settings


class GPSClient:
    def __init__(self):
        self.bridge_url = settings.CSMS_BRIDGE_URL.rstrip("/")
        self.position = {"lat": 0.0, "lon": 0.0, "alt": 0.0, "speed": 0.0}

    async def _get(self, path: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.bridge_url}{path}")
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return None

    async def get_position(self) -> dict:
        data = await self._get("/gps")
        if data:
            self.position = {
                "lat": data.get("latitude", 0.0),
                "lon": data.get("longitude", 0.0),
                "alt": data.get("altitude", 0.0),
                "speed": 0.0,
                "track": 0.0,
                "satellites": data.get("satellites", 0),
                "fix": data.get("fix", False),
                "time": data.get("timestamp", ""),
            }
        return self.position

    async def get_satellites(self) -> list:
        data = await self._get("/gps")
        if not data:
            return []
        return [
            {
                "count": data.get("satellites", 0),
                "used": data.get("fix", False),
            }
        ]

    async def get_ntp(self) -> dict:
        data = await self._get("/ntp")
        return data or {}


gps_client = GPSClient()
