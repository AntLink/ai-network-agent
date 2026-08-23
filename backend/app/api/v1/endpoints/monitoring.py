from fastapi import APIRouter
router = APIRouter()

@router.get("/{device_id}")
async def monitoring(device_id: str):
    return {"device_id": device_id, "status": "not_implemented"}
