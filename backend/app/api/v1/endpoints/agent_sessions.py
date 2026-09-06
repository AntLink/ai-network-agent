"""Agent chat session persistence endpoints."""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from typing import Any

router = APIRouter()

# Persisted to a JSON file so sessions survive backend restarts.
SESSIONS_FILE = Path(__file__).resolve().parents[4] / "logs" / "agent-sessions.json"

# In-memory fallback if file cannot be read/written.
_sessions: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, dict[str, Any]]:
    try:
        if SESSIONS_FILE.exists():
            data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return _sessions


def _save(data: dict[str, dict[str, Any]]) -> None:
    global _sessions
    _sessions = data
    try:
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSIONS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def _serialize(session: dict[str, Any], include_messages: bool = False) -> dict[str, Any]:
    """Safe output shape (no internal fields)."""
    out = {
        "id": session.get("id"),
        "title": session.get("title", "New Chat"),
        "created_at": session.get("created_at"),
        "updated_at": session.get("updated_at"),
        "status": session.get("status", "idle"),
        "device_ids": session.get("device_ids", []),
        "lab_id": session.get("lab_id"),
        "project_id": session.get("project_id"),
        "environment": session.get("environment", "lab"),
        "message_count": len(session.get("messages", [])),
    }
    if include_messages:
        out["messages"] = session.get("messages", [])
    return out


@router.get("/sessions")
async def list_sessions():
    data = _load()
    sessions = [_serialize(s) for s in data.values()]
    sessions.sort(key=lambda s: s.get("updated_at") or "", reverse=True)
    return {"sessions": sessions}


@router.post("/sessions")
async def create_session(payload: dict[str, Any] | None = None):
    payload = payload or {}
    session_id = str(uuid.uuid4())
    now = _utc_now()
    session = {
        "id": session_id,
        "title": payload.get("title") or "New Chat",
        "created_at": now,
        "updated_at": now,
        "status": "idle",
        "device_ids": payload.get("device_ids", []),
        "lab_id": payload.get("lab_id"),
        "project_id": payload.get("project_id"),
        "environment": payload.get("environment") or "lab",
        "messages": [],
    }
    data = _load()
    data[session_id] = session
    _save(data)
    return _serialize(session)


@router.post("/sessions/backfill")
async def backfill_sessions(payload: dict[str, Any] | None = None):
    """Repair empty or truncated assistant messages in stored sessions."""
    payload = payload or {}
    session_ids = payload.get("session_ids")
    dry_run = bool(payload.get("dry_run", False))

    data = _load()
    repaired_sessions = 0
    repaired_messages = 0
    skipped_sessions = 0

    for session_id, session in data.items():
        if isinstance(session_ids, list) and session_ids and session_id not in session_ids:
            continue

        messages = session.get("messages", [])
        if not messages:
            skipped_sessions += 1
            continue

        session_repaired = 0
        for index, message in enumerate(messages):
            if message.get("role") != "assistant":
                continue
            if not _looks_truncated_assistant_message(message):
                continue

            repaired_text = await _repair_session_message(session, index)
            if not repaired_text:
                continue

            if not dry_run:
                message["content"] = repaired_text
                message["updated_at"] = _utc_now()
            repaired_messages += 1
            session_repaired += 1

        if session_repaired:
            repaired_sessions += 1
            session["updated_at"] = _utc_now()

    if not dry_run:
        _save(data)

    return {
        "status": "ok",
        "dry_run": dry_run,
        "repaired_sessions": repaired_sessions,
        "repaired_messages": repaired_messages,
        "skipped_sessions": skipped_sessions,
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return _serialize(session, include_messages=True)


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, payload: dict[str, Any]):
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if "title" in payload:
        session["title"] = payload["title"]
    if "device_ids" in payload:
        session["device_ids"] = payload["device_ids"]
    if "lab_id" in payload:
        session["lab_id"] = payload["lab_id"]
    if "project_id" in payload:
        session["project_id"] = payload["project_id"]
    if "environment" in payload:
        session["environment"] = payload["environment"] or "lab"
    if "status" in payload:
        session["status"] = payload["status"]
    session["updated_at"] = _utc_now()
    _save(data)
    return _serialize(session)


def update_session_context(
    session_id: str,
    *,
    device_ids: list[str] | None = None,
    lab_id: str | None = None,
    project_id: str | None = None,
    environment: str | None = None,
) -> dict[str, Any]:
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if device_ids is not None:
        session["device_ids"] = device_ids
    if lab_id is not None:
        session["lab_id"] = lab_id or None
    if project_id is not None:
        session["project_id"] = project_id or None
    if environment is not None:
        session["environment"] = environment or "lab"
    session["updated_at"] = _utc_now()
    _save(data)
    return _serialize(session)


def get_session_context(session_id: str) -> dict[str, Any] | None:
    data = _load()
    session = data.get(session_id)
    if not session:
        return None
    return {
        "device_ids": session.get("device_ids", []) or [],
        "lab_id": session.get("lab_id"),
        "project_id": session.get("project_id"),
        "environment": session.get("environment", "lab"),
        "status": session.get("status", "idle"),
        "title": session.get("title", "New Chat"),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    data = _load()
    if session_id not in data:
        raise HTTPException(404, "Session not found")
    del data[session_id]
    _save(data)
    return {"status": "deleted", "session_id": session_id}


@router.get("/sessions/{session_id}/messages")
async def list_session_messages(session_id: str):
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {"messages": session.get("messages", [])}


@router.post("/sessions/{session_id}/messages")
async def add_session_message(session_id: str, payload: dict[str, Any]):
    return await upsert_session_message(session_id, payload)


async def upsert_session_message(session_id: str, payload: dict[str, Any]):
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    message = {
        "id": payload.get("id") or str(uuid.uuid4()),
        "session_id": session_id,
        "role": payload.get("role", "user"),
        "content": payload.get("content", ""),
        "type": payload.get("type", "message"),
        "created_at": payload.get("created_at") or _utc_now(),
    }
    messages = session.setdefault("messages", [])
    existing_index = next((index for index, item in enumerate(messages) if item.get("id") == message["id"]), -1)
    if existing_index >= 0:
        messages[existing_index] = message
    else:
        messages.append(message)
    session["updated_at"] = _utc_now()
    # Auto-title from first user message
    if session["title"] == "New Chat" and message["role"] == "user":
        title = message["content"].strip().replace("\n", " ")[:48]
        if title:
            session["title"] = title
    _save(data)
    return message


async def _repair_session_message(session: dict[str, Any], message_index: int) -> str:
    """Regenerate a blank assistant message from the surrounding conversation."""
    messages = session.get("messages", [])
    if message_index < 0 or message_index >= len(messages):
        return ""

    history = messages[:message_index]
    last_user = next((item for item in reversed(history) if item.get("role") == "user"), None)
    prompt = str(last_user.get("content", "") if last_user else "").strip()
    if not prompt:
        return ""

    try:
        from app.api.v1.endpoints.agent import (
            _append_device_context,
            _build_prompts,
            _collect_device_context,
            _context_aware_response,
            _llm_chat,
        )

        history_payload = [{"role": item.get("role"), "text": item.get("content", "")} for item in history]
        system_prompt, base_user_prompt, resolved_device_ids, _ = _build_prompts(
            prompt,
            history=history_payload,
            device_ids=session.get("device_ids", []),
            lab_id=str(session.get("lab_id") or ""),
            mode="guarded",
        )

        device_context = ""
        if resolved_device_ids:
            try:
                device_context = await _collect_device_context(resolved_device_ids)
            except Exception as exc:
                device_context = f"(failed to collect device context: {exc})"

        user_prompt = _append_device_context(
            base_user_prompt,
            device_context,
            resolved_device_ids,
            message=prompt,
            history=history_payload,
        )
        response = await _llm_chat(system_prompt, user_prompt)
        response = response.strip()
        if response:
            return response
    except Exception:
        pass

    try:
        from app.api.v1.endpoints.agent import _context_aware_response

        return _context_aware_response(
            prompt,
            session.get("device_ids", []),
            "",
            "backfill fallback",
        ).strip()
    except Exception:
        return ""


def _looks_truncated_assistant_message(message: dict[str, Any]) -> bool:
    """Heuristic check for assistant replies that are likely partial or corrupted."""
    content = " ".join(str(message.get("content", "")).split()).strip()
    if not content:
        return True

    normalized = content.lower()
    safe_short_replies = {
        "halo!",
        "hello!",
        "hi!",
        "oke",
        "ok",
        "siap",
        "baik",
        "lanjut",
        "yes",
        "ya",
    }
    if normalized in safe_short_replies:
        return False

    if content.startswith(("```", "{", "[")):
        return False

    if normalized in {"?", "(linux)", "(cisco)", "(mikrotik)", "(aruba)"}:
        return True

    word_count = len(content.split())
    if len(content) <= 24 and word_count <= 3:
        suspicious_tokens = (
            "ikutnya",
            "figurasi",
            "routing",
            "interface",
            "config",
            "state",
            "linux",
            "cisco",
            "mikrotik",
            "aruba",
        )
        if any(token in normalized for token in suspicious_tokens):
            return True
        if content.endswith((".", ",", ":", ";", "-", "—", "?", ")")):
            return True

    return False


@router.delete("/sessions/{session_id}/messages/{message_id}")
async def delete_session_message(session_id: str, message_id: str):
    data = _load()
    session = data.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    before = len(session.get("messages", []))
    session["messages"] = [m for m in session.get("messages", []) if m.get("id") != message_id]
    if len(session["messages"]) == before:
        raise HTTPException(404, "Message not found")
    session["updated_at"] = _utc_now()
    _save(data)
    return {"status": "deleted", "message_id": message_id}
