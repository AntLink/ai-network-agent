"""Milestone 3: scoped routing for multi-site / overlapping subnets.

Proves that Edge ownership and customer/site scope are enforced by the
authoritative ExecutionRoutingResolver:
- same management IP behind different Edges routes to the correct Edge;
- a requested Edge that does not own the device (cross-tenant / incorrect Edge)
  is rejected;
- customer/site scope mismatches are rejected;
- routing never falls back to a global/ambiguous route.
"""
import pytest

from app.schemas.edge import ExecutionLocation
from app.services.execution_routing import ExecutionRoutingError, ExecutionRoutingResolver


def _device(device_id, mgmt, edge, customer=None, site=None):
    d = {"id": device_id, "management_address": mgmt, "edge_id": edge}
    if customer:
        d["customer_id"] = customer
    if site:
        d["site_id"] = site
    return d


def test_overlapping_subnet_disambiguates_by_owning_edge():
    """Same 192.168.1.1 behind Edge-A and Edge-B must not be ambiguous."""
    resolver = ExecutionRoutingResolver()
    device_a = _device("a-r1", "192.168.1.1", "edge-a", customer="cust-a", site="site-a")
    device_b = _device("b-r1", "192.168.1.1", "edge-b", customer="cust-b", site="site-b")

    route_a = resolver.resolve(device_a, requested_location=ExecutionLocation.EDGE, requested_edge_id="edge-a")
    route_b = resolver.resolve(device_b, requested_location=ExecutionLocation.EDGE, requested_edge_id="edge-b")

    assert route_a.edge_id == "edge-a"
    assert route_b.edge_id == "edge-b"
    assert route_a.edge_id != route_b.edge_id
    assert route_a.customer_id == "cust-a"
    assert route_b.customer_id == "cust-b"


def test_cross_tenant_wrong_edge_dispatch_rejected():
    """Requesting Edge-B for a device owned by Edge-A must be rejected."""
    resolver = ExecutionRoutingResolver()
    device_a = _device("a-r1", "192.168.1.1", "edge-a", customer="cust-a", site="site-a")
    with pytest.raises(ExecutionRoutingError, match="does not own"):
        resolver.resolve(device_a, requested_location=ExecutionLocation.EDGE, requested_edge_id="edge-b")


def test_customer_scope_mismatch_rejected():
    resolver = ExecutionRoutingResolver()
    device = _device("r1", "192.168.1.1", "edge-a", customer="cust-a", site="site-a")
    with pytest.raises(ExecutionRoutingError, match="customer"):
        resolver.resolve(
            device,
            requested_location=ExecutionLocation.EDGE,
            requested_edge_id="edge-a",
            requested_customer_id="cust-other",
        )


def test_site_scope_mismatch_rejected():
    resolver = ExecutionRoutingResolver()
    device = _device("r1", "192.168.1.1", "edge-a", customer="cust-a", site="site-a")
    with pytest.raises(ExecutionRoutingError, match="site"):
        resolver.resolve(
            device,
            requested_location=ExecutionLocation.EDGE,
            requested_edge_id="edge-a",
            requested_site_id="site-other",
        )


def test_no_forwarding_to_other_edge_when_no_owning_edge_metadata():
    """Backward compatibility: request provides edge for a device without stored owner."""
    resolver = ExecutionRoutingResolver()
    route = resolver.resolve(
        {"id": "r1", "management_address": "192.168.1.1"},
        requested_location=ExecutionLocation.EDGE,
        requested_edge_id="edge-a",
    )
    assert route.edge_id == "edge-a"


def test_defaults_to_owning_edge_when_only_metadata_present():
    resolver = ExecutionRoutingResolver()
    route = resolver.resolve(
        _device("a-r1", "192.168.1.1", "edge-a", customer="cust-a", site="site-a"),
        requested_location=ExecutionLocation.EDGE,
    )
    assert route.edge_id == "edge-a"
    assert route.location == ExecutionLocation.EDGE
