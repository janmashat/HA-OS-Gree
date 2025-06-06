"""Global fixtures for gree_custom integration."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys
sys.modules['homeassistant.components.gree'] = type(sys)('dummy')
sys.modules['homeassistant.components.gree.coordinator'] = type(sys)('dummy')

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gree_custom.const import DOMAIN

# This line tells pytest to load the homeassistant_custom_component fixtures
pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture is used to prevent Home Assistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is not loaded during testing.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield

# This fixture, when defined, tells pytest that your custom component requires testing against a mocked version of
# a core integration. It will disable the core integration and use your custom component's code instead.
@pytest.fixture(name="gree")
def gree_fixture():
    """Mock the gree integration."""
    with patch("custom_components.gree_custom.PLATFORMS", []):
        yield


MOCK_CONFIG = {
    CONF_NAME: "test_device_name",
    CONF_HOST: "192.168.1.100",
    CONF_MAC: "A0:B1:C2:D3:E4:F5",
    CONF_PORT: 7000,
}


@pytest.fixture
def mock_gree_device():
    """Fixture for a mocked greeclimate Device."""
    mock_device = MagicMock()
    mock_device.name = MOCK_CONFIG[CONF_NAME]
    mock_device.mac = MOCK_CONFIG[CONF_MAC].replace(":", "").lower()
    mock_device.device_key = "mock_device_key"
    mock_device.bind = AsyncMock(return_value=None)
    mock_device.update_state = AsyncMock(return_value=None)
    mock_device.push_state_update = AsyncMock(return_value=None)
    mock_device.set_property = MagicMock()

    # Mock the internal _properties dictionary that the coordinator will read
    mock_device._properties = {
        "Pow": 1, "Mod": 1, "SetTem": 24, "TemSen": 28, "WdSpd": 2,
        "SwingLfRig": 1, "SwUpDn": 1, "Quiet": 0, "Lig": 1,
    }

    # Mock the processed properties that the library would calculate
    type(mock_device).power = True
    type(mock_device).mode = 1
    type(mock_device).target_temperature = 24
    type(mock_device).current_temperature = 28
    type(mock_device).fan_speed = 2
    type(mock_device).light = True
    type(mock_device).quiet = False

    return mock_device


@pytest.fixture
def mock_gree_device_info():
    """Fixture for a mocked greeclimate DeviceInfo."""
    mock_device_info = MagicMock()
    mock_device_info.ip = MOCK_CONFIG[CONF_HOST]
    mock_device_info.port = MOCK_CONFIG[CONF_PORT]
    mock_device_info.mac = MOCK_CONFIG[CONF_MAC].replace(":", "").lower()
    mock_device_info.name = MOCK_CONFIG[CONF_NAME]
    return mock_device_info


@pytest.fixture
def mock_gree_classes(mock_gree_device, mock_gree_device_info):
    """Patch all greeclimate classes used by the integration."""
    with patch(
        "custom_components.gree_custom.coordinator.GreeClimateLibDevice",
        return_value=mock_gree_device,
    ) as mock_device_class, patch(
        "custom_components.gree_custom.coordinator.DeviceInfo", return_value=mock_gree_device_info
    ) as mock_device_info_class, patch(
        "custom_components.gree_custom.config_flow.GreeClimateLibDevice",
        return_value=mock_gree_device,
    ) as mock_cf_device_class, patch(
        "custom_components.gree_custom.config_flow.DeviceInfo",
        return_value=mock_gree_device_info,
    ) as mock_cf_device_info_class, patch(
        "custom_components.gree_custom.config_flow.Discovery"
    ) as mock_cf_discovery_class:
        
        mock_discovery_instance = mock_cf_discovery_class.return_value
        mock_discovery_instance.scan = AsyncMock(return_value=None)
        type(mock_discovery_instance).devices = [mock_gree_device_info]
        
        yield

@pytest.fixture
async def config_entry(hass: HomeAssistant) -> ConfigEntry:
    """Create a mock config entry and add it to hass."""
    # Use the MockConfigEntry helper from pytest-homeassistant-custom-component
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_CONFIG[CONF_NAME],
        data=MOCK_CONFIG,
        unique_id=MOCK_CONFIG[CONF_MAC],
    )
    entry.add_to_hass(hass)
    return entry
