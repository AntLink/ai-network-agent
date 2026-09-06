import asyncio

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1.endpoints.safety import direct_write_guard


def _request(path: str, headers: dict[str, str] | None = None) -> Request:
    raw = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({"type": "http", "method": "POST", "path": path, "headers": raw})


def test_gns3_write_requires_operator_approval(monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.safety.settings.ALLOW_DIRECT_WRITE", False)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(direct_write_guard(_request("/api/v1/gns3/projects/p/nodes/n/start")))
    assert exc.value.status_code == 403


def test_gns3_write_accepts_approved_operator_header(monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.safety.settings.ALLOW_DIRECT_WRITE", False)
    asyncio.run(
        direct_write_guard(
            _request(
                "/api/v1/gns3/projects/p/nodes/n/start",
                {"X-Approved-By": "mohfa"},
            )
        )
    )
