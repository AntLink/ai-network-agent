from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.services.terminal_service import TerminalSessionError, terminal_session_manager

router = APIRouter()


class TerminalSessionCreate(BaseModel):
    device_id: str = Field(..., min_length=1)


class TerminalExecuteRequest(BaseModel):
    command: str = Field(..., min_length=1)


class TerminalSuggestRequest(BaseModel):
    partial: str = ""


class TerminalInputRequest(BaseModel):
    data: str = ""


@router.get("/sessions")
async def list_terminal_sessions():
    return {"status": "ok", "data": await terminal_session_manager.list_sessions()}


@router.post("/sessions")
async def create_terminal_session(payload: TerminalSessionCreate):
    try:
        session = await terminal_session_manager.create(payload.device_id)
    except TerminalSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SSH session failed: {e}")
    return {
        "status": "connected",
        "data": {
            "session_id": session.session_id,
            "device_id": session.device_id,
            "hostname": session.device.get("hostname"),
            "vendor": session.vendor,
            "management_address": session.device.get("management_address"),
            "prompt": session.prompt,
        },
    }


@router.delete("/sessions/{session_id}")
async def close_terminal_session(session_id: str):
    await terminal_session_manager.close(session_id)
    return {"status": "closed", "session_id": session_id}


@router.post("/sessions/{session_id}/execute")
async def execute_terminal_command(session_id: str, payload: TerminalExecuteRequest):
    try:
        return {"status": "ok", "data": await terminal_session_manager.execute(session_id, payload.command)}
    except TerminalSessionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"terminal command failed: {e}")


@router.post("/sessions/{session_id}/suggest")
async def suggest_terminal_command(session_id: str, payload: TerminalSuggestRequest):
    try:
        return {"status": "ok", "data": await terminal_session_manager.suggest(session_id, payload.partial)}
    except TerminalSessionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"terminal suggest failed: {e}")


@router.post("/sessions/{session_id}/input")
async def send_terminal_input(session_id: str, payload: TerminalInputRequest):
    try:
        return {"status": "ok", "data": await terminal_session_manager.raw_input(session_id, payload.data)}
    except TerminalSessionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"terminal input failed: {e}")


@router.websocket("/sessions/{session_id}/stream")
async def terminal_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        await terminal_session_manager.get(session_id)
        await websocket.send_json({"type": "connected", "session_id": session_id})
        while True:
            event = await websocket.receive_json()
            event_type = event.get("type")

            if event_type == "execute":
                result = await terminal_session_manager.execute(session_id, str(event.get("command", "")))
                await websocket.send_json({"type": "command_output", "data": result})
            elif event_type == "suggest":
                result = await terminal_session_manager.suggest(session_id, str(event.get("partial", "")))
                await websocket.send_json({"type": "suggestions", "data": result})
            elif event_type == "input":
                result = await terminal_session_manager.raw_input(session_id, str(event.get("data", "")))
                await websocket.send_json(result)
            elif event_type == "close":
                await terminal_session_manager.close(session_id)
                await websocket.send_json({"type": "closed", "session_id": session_id})
                await websocket.close()
                return
            else:
                await websocket.send_json({"type": "error", "message": f"Unsupported event type: {event_type}"})
    except WebSocketDisconnect:
        return
    except TerminalSessionError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close(code=1008)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close(code=1011)
