"""Shared API response helpers.

Keep HTTP transport errors separate from device-operation failures. Tooling can
then inspect ok/status/error_code without every device prompt issue becoming a
backend exception.
"""
from __future__ import annotations

from fastapi.responses import JSONResponse


def operation_success(
    *,
    data: dict | list | None = None,
    status: str = "success",
    output: str = "",
    http_status: int = 200,
    **meta,
) -> JSONResponse:
    content = {
        "ok": True,
        "status": status,
        "data": data,
        "output": output,
        "error": None,
        **meta,
    }
    return JSONResponse(status_code=http_status, content=content)


def operation_failure(
    *,
    error_code: str,
    message: str,
    retryable: bool = False,
    suggestion: str | None = None,
    status: str = "failed",
    output: str = "",
    http_status: int = 202,
    **meta,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={
            "ok": False,
            "status": status,
            "error_code": error_code,
            "message": message,
            "retryable": retryable,
            "suggestion": suggestion,
            "data": None,
            "output": output,
            "error": {
                "code": error_code,
                "message": message,
                "retryable": retryable,
                "suggestion": suggestion,
            },
            **meta,
        },
    )


def classify_console_error(exc: Exception) -> tuple[str, bool, str]:
    error_text = str(exc).lower()
    if "did not reach a cli prompt" in error_text or "prompt" in error_text:
        return (
            "CLI_PROMPT_NOT_READY",
            True,
            "Tunggu device selesai boot, pastikan prompt Router>/Router# muncul, "
            "atau jawab initial configuration dialog dengan 'no', lalu retry.",
        )
    if "auth" in error_text or "password" in error_text or "login" in error_text:
        return (
            "CONSOLE_AUTH_FAILED",
            False,
            "Periksa username/password/enable secret atau parameter bootstrap perangkat.",
        )
    return (
        "CONSOLE_EXEC_FAILED",
        False,
        "Periksa status node, console host/port, dan output console sebelum retry.",
    )


def console_failure_response(
    *,
    message: str,
    exc: Exception,
    command: str,
    http_status: int = 202,
    **meta,
) -> JSONResponse:
    error_code, retryable, suggestion = classify_console_error(exc)
    return operation_failure(
        error_code=error_code,
        message=message,
        retryable=retryable,
        suggestion=suggestion,
        command=command,
        http_status=http_status,
        **meta,
    )
