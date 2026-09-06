from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.edge import EdgeEnvelope, ExecutionLocation, RetryClass
from app.services.execution_routing import ExecutionRoutingResolver


def test_resolver_scopes_edge_by_edge_id_not_management_ip():
    resolver = ExecutionRoutingResolver()
    route_a = resolver.resolve(
        {"id": "a-r1", "management_address": "192.168.1.1"},
        requested_location=ExecutionLocation.EDGE,
        requested_edge_id="edge-a",
    )
    route_b = resolver.resolve(
        {"id": "b-r1", "management_address": "192.168.1.1"},
        requested_location=ExecutionLocation.EDGE,
        requested_edge_id="edge-b",
    )
    assert route_a.edge_id == "edge-a"
    assert route_b.edge_id == "edge-b"
    assert route_a.edge_id != route_b.edge_id


def test_edge_route_requires_edge_id():
    with pytest.raises(ValueError, match="edge_id"):
        ExecutionRoutingResolver().resolve(
            {"id": "r1", "management_address": "192.168.1.1"},
            requested_location=ExecutionLocation.EDGE,
        )


def test_envelope_rejects_secret_payload_and_keeps_retry_contract():
    with pytest.raises(ValidationError, match="secret-bearing"):
        EdgeEnvelope(
            protocol_version=1,
            message_id="message-1",
            task_id="task-1",
            attempt_id="attempt-1",
            idempotency_key="idempotency-1",
            edge_id="edge-1",
            sequence=1,
            nonce="n" * 16,
            issued_at=datetime.now(timezone.utc),
            valid_for_seconds=60,
            lease_duration_seconds=30,
            retry_class=RetryClass.SAFE_RETRY,
            capability="device.read.facts",
            payload={"password": "must-not-cross-boundary"},
        )
