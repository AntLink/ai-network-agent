"""Typed Central/Edge contracts for the first capability-based slice."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutionLocation(StrEnum):
    CENTRAL = "CENTRAL"
    EDGE = "EDGE"
    LAB = "LAB"


class RetryClass(StrEnum):
    SAFE_RETRY = "SAFE_RETRY"
    CONDITIONAL_RETRY = "CONDITIONAL_RETRY"
    NON_RETRYABLE = "NON_RETRYABLE"


class CapabilityRequest(BaseModel):
    """Logical task request; secret values are intentionally not accepted."""

    model_config = ConfigDict(extra="forbid")

    task_id: str | None = None
    customer_id: str | None = None
    site_id: str | None = None
    edge_id: str | None = None
    device_id: str
    capability: Literal["device.read.facts"] = "device.read.facts"
    credential_ref: str | None = Field(default=None, min_length=1)
    execution_location: ExecutionLocation | None = None
    deadline_at: datetime | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)


class TaskAttempt(BaseModel):
    attempt_id: str
    task_id: str
    edge_id: str | None = None
    lease_owner: Literal["CENTRAL"] = "CENTRAL"
    lease_expires_at: datetime
    accepted_at: datetime
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    finished_at: datetime | None = None
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN_EXECUTION_STATE"]
    retry_class: RetryClass
    execution_fingerprint: str
    result: dict[str, Any] | None = None
    error_code: str | None = None


class EdgeEnvelope(BaseModel):
    """Versioned, bounded message envelope; sequence is ordering only."""

    protocol_version: int = Field(ge=1, le=10)
    driver_capability_version: int = Field(default=1, ge=1, le=10)
    message_id: str = Field(min_length=1, max_length=128)
    task_id: str = Field(min_length=1, max_length=128)
    attempt_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=200)
    edge_id: str = Field(min_length=1, max_length=128)
    sequence: int = Field(ge=0)
    nonce: str = Field(min_length=16, max_length=256)
    issued_at: datetime
    valid_for_seconds: int = Field(ge=1, le=300)
    lease_duration_seconds: int = Field(ge=1, le=3600)
    retry_class: RetryClass
    capability: Literal["device.read.facts"]
    credential_ref: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_secret_fields(self) -> "EdgeEnvelope":
        secret_names = {"password", "secret", "token", "private_key", "api_key"}
        if any(str(key).lower() in secret_names for key in self.payload):
            raise ValueError("secret-bearing payload fields are not permitted")
        return self
    model_config = ConfigDict(extra="forbid")
