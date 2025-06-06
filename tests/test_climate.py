import pytest
from homeassistant.components.climate import (
    ATTR_FAN_MODE, ATTR_HVAC_MODE, ATTR_SWING_MODE, ATTR_SWING_HORIZONTAL_MODE,
    SERVICE_SET_FAN_MODE, SERVICE_SET_HVAC_MODE, SERVICE_SET_SWING_MODE,
    SERVICE_SET_SWING_HORIZONTAL_MODE, SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from syrupy.assertion import SnapshotAssertion

from custom_components.gree_custom.const import (
    DOMAIN, HA_HVACMODE_TO_GREE_MODE_INT, HA_FANMODE_STR_TO_GREE_FANSPEED_INT,
    HA_TO_GREE_VERTICAL_SWING_MAP, HA_H_SWING_TO_GREE_MAP,
    VS_FULL, FAN_HIGH, HVACMode,
)


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

ENTITY_ID = f"climate.{DOMAIN}_test_device_name"


@pytest.mark.asyncio
async def test_climate_entity_properties(hass, config_entry, snapshot: SnapshotAssertion):
    """Test the climate entity properties."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == HVACMode.COOL.value

    assert state.attributes == snapshot

@pytest.mark.asyncio
async def test_set_hvac_mode(hass, config_entry, mock_gree_device):
    """Test setting the HVAC mode."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "climate", SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    assert mock_gree_device.mode == HA_HVACMODE_TO_GREE_MODE_INT[HVACMode.HEAT]
    mock_gree_device.push_state_update.assert_called()

@pytest.mark.asyncio
async def test_set_temperature(hass, config_entry, mock_gree_device):
    """Test setting the target temperature."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "climate", SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 22.0},
        blocking=True,
    )
    assert mock_gree_device.target_temperature == 22
    mock_gree_device.push_state_update.assert_called()

@pytest.mark.asyncio
async def test_set_fan_mode(hass, config_entry, mock_gree_device):
    """Test setting the fan mode."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "climate", SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_FAN_MODE: FAN_HIGH},
        blocking=True,
    )
    assert mock_gree_device.fan_speed == HA_FANMODE_STR_TO_GREE_FANSPEED_INT[FAN_HIGH]
    mock_gree_device.push_state_update.assert_called()

@pytest.mark.asyncio
async def test_set_vertical_swing_mode(hass, config_entry, mock_gree_device):
    """Test setting the vertical swing mode."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "climate", SERVICE_SET_SWING_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_SWING_MODE: VS_FULL},
        blocking=True,
    )
    from greeclimate.device import Props
    gree_value = HA_TO_GREE_VERTICAL_SWING_MAP[VS_FULL]
    mock_gree_device.set_property.assert_called_with(Props.SWING_VERT, gree_value)
    mock_gree_device.push_state_update.assert_called()

@pytest.mark.asyncio
async def test_set_horizontal_swing_mode(hass, config_entry, mock_gree_device):
    """Test setting the horizontal swing mode."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    target_h_swing = "Full Swing"
    await hass.services.async_call(
        "climate", SERVICE_SET_SWING_HORIZONTAL_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_SWING_HORIZONTAL_MODE: target_h_swing},
        blocking=True,
    )
    from greeclimate.device import Props
    gree_value = HA_H_SWING_TO_GREE_MAP[target_h_swing]
    mock_gree_device.set_property.assert_called_with(Props.SWING_HORIZ, gree_value)
    mock_gree_device.push_state_update.assert_called()
