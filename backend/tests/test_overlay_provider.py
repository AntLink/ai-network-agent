import pytest

from app.services.overlay import NullOverlayProvider, ZeroTierProvider


def test_zerotier_provider_requires_private_controller_credentials():
    with pytest.raises(ValueError):
        ZeroTierProvider(controller_url="", api_token="secret")
    with pytest.raises(ValueError):
        ZeroTierProvider(controller_url="http://controller", api_token="")


@pytest.mark.asyncio
async def test_null_overlay_fails_closed():
    with pytest.raises(Exception, match="not configured"):
        await NullOverlayProvider().revoke_member(network_id="n", member_id="m")
