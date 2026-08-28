"""9Router web search and fetch endpoints."""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Any

from app.agent.providers import NineRouterProvider, get_provider

router = APIRouter()


def _get_9router() -> NineRouterProvider:
    provider = get_provider("9router")
    if not isinstance(provider, NineRouterProvider):
        raise HTTPException(500, "9Router provider not configured")
    return provider


@router.post("/search")
async def web_search(payload: dict[str, Any]):
    query = payload.get("query", "")
    if not query:
        raise HTTPException(400, "query is required")

    try:
        drv = _get_9router()
        result = await drv.web_search(
            query=query,
            max_results=payload.get("max_results", 5),
            search_type=payload.get("search_type", "web"),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"9Router search failed: {e}")


@router.post("/fetch")
async def web_fetch(payload: dict[str, Any]):
    url = payload.get("url", "")
    if not url:
        raise HTTPException(400, "url is required")

    try:
        drv = _get_9router()
        result = await drv.web_fetch(
            url=url,
            format=payload.get("format", "markdown"),
            max_characters=payload.get("max_characters", 12000),
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"9Router fetch failed: {e}")


@router.get("/status")
async def nine_router_status():
    try:
        drv = _get_9router()
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{drv.base_url}/v1/models",
                headers=drv._headers(),
            )
            if resp.status_code == 200:
                return {"status": "connected", "url": drv.base_url}
            return {"status": "error", "url": drv.base_url, "code": resp.status_code}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}


@router.get("/models/free")
async def list_free_models():
    try:
        drv = _get_9router()
        return {"models": drv.get_free_models()}
    except Exception as e:
        return {"models": [], "error": str(e)}
