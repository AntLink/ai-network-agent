from app.schemas.edge import RetryClass
from app.services.retry_policy import RetryDecision, evaluate_retry


def test_transport_loss_requires_review_when_execution_is_unknown():
    result = evaluate_retry(
        retry_class=RetryClass.SAFE_RETRY,
        prior_status="RUNNING",
        idempotency_key="idem-1",
        transport_lost=True,
    )
    assert result.decision is RetryDecision.REQUIRE_REVIEW


def test_safe_retry_allows_failed_read_capability():
    result = evaluate_retry(
        retry_class=RetryClass.SAFE_RETRY,
        prior_status="FAILED",
        idempotency_key="idem-2",
    )
    assert result.decision is RetryDecision.ALLOW


def test_conditional_retry_requires_approval_and_verification():
    result = evaluate_retry(
        retry_class=RetryClass.CONDITIONAL_RETRY,
        prior_status="FAILED",
        idempotency_key="idem-3",
        operator_approved=True,
        verification="NOT_EXECUTED",
    )
    assert result.decision is RetryDecision.ALLOW


def test_non_retryable_is_rejected_without_explicit_operator_workflow():
    result = evaluate_retry(
        retry_class=RetryClass.NON_RETRYABLE,
        prior_status="FAILED",
        idempotency_key="idem-4",
    )
    assert result.decision is RetryDecision.REJECT
