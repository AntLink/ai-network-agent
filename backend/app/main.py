from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.transports.ssh import (
    SSHTransportError,
    SSHConnectError,
    SSHTimeoutError,
    PromptTimeoutError,
)
from app.drivers.cisco.cli import CiscoCLIError

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(SSHConnectError)
async def ssh_connect_error_handler(request: Request, exc: SSHConnectError):
    return JSONResponse(status_code=502, content={"detail": f"SSH connection failed: {exc}"})


@app.exception_handler(SSHTimeoutError)
async def ssh_timeout_error_handler(request: Request, exc: SSHTimeoutError):
    return JSONResponse(status_code=504, content={"detail": f"SSH timeout: {exc}"})


@app.exception_handler(PromptTimeoutError)
async def prompt_timeout_error_handler(request: Request, exc: PromptTimeoutError):
    return JSONResponse(status_code=504, content={"detail": f"CLI prompt timeout: {exc}"})


@app.exception_handler(SSHTransportError)
async def ssh_transport_error_handler(request: Request, exc: SSHTransportError):
    return JSONResponse(status_code=503, content={"detail": f"SSH transport error: {exc}"})


@app.exception_handler(CiscoCLIError)
async def cisco_cli_error_handler(request: Request, exc: CiscoCLIError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    detail = str(exc)
    status = 504 if "timed out" in detail.lower() else 422
    return JSONResponse(status_code=status, content={"detail": detail})


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
