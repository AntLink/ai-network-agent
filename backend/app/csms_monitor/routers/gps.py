from fastapi import APIRouter
from app.csms_monitor.gps_client import gps_client

router = APIRouter()

@router.get("/position")
async def get_position():
    position = await gps_client.get_position()
    return position

@router.get("/satellites")
async def get_satellites():
    satellites = await gps_client.get_satellites()
    return {"satellites": satellites}
