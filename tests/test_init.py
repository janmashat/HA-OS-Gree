from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.gree_custom.const import DOMAIN

pytestmark = pytest.mark.usefixtures("mock_gree_classes")

@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, config_entry):
    """Test a successful setup entry."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data

@pytest.mark.asyncio
async def test_async_setup_entry_not_ready(hass: HomeAssistant, config_entry, mock_gree_device):
    """Test a setup entry that's not ready due to a connection error."""
    mock_gree_device.bind.side_effect = TimeoutError("Connection failed")

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY

@pytest.mark.asyncio
async def test_async_unload_entry(hass: HomeAssistant, config_entry):
    """Test a successful unload entry."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN in hass.data

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert DOMAIN not in hass.data
