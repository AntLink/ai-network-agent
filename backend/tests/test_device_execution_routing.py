from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.endpoints import devices


@pytest.mark.asyncio
async def test_edge_facts_use_existing_capability_dispatch():
    device = {
        "id": "edge-router-1",
        "management_address": "192.168.1.1",
        "vendor": "cisco",
        "execution_location": "EDGE",
        "edge_id": "edge-001",
        "customer_id": "cust-a",
        "site_id": "site-a",
        "credential_ref": "cred-edge-1",
    }
    dispatched = {"execution_location": "EDGE", "edge_id": "edge-001"}

    with patch.object(devices.inventory_repository, "get_device", return_value=device), patch(
        "app.api.v1.endpoints.tasks.execute_capability",
        new=AsyncMock(return_value=dispatched),
    ) as dispatch:
        result = await devices.get_facts("edge-router-1", credential_ref=None)

    assert result == dispatched
    dispatch.assert_awaited_once()
    request = dispatch.await_args.args[0]
    assert request.device_id == "edge-router-1"
    assert request.capability == "device.read.facts"
    assert request.execution_location.value == "EDGE"
    assert request.edge_id == "edge-001"
    assert request.model_dump()["credential_ref"] == "cred-edge-1"


@pytest.mark.asyncio
async def test_direct_facts_stay_on_central_device_service():
    device = {
        "id": "direct-router-1",
        "management_address": "198.51.100.10",
        "vendor": "cisco",
        "execution_location": "CENTRAL",
    }
    central_facts = {"hostname": "direct-router-1", "vendor": "cisco"}

    with patch.object(devices.inventory_repository, "get_device", return_value=device), patch.object(
        devices.device_service, "facts", new=AsyncMock(return_value=central_facts)
    ) as facts, patch("app.api.v1.endpoints.tasks.execute_capability", new=AsyncMock()) as dispatch:
        result = await devices.get_facts("direct-router-1")

    assert result == central_facts
    facts.assert_awaited_once_with("direct-router-1")
    dispatch.assert_not_awaited()