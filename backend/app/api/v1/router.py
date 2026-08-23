from fastapi import APIRouter
from app.api.v1.endpoints import devices, config, monitoring, topology, audit, mikrotik, cisco

api_router = APIRouter()
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(topology.router, prefix="/topology", tags=["topology"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(mikrotik.router, prefix="/mikrotik", tags=["mikrotik"])
api_router.include_router(cisco.router, prefix="/cisco", tags=["cisco"])
