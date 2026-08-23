from fastapi import APIRouter
from app.csms_monitor.scpi_client import scpi_client

router = APIRouter()

@router.get("/identify")
async def identify():
    result = await scpi_client.identify()
    return {"device": result}

@router.get("/frequency")
async def measure_frequency():
    result = await scpi_client.measure_frequency()
    return {"frequency_hz": result}

@router.get("/power")
async def measure_power():
    result = await scpi_client.measure_power()
    return {"power_dbm": result}

@router.get("/sweep/start")
async def get_sweep_start():
    result = await scpi_client.get_frequency_center()
    return {"start_hz": result}

@router.get("/sweep/stop")
async def get_sweep_stop():
    result = await scpi_client.get_frequency_span()
    return {"span_hz": result}

@router.get("/sweep/data")
async def get_sweep_data():
    data = await scpi_client.get_sweep_data()
    return {"data": data}

@router.post("/sweep/start/{freq_hz}")
async def set_sweep_start(freq_hz: int):
    result = await scpi_client.set_sweep_start(freq_hz)
    return {"status": result}

@router.post("/sweep/stop/{freq_hz}")
async def set_sweep_stop(freq_hz: int):
    result = await scpi_client.set_sweep_stop(freq_hz)
    return {"status": result}

@router.post("/sweep/step/{step_hz}")
async def set_sweep_step(step_hz: int):
    result = await scpi_client.set_sweep_step(step_hz)
    return {"status": result}
