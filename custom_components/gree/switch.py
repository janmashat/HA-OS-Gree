"""Switch entities for Gree Climate integration."""
import logging
from typing import Any, Optional

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, SWITCH_TYPE_LIGHT, SWITCH_TYPE_QUIET,
    GREE_PROPERTY_LIGHT, GREE_PROPERTY_QUIET, GREE_POWER_ON
)
from .coordinator import GreeClimateUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key=SWITCH_TYPE_LIGHT, name="Panel Light", icon="mdi:lightbulb",
        translation_key=SWITCH_TYPE_LIGHT,
    ),
    SwitchEntityDescription(
        key=SWITCH_TYPE_QUIET, name="Quiet Mode", icon="mdi:volume-mute",
        translation_key=SWITCH_TYPE_QUIET,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gree switch entities from a config entry."""
    coordinator: GreeClimateUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [GreeSwitch(coordinator, description) for description in SWITCH_DESCRIPTIONS]
    async_add_entities(entities)

class GreeSwitch(CoordinatorEntity[GreeClimateUpdateCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GreeClimateUpdateCoordinator, description: SwitchEntityDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_mac_display}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_mac_display)},
            "name": coordinator.device_name,
            "manufacturer": "Gree",
        }

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.device is not None

    @property
    def is_on(self) -> Optional[bool]:
        if not self.coordinator.data: return None # No data from coordinator yet
        if self.entity_description.key == SWITCH_TYPE_LIGHT:
            return self.coordinator.data.get(GREE_PROPERTY_LIGHT) == GREE_POWER_ON
        if self.entity_description.key == SWITCH_TYPE_QUIET:
            return self.coordinator.data.get(GREE_PROPERTY_QUIET) == GREE_POWER_ON
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self.entity_description.key == SWITCH_TYPE_LIGHT:
            await self.coordinator.async_set_light(True)
        elif self.entity_description.key == SWITCH_TYPE_QUIET:
            await self.coordinator.async_set_quiet_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.entity_description.key == SWITCH_TYPE_LIGHT:
            await self.coordinator.async_set_light(False)
        elif self.entity_description.key == SWITCH_TYPE_QUIET:
            await self.coordinator.async_set_quiet_mode(False)
