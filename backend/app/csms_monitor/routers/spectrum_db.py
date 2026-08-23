from fastapi import APIRouter, HTTPException

from app.csms_monitor.spectrum_db import spectrum_db_client

router = APIRouter()


@router.get("/measurements")
async def list_measurements(limit: int = 10):
    try:
        return {"measurements": await spectrum_db_client.measurements(limit)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CSMS DB unreachable: {e}")


@router.get("/latest")
async def latest_signal():
    try:
        return await spectrum_db_client.latest_with_signal()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CSMS DB unreachable: {e}")


@router.get("/spectrum/{measure_id}")
async def get_spectrum(measure_id: int):
    try:
        data = await spectrum_db_client.spectrum(measure_id)
        if not data["blocks"]:
            raise HTTPException(status_code=404, detail="No spectrum data for this measurement")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CSMS DB unreachable: {e}")
