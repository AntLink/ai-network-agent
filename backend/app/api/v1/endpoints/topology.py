from fastapi import APIRouter
router = APIRouter()

@router.get("")
async def topology():
    return {"nodes": [], "links": []}
