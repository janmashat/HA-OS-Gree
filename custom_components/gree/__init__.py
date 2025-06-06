"""The Gree Climate integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform, CONF_HOST, CONF_PORT

from .const import DOMAIN
from .coordinator import GreeClimateUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Correctly define the platforms that have corresponding Python files
PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    # Platform.SELECT, # REMOVED: This was causing the error as select.py was deleted
    Platform.SWITCH,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree Climate from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info(
        "Setting up Gree device %s (%s:%s) via %s domain",
        entry.title, entry.data[CONF_HOST], entry.data[CONF_PORT], DOMAIN,
    )

    coordinator = GreeClimateUpdateCoordinator(hass, entry)

    # Perform the first refresh to populate data and check connectivity.
    await coordinator.async_config_entry_first_refresh()

    # Check if the coordinator's device object was initialized and if the first update succeeded
    if coordinator.device is None: # Check if greeclimate library failed to load in coordinator
        _LOGGER.error("Greeclimate library failed to load for %s. Setup aborted.", coordinator.device_name if hasattr(coordinator, 'device_name') else entry.title)
        return False
    if not coordinator.last_update_success:
        _LOGGER.error("Initial update failed for %s. Setup aborted.", coordinator.device_name)
        return False

    hass.data[DOMAIN][entry.entry_id] = coordinator # Store only coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(options_update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Gree device %s", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.info("Configuration options updated for %s, reloading entry.", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)
