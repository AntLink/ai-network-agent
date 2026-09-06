"""Central execution-retry policy.

Transport loss is not execution evidence. Callers must provide verification
before replaying an attempt whose device-side outcome is uncertain.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.schemas.edge import RetryClass


class RetryDecision(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    REJECT = "REJECT"


@dataclass(frozen=True)
class RetryEvaluation:
    decision: RetryDecision
    reason: str


def evaluate_retry(
    *,
    retry_class: RetryClass,
    prior_status: str,
    idempotency_key: str | None,
    transport_lost: bool = False,
    verification: str | None = None,
    operator_approved: bool = False,
) -> RetryEvaluation:
    if not idempotency_key:
        return RetryEvaluation(RetryDecision.REJECT, "idempotency key is required")
    if prior_status == "SUCCEEDED":
        return RetryEvaluation(RetryDecision.REJECT, "attempt already succeeded")
    if transport_lost and prior_status in {"DISPATCHING", "RUNNING"} and verification != "NOT_EXECUTED":
        return RetryEvaluation(RetryDecision.REQUIRE_REVIEW, "transport loss does not prove non-execution")
    if retry_class is RetryClass.SAFE_RETRY:
        return RetryEvaluation(RetryDecision.ALLOW, "safe capability may be retried")
    if retry_class is RetryClass.CONDITIONAL_RETRY:
        if operator_approved and verification == "NOT_EXECUTED":
            return RetryEvaluation(RetryDecision.ALLOW, "operator-approved conditional retry verified not executed")
        return RetryEvaluation(RetryDecision.REQUIRE_REVIEW, "conditional retry requires approval and non-execution verification")
    if operator_approved:
        return RetryEvaluation(RetryDecision.ALLOW, "explicit operator workflow approved non-retryable action")
    return RetryEvaluation(RetryDecision.REJECT, "capability is non-retryable")
