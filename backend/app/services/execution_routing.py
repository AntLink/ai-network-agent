"""Single authoritative executor selection for device operations.

Milestone 3 adds scoped ownership enforcement: a device declares the Edge (and
optionally customer/site) that owns it. Routing to a requested Edge is only
permitted when that Edge matches the device's owning Edge. This rejects
cross-tenant / incorrect-Edge dispatch and disambiguates overlapping subnets
(same management IP behind different Edges) by customer/site/Edge identity
rather than by IP alone.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.edge import ExecutionLocation


@dataclass(frozen=True)
class ExecutionRoute:
    location: ExecutionLocation
    edge_id: str | None
    reason: str
    customer_id: str | None = None
    site_id: str | None = None
    device_id: str | None = None


class ExecutionRoutingError(ValueError):
    """Raised when a route is not permitted (e.g. cross-tenant / wrong Edge)."""


class ExecutionRoutingResolver:
    def _scope_point(self, device: dict) -> str:
        """Return an edge/customer/site scoping point for consistent messages."""
        device_id = str(device.get("id", "?"))
        owning_edge = device.get("edge_id")
        customer = device.get("customer_id", device.get("customer", "-"))
        site = device.get("site_id", device.get("site", "-"))
        return (
            f"device={device_id} customer={customer} site={site} edge={owning_edge or '<unset>'}"
        )

    def resolve(self, device: dict, *, requested_location: ExecutionLocation | None = None,
                requested_edge_id: str | None = None,
                requested_customer_id: str | None = None,
                requested_site_id: str | None = None) -> ExecutionRoute:
        metadata_location = device.get("execution_location")
        location = requested_location or (
            ExecutionLocation(str(metadata_location).upper())
            if metadata_location else None
        )

        owning_edge_id = device.get("edge_id")
        owning_customer = device.get("customer_id", device.get("customer"))
        owning_site = device.get("site_id", device.get("site"))

        # EDGE selected via explicit request or device metadata.
        edge_selected = (location == ExecutionLocation.EDGE) or requested_edge_id or owning_edge_id
        if edge_selected:
            if not (requested_edge_id or owning_edge_id):
                raise ExecutionRoutingError("EDGE execution requires edge_id")

            edge_id = str(requested_edge_id or owning_edge_id)

            # Ownership enforcement: a requested Edge must match the device's
            # owning Edge. Rejecting a mismatched Edge prevents cross-tenant and
            # incorrect-Edge dispatch, and disambiguates overlapping subnets.
            if requested_edge_id is not None and owning_edge_id is not None:
                if str(requested_edge_id) != str(owning_edge_id):
                    raise ExecutionRoutingError(
                        f"requested Edge {requested_edge_id!r} does not own {self._scope_point(device)}"
                    )

            # Optional customer/site scope enforcement on the request.
            if requested_customer_id is not None and owning_customer is not None:
                if str(requested_customer_id) != str(owning_customer):
                    raise ExecutionRoutingError(
                        f"requested customer {requested_customer_id!r} does not match {self._scope_point(device)}"
                    )
            if requested_site_id is not None and owning_site is not None:
                if str(requested_site_id) != str(owning_site):
                    raise ExecutionRoutingError(
                        f"requested site {requested_site_id!r} does not match {self._scope_point(device)}"
                    )

            return ExecutionRoute(
                ExecutionLocation.EDGE,
                edge_id,
                "device/request edge context (M3 scoped)",
                customer_id=owning_customer,
                site_id=owning_site,
                device_id=str(device.get("id")),
            )

        if location == ExecutionLocation.LAB or device.get("lab") or device.get("device_type") == "virtual":
            return ExecutionRoute(ExecutionLocation.LAB, None, "existing lab/virtual device")
        return ExecutionRoute(ExecutionLocation.CENTRAL, None, "default central execution")


execution_routing_resolver = ExecutionRoutingResolver()
