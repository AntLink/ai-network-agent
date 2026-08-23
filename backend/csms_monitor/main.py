from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.csms_monitor.config import settings
from app.csms_monitor.routers import scpi, system, gps
from app.csms_monitor.websocket_manager import manager
from app.csms_monitor.scpi_client import scpi_client
import asyncio
import json

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scpi.router, prefix=f"{settings.API_PREFIX}/scpi", tags=["SCPI"])
app.include_router(system.router, prefix=f"{settings.API_PREFIX}/system", tags=["System"])
app.include_router(gps.router, prefix=f"{settings.API_PREFIX}/gps", tags=["GPS"])

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "scpi": f"{settings.API_PREFIX}/scpi",
            "system": f"{settings.API_PREFIX}/system",
            "gps": f"{settings.API_PREFIX}/gps",
            "websocket": settings.WS_PATH,
        }
    }

@app.get("/health")
async def health():
    connected = await scpi_client.connect()
    return {"status": "ok", "scpi_connected": connected}

@app.websocket(settings.WS_PATH)
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe":
                    # Start streaming data
                    pass
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup():
    # Connect to SCPI
    await scpi_client.connect()

@app.on_event("shutdown")
async def shutdown():
    # Disconnect SCPI
    await scpi_client.disconnect()
