import pytest
from homeassistant.const import SERVICE_TURN_ON, SERVICE_TURN_OFF, ATTR_ENTITY_ID
from syrupy.assertion import SnapshotAssertion

from custom_components.gree_custom.const import DOMAIN, SWITCH_TYPE_LIGHT, SWITCH_TYPE_QUIET


from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.setup import async_setup_component
from homeassistant.const import CONF_HOST, CONF_PORT

mock_entry = MockConfigEntry(
    domain="gree_custom",
    data={CONF_HOST: "192.168.1.100", CONF_PORT: 7000, "mac": "AA:BB:CC:DD:EE:FF"},
)
mock_entry.add_to_hass(hass)

# Patch the coordinator and its refresh method
with patch("custom_components.gree_custom.GreeClimateUpdateCoordinator.async_config_entry_first_refresh", return_value=True), \
     patch("custom_components.gree_custom.GreeClimateUpdateCoordinator.device", new=MagicMock()), \
     patch("custom_components.gree_custom.GreeClimateUpdateCoordinator.last_update_success", True):

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()


pytestmark = pytest.mark.usefixtures("mock_gree_classes")

ENTITY_ID_LIGHT = f"switch.{DOMAIN}_test_device_name_{SWITCH_TYPE_LIGHT}"
ENTITY_ID_QUIET = f"switch.{DOMAIN}_test_device_name_{SWITCH_TYPE_QUIET}"

@pytest.mark.asyncio
async def test_switch_entity_properties(hass, config_entry, snapshot: SnapshotAssertion):
    """Test the switch entity properties."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state_light = hass.states.get(ENTITY_ID_LIGHT)
    assert state_light
    assert state_light.state == "on"
    assert state_light.attributes == snapshot(name="light-switch-attributes")

    state_quiet = hass.states.get(ENTITY_ID_QUIET)
    assert state_quiet
    assert state_quiet.state == "off"
    assert state_quiet.attributes == snapshot(name="quiet-switch-attributes")

@pytest.mark.asyncio
async def test_turn_on_light_switch(hass, config_entry, mock_gree_device):
    """Test turning on the light switch."""
    mock_gree_device._properties["Lig"] = 0 
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID_LIGHT}, blocking=True
    )
    assert mock_gree_device.light is True 
    mock_gree_device.push_state_update.assert_called()

@pytest.mark.asyncio
async def test_turn_off_quiet_switch(hass, config_entry, mock_gree_device):
    """Test turning off the quiet mode switch."""
    mock_gree_device._properties["Quiet"] = 1
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "switch", SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_ID_QUIET}, blocking=True
    )
    assert mock_gree_device.quiet is False
    mock_gree_device.push_state_update.assert_called()
