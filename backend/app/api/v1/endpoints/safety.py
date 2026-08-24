import re

from fastapi import HTTPException, Request

from app.core.config import settings


READ_LIKE_POST_PATTERNS = (
    r"^/api/v1/gns3/test-connection$",
    r"^/api/v1/gns3/projects$",
    r"^/api/v1/gns3/projects/[^/]+$",
    r"^/api/v1/gns3/projects/[^/]+/nodes$",
    r"^/api/v1/gns3/projects/[^/]+/links$",
    r"^/api/v1/gns3/projects/[^/]+/snapshots$",
    r"^/api/v1/(cisco|mikrotik)/[^/]+/tools/(ping|traceroute)$",
    r"^/api/v1/mikrotik/[^/]+/monitoring$",
    r"^/api/v1/(cisco|mikrotik)/[^/]+/config/backup$",
)


def is_read_like_request(method: str, path: str) -> bool:
    if method == "GET":
        return True
    if method != "POST":
        return False
    return any(re.match(pattern, path) for pattern in READ_LIKE_POST_PATTERNS)


async def direct_write_guard(request: Request):
    """Development-stage direct write gate.

    Keep ALLOW_DIRECT_WRITE=true for lab iteration. Set it false to force
    changes through the safer plan/policy/apply workflow.
    """
    if settings.ALLOW_DIRECT_WRITE or is_read_like_request(request.method, request.url.path):
        return
    raise HTTPException(
        status_code=403,
        detail=(
            "Direct write endpoints are disabled. Use /api/v1/config/plan, "
            "/api/v1/policy/check, then /api/v1/config/apply."
        ),
    )
