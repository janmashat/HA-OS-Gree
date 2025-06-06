import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.gree_custom.const import DOMAIN
from .conftest import MOCK_CONFIG

pytestmark = pytest.mark.usefixtures("mock_gree_classes")

@pytest.mark.asyncio
async def test_flow_ip_and_discover_mac(hass: HomeAssistant) -> None:
    """Test the full discovery flow starting with IP."""
    mock_finder_instance = AsyncMock()
    # In this test, we don't need mock_gree_classes fixture because we patch the classes directly
    with patch(
        "custom_components.gree_custom.config_flow.MacFinder", return_value=mock_finder_instance
    ), patch(
        "custom_components.gree_custom.config_flow.GreeClimateLibDevice"
    ) as mock_device, patch(
        "custom_components.gree_custom.config_flow.DeviceInfo"
    ) as mock_device_info:

        mock_device_info_instance = mock_device_info.return_value
        mock_finder_instance.found_device_info = mock_device_info_instance
        mock_finder_instance.found_event.wait = AsyncMock(return_value=True)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: MOCK_CONFIG[CONF_HOST]}
        )
        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "link"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], {CONF_NAME: "Final Device Name"}
        )
        await hass.async_block_till_done()

        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result3["title"] == "Final Device Name"


@pytest.mark.asyncio
async def test_flow_manual_entry(hass: HomeAssistant) -> None:
    """Test the full manual entry flow after discovery fails."""
    with patch(
        "custom_components.gree_custom.config_flow.asyncio.wait_for",
        side_effect=asyncio.TimeoutError
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.100"}
        )
        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "manual"

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], MOCK_CONFIG
    )
    await hass.async_block_till_done()

    assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result3["title"] == MOCK_CONFIG[CONF_NAME]
    assert result3["data"] == MOCK_CONFIG
